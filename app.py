import datetime as dt
import io
import base64

import requests
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State, callback, no_update, ctx
import plotly.graph_objects as go
import plotly.io as pio

from fpdf import FPDF

from project import fetch_daily_temp, compute_daily_gdd, determine_growing_stage, CropSeason
from crops_data import crops


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def geocode_location(place_name):
    """Search for a place name using Open-Meteo Geocoding API.

    The API works best with a single place name rather than comma-separated
    queries, so we try the full string first, then fall back to the first
    comma-delimited part.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"

    # Try the full query first, then just the first part before a comma
    queries = [place_name]
    if "," in place_name:
        queries.append(place_name.split(",")[0].strip())

    results = []
    for query in queries:
        params = {
            "name": query,
            "count": 1,
            "language": "en",
            "format": "json",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if results:
            break

    if not results:
        return None

    top = results[0]
    name_parts = [top.get("name", "")]
    if top.get("admin1"):
        name_parts.append(top["admin1"])
    if top.get("country"):
        name_parts.append(top["country"])

    return {
        "name": ", ".join(name_parts),
        "latitude": top["latitude"],
        "longitude": top["longitude"],
    }


def fetch_climate_temp(latitude, longitude, start_date, end_date):
    """Fetch projected daily temperatures from the Open-Meteo Climate API."""
    url = "https://climate-api.open-meteo.com/v1/climate"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_min,temperature_2m_max",
        "models": "EC_Earth3P_HR",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmins = daily.get("temperature_2m_min", [])
    tmaxs = daily.get("temperature_2m_max", [])

    if not dates:
        return pd.DataFrame(columns=["date", "tmin", "tmax"])

    df = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "tmin": [float(t) if t is not None else 0.0 for t in tmins],
        "tmax": [float(t) if t is not None else 0.0 for t in tmaxs],
    })

    return df


def build_map_figure(lat=None, lon=None, location_name=""):
    """Build a Plotly map figure centered on the given coordinates."""
    center_lat = lat if lat is not None else 20.0
    center_lon = lon if lon is not None else 0.0
    zoom = 10 if lat is not None else 1

    fig = go.Figure()

    if lat is not None and lon is not None:
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode="markers",
            marker=dict(size=14, color="red"),
            text=[location_name or f"{lat:.4f}, {lon:.4f}"],
            hoverinfo="text",
            name="Selected Location",
        ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        showlegend=False,
    )
    return fig


def build_progress_chart(season):
    """Build a Plotly chart for Mode A: actual GDD vs ideal GDD."""
    fig = go.Figure()

    actual_cumulative = season.weather["cumulative_gdd"]
    window_days = len(actual_cumulative)
    x_days = list(range(1, window_days + 1))
    t_base = season.params["t_base"]
    t_upper = season.params["t_upper"]

    upper_daily = t_upper - t_base
    ideal_gdd = [upper_daily * i for i in x_days]

    fig.add_trace(go.Scatter(
        x=x_days, y=ideal_gdd,
        mode="lines", name="Ideal GDD",
        line=dict(dash="dash", width=1.5, color="gray"),
    ))

    fig.add_trace(go.Scatter(
        x=x_days, y=actual_cumulative.tolist(),
        mode="lines", name="Actual GDD",
        line=dict(width=2, color="#1f77b4"),
    ))

    fig.add_trace(go.Scatter(
        x=[x_days[-1]], y=[actual_cumulative.iloc[-1]],
        mode="markers", name="Current",
        marker=dict(size=10, color="#1f77b4"),
        showlegend=False,
    ))

    stages = season.params["stages"]
    colors = {
        "initial": "#2ca02c",
        "development": "#ff7f0e",
        "mid_season": "#d62728",
        "harvest": "#9467bd",
    }
    for stage_name, gdd_threshold in stages.items():
        fig.add_hline(
            y=gdd_threshold,
            line_dash="dot",
            line_color=colors.get(stage_name, "gray"),
            annotation_text=stage_name.replace("_", " ").title(),
            annotation_position="top left",
        )

    crop_label = season.crop_id.replace("_", " ").title()
    fig.update_layout(
        title=f"Cumulative GDD Progress \u2013 {crop_label} ({season.location})",
        xaxis_title="Days since planting",
        yaxis_title="Cumulative GDD",
        template="plotly_white",
        height=400,
    )
    return fig


def build_planning_chart(weather_df, crop_params, crop_id, location_name, planting_date):
    """Build a Plotly chart for Mode B: projected GDD with stage thresholds."""
    fig = go.Figure()

    t_base = crop_params["t_base"]
    t_upper = crop_params["t_upper"]
    stages = crop_params["stages"]

    weather_df = weather_df.copy()
    weather_df["daily_gdd"] = weather_df.apply(
        lambda row: compute_daily_gdd(row["tmin"], row["tmax"], t_base, t_upper),
        axis=1,
    )
    weather_df["cumulative_gdd"] = weather_df["daily_gdd"].cumsum()

    x_days = list(range(1, len(weather_df) + 1))
    projected_gdd = weather_df["cumulative_gdd"].tolist()

    upper_daily = t_upper - t_base
    ideal_gdd = [upper_daily * i for i in x_days]

    fig.add_trace(go.Scatter(
        x=x_days, y=ideal_gdd,
        mode="lines", name="Ideal GDD",
        line=dict(dash="dash", width=1.5, color="gray"),
    ))

    fig.add_trace(go.Scatter(
        x=x_days, y=projected_gdd,
        mode="lines", name="Projected GDD (Climate Model)",
        line=dict(width=2, color="#ff7f0e"),
    ))

    colors = {
        "initial": "#2ca02c",
        "development": "#ff7f0e",
        "mid_season": "#d62728",
        "harvest": "#9467bd",
    }
    stage_dates = {}
    for stage_name, gdd_threshold in stages.items():
        reached = weather_df[weather_df["cumulative_gdd"] >= gdd_threshold]
        if not reached.empty:
            day_idx = reached.index[0]
            est_date = weather_df.loc[day_idx, "date"]
            if hasattr(est_date, "date"):
                est_date = est_date.date()
            stage_dates[stage_name] = est_date
            annotation = f"{stage_name.replace('_', ' ').title()} ({est_date})"
        else:
            annotation = f"{stage_name.replace('_', ' ').title()} (> {len(x_days)}d)"

        fig.add_hline(
            y=gdd_threshold,
            line_dash="dot",
            line_color=colors.get(stage_name, "gray"),
            annotation_text=annotation,
            annotation_position="top left",
        )

    crop_label = crop_id.replace("_", " ").title()
    fig.update_layout(
        title=f"Projected GDD \u2013 {crop_label} ({location_name})",
        xaxis_title="Days since planting",
        yaxis_title="Cumulative GDD",
        template="plotly_white",
        height=400,
    )

    return fig, stage_dates


def build_temperature_chart(weather_df, location_name, planting_date):
    """Build a Plotly chart showing daily Tmin and Tmax over time."""
    fig = go.Figure()

    dates = weather_df["date"]

    fig.add_trace(go.Scatter(
        x=dates, y=weather_df["tmax"],
        mode="lines", name="Tmax",
        line=dict(width=1.5, color="#d62728"),
    ))

    fig.add_trace(go.Scatter(
        x=dates, y=weather_df["tmin"],
        mode="lines", name="Tmin",
        line=dict(width=1.5, color="#1f77b4"),
        fill="tonexty",
        fillcolor="rgba(31,119,180,0.15)",
    ))

    fig.update_layout(
        title=f"Daily Temperature \u2013 {location_name}",
        xaxis_title="Date",
        yaxis_title="Temperature (\u00b0C)",
        template="plotly_white",
        height=300,
    )
    return fig


def build_stage_table(crop_params, crop_label):
    """Build an HTML table showing cumulative GDD thresholds per growth stage."""
    stages = crop_params["stages"]
    header = html.Tr([
        html.Th("Growth Stage", style={"padding": "6px 12px", "textAlign": "left"}),
        html.Th("Cumulative GDD", style={"padding": "6px 12px", "textAlign": "right"}),
    ])
    rows = []
    for stage_name in ["initial", "development", "mid_season", "harvest"]:
        gdd = stages.get(stage_name, "N/A")
        rows.append(html.Tr([
            html.Td(stage_name.replace("_", " ").title(), style={"padding": "4px 12px"}),
            html.Td(f"{gdd}", style={"padding": "4px 12px", "textAlign": "right"}),
        ]))

    return html.Div([
        html.H4(f"GDD Thresholds \u2013 {crop_label}", style={"marginBottom": "6px"}),
        html.Table(
            [html.Thead(header), html.Tbody(rows)],
            style={
                "borderCollapse": "collapse",
                "width": "100%",
                "border": "1px solid #dee2e6",
                "marginBottom": "16px",
                "fontSize": "14px",
            },
        ),
    ])


def generate_pdf_report(report_data, chart_fig):
    """Generate a 1-page PDF report and return it as bytes."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "GDD Crop Phenology Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {dt.date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # Location
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Location", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Name: {report_data.get('location', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Coordinates: {report_data.get('latitude', '')}, {report_data.get('longitude', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Crop
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Crop Information", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Crop: {report_data.get('crop_label', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Tbase: {report_data.get('t_base', '')} C  |  Tupper: {report_data.get('t_upper', '')} C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Planting Date: {report_data.get('planting_date', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Results
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Results", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    mode = report_data.get("mode", "check")
    if mode == "check":
        pdf.cell(0, 6, f"Date: {report_data.get('date', '')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Cumulative GDD: {report_data.get('cumulative_gdd', 0):.2f}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Current Stage: {report_data.get('stage', '')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Stage Progress: {report_data.get('stage_progress', 0):.1f}%", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Overall Progress: {report_data.get('overall_progress', 0):.1f}%", new_x="LMARGIN", new_y="NEXT")
    else:
        stage_dates = report_data.get("stage_dates", {})
        for stage_name, est_date in stage_dates.items():
            label = stage_name.replace("_", " ").title()
            pdf.cell(0, 6, f"{label}: {est_date}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # Chart image
    try:
        img_bytes = pio.to_image(chart_fig, format="png", width=700, height=350)
        img_stream = io.BytesIO(img_bytes)
        pdf.image(img_stream, x=10, w=190)
    except Exception:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "(Chart image could not be generated)", new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Data source: Open-Meteo (open-meteo.com) | Based on FAO56rev GDD framework", align="C")

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Dash app
# ---------------------------------------------------------------------------

app = Dash(__name__)

# Build crop name -> variants mapping from crops_data keys
# Each key follows the pattern: {crop_name}_{variant}
crop_variants = {}
for cid in sorted(crops.keys()):
    parts = cid.rsplit("_", 1)
    crop_name = parts[0]
    variant = parts[1] if len(parts) == 2 else "default"
    crop_variants.setdefault(crop_name, []).append(variant)

crop_name_options = [
    {"label": name.replace("_", " ").title(), "value": name}
    for name in sorted(crop_variants.keys())
]

app.layout = html.Div(
    style={"display": "flex", "fontFamily": "Arial, sans-serif", "minHeight": "100vh"},
    children=[
        # --- Left panel: Inputs ---
        html.Div(
            style={
                "width": "380px",
                "padding": "20px",
                "backgroundColor": "#f8f9fa",
                "borderRight": "1px solid #dee2e6",
                "overflowY": "auto",
            },
            children=[
                html.H2("GDD Crop Phenology Tracker", style={"marginTop": 0}),
                html.Hr(),

                # Map
                dcc.Graph(id="map-graph", figure=build_map_figure(),
                          config={"scrollZoom": True},
                          style={"marginBottom": "12px"}),

                # Location search
                html.Label("Search Location", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="input-search",
                    type="text",
                    placeholder="e.g. La Trinidad, Benguet",
                    style={"width": "100%", "marginBottom": "6px"},
                ),
                html.Button(
                    "Search",
                    id="btn-search",
                    n_clicks=0,
                    style={"width": "100%", "marginBottom": "12px"},
                ),

                # Lat / Lon
                html.Div(style={"display": "flex", "gap": "10px", "marginBottom": "12px"}, children=[
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Latitude"),
                        dcc.Input(id="input-lat", type="number", style={"width": "100%"}),
                    ]),
                    html.Div(style={"flex": 1}, children=[
                        html.Label("Longitude"),
                        dcc.Input(id="input-lon", type="number", style={"width": "100%"}),
                    ]),
                ]),

                html.Div(id="location-name", style={"marginBottom": "12px", "fontStyle": "italic"}),

                html.Hr(),

                # Crop name
                html.Label("Crop", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="dropdown-crop-name",
                    options=crop_name_options,
                    placeholder="Select a crop...",
                    style={"marginBottom": "8px"},
                ),

                # Season / variant
                html.Label("Season", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="dropdown-variant",
                    placeholder="Select season...",
                    style={"marginBottom": "12px"},
                ),

                # Mode
                html.Label("Mode", style={"fontWeight": "bold"}),
                dcc.RadioItems(
                    id="radio-mode",
                    options=[
                        {"label": " Check Progress (past planting)", "value": "check"},
                        {"label": " Plan Harvest (future planting)", "value": "plan"},
                    ],
                    value="check",
                    style={"marginBottom": "12px"},
                ),

                # Planting date
                html.Label("Planting Date", style={"fontWeight": "bold"}),
                dcc.DatePickerSingle(
                    id="datepicker-planting",
                    placeholder="Select date...",
                    style={"marginBottom": "12px"},
                ),

                # Compute button
                html.Button(
                    "Compute GDD",
                    id="btn-compute",
                    n_clicks=0,
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "backgroundColor": "#28a745",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "4px",
                        "fontWeight": "bold",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "marginBottom": "16px",
                    },
                ),

                # Documentation link
                html.A(
                    "Documentation",
                    href="https://open-meteo.com/en/docs",
                    target="_blank",
                    style={
                        "display": "block",
                        "textAlign": "center",
                        "color": "#007bff",
                        "fontSize": "13px",
                    },
                ),

                # Hidden stores
                dcc.Store(id="store-location", data={}),
                dcc.Store(id="store-report", data={}),
                dcc.Store(id="store-chart", data={}),
            ],
        ),

        # --- Right panel: Outputs ---
        html.Div(
            style={"flex": "1", "padding": "20px", "overflowY": "auto"},
            children=[
                # GDD stage thresholds table
                html.Div(id="stage-table"),

                # Results
                dcc.Loading(
                    id="loading-results",
                    type="default",
                    children=html.Div(id="results-panel"),
                ),

                html.Div(style={"height": "20px"}),

                # GDD Chart
                dcc.Loading(
                    id="loading-chart",
                    type="default",
                    children=dcc.Graph(id="gdd-chart", figure=go.Figure()),
                ),

                # Temperature Chart
                dcc.Loading(
                    id="loading-temp-chart",
                    type="default",
                    children=dcc.Graph(id="temp-chart", figure=go.Figure()),
                ),

                html.Div(style={"height": "12px"}),

                # Download PDF
                html.Button(
                    "Download PDF Report",
                    id="btn-download",
                    n_clicks=0,
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "backgroundColor": "#007bff",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "4px",
                        "fontWeight": "bold",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "marginTop": "12px",
                        "display": "none",
                    },
                ),
                dcc.Download(id="download-pdf"),
            ],
        ),
    ],
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

# Callback 1: Geocode search -> update lat, lon, location name
@callback(
    Output("input-lat", "value"),
    Output("input-lon", "value"),
    Output("store-location", "data"),
    Output("location-name", "children"),
    Input("btn-search", "n_clicks"),
    State("input-search", "value"),
    prevent_initial_call=True,
)
def geocode_search(n_clicks, search_text):
    if not search_text or not search_text.strip():
        return no_update, no_update, no_update, "Please enter a location name."

    try:
        result = geocode_location(search_text.strip())
    except Exception:
        return no_update, no_update, no_update, "Geocoding failed. Check your connection."

    if result is None:
        return no_update, no_update, no_update, "Location not found. Try a different term."

    return (
        round(result["latitude"], 4),
        round(result["longitude"], 4),
        result,
        result["name"],
    )


# Callback 2: Update map when lat/lon change
@callback(
    Output("map-graph", "figure"),
    Input("input-lat", "value"),
    Input("input-lon", "value"),
    State("store-location", "data"),
)
def update_map(lat, lon, loc_data):
    if lat is None or lon is None:
        return build_map_figure()

    name = loc_data.get("name", "") if loc_data else ""
    return build_map_figure(lat, lon, name)


# Callback 3: Mode toggle -> adjust date picker max/min
@callback(
    Output("datepicker-planting", "max_date_allowed"),
    Output("datepicker-planting", "min_date_allowed"),
    Output("datepicker-planting", "date"),
    Input("radio-mode", "value"),
)
def toggle_mode(mode):
    today = dt.date.today()
    if mode == "check":
        return today.isoformat(), None, None
    else:
        return "2050-12-31", today.isoformat(), None


# Callback 3b: Update variant dropdown when crop name changes
@callback(
    Output("dropdown-variant", "options"),
    Output("dropdown-variant", "value"),
    Input("dropdown-crop-name", "value"),
)
def update_variant_options(crop_name):
    if not crop_name:
        return [], None

    variants = crop_variants.get(crop_name, [])
    options = [
        {"label": v.title(), "value": v}
        for v in variants
    ]
    # Auto-select if only one variant
    default = variants[0] if len(variants) == 1 else None
    return options, default


# Callback 4: Compute GDD
@callback(
    Output("stage-table", "children"),
    Output("results-panel", "children"),
    Output("gdd-chart", "figure"),
    Output("temp-chart", "figure"),
    Output("btn-download", "style"),
    Output("store-report", "data"),
    Output("store-chart", "data"),
    Input("btn-compute", "n_clicks"),
    State("input-lat", "value"),
    State("input-lon", "value"),
    State("dropdown-crop-name", "value"),
    State("dropdown-variant", "value"),
    State("datepicker-planting", "date"),
    State("radio-mode", "value"),
    State("store-location", "data"),
    prevent_initial_call=True,
)
def compute_gdd(n_clicks, lat, lon, crop_name, variant, planting_date_str, mode, loc_data):
    if lat is None or lon is None:
        return None, "Please enter or search for a location.", go.Figure(), go.Figure(), {"display": "none"}, {}, {}
    if not crop_name or not variant:
        return None, "Please select a crop and season.", go.Figure(), go.Figure(), {"display": "none"}, {}, {}

    crop_id = f"{crop_name}_{variant}"
    if not planting_date_str:
        return None, "Please select a planting date.", go.Figure(), go.Figure(), {"display": "none"}, {}, {}

    try:
        planting_date = dt.date.fromisoformat(planting_date_str)
    except ValueError:
        return None, "Invalid planting date.", go.Figure(), go.Figure(), {"display": "none"}, {}, {}

    location_name = loc_data.get("name", f"{lat}, {lon}") if loc_data else f"{lat}, {lon}"
    crop_params = crops[crop_id]
    crop_label = crop_id.replace("_", " ").title()

    download_btn_style = {
        "width": "100%",
        "padding": "10px",
        "backgroundColor": "#007bff",
        "color": "white",
        "border": "none",
        "borderRadius": "4px",
        "fontWeight": "bold",
        "fontSize": "14px",
        "cursor": "pointer",
        "marginTop": "12px",
        "display": "block",
    }

    today = dt.date.today()

    stage_table = build_stage_table(crop_params, crop_label)

    # ---- Mode A: Check Progress ----
    if mode == "check":
        if planting_date > today:
            return (
                stage_table, "Check mode requires a past planting date.",
                go.Figure(), go.Figure(), {"display": "none"}, {}, {},
            )

        try:
            weather = fetch_daily_temp(lat, lon, planting_date.isoformat(), today.isoformat())
        except Exception as e:
            return stage_table, f"Could not fetch weather data: {e}", go.Figure(), go.Figure(), {"display": "none"}, {}, {}

        if weather.empty:
            return stage_table, "No weather data available for this location and date range.", go.Figure(), go.Figure(), {"display": "none"}, {}, {}

        season = CropSeason(crop_id, planting_date, weather, location_name)
        season.compute_gdd_series()
        summary = season.summary_today()

        results = html.Div([
            html.H4("Results", style={"marginBottom": "8px"}),
            html.P(f"Date: {summary['date']}"),
            html.P(f"Crop: {crop_label}"),
            html.P(f"Cumulative GDD: {summary['cumulative_gdd']:.2f}"),
            html.P(f"Stage: {summary['stage'].replace('_', ' ').title()}"),
            html.P(f"Stage Progress: {summary['stage_progress'] * 100:.1f}%"),
            html.P(f"Overall Progress: {summary['overall_progress'] * 100:.1f}%"),
        ])

        chart_fig = build_progress_chart(season)
        temp_fig = build_temperature_chart(weather, location_name, planting_date)

        report_data = {
            "mode": "check",
            "location": location_name,
            "latitude": lat,
            "longitude": lon,
            "crop_label": crop_label,
            "t_base": crop_params["t_base"],
            "t_upper": crop_params["t_upper"],
            "planting_date": planting_date.isoformat(),
            "date": summary["date"],
            "cumulative_gdd": summary["cumulative_gdd"],
            "stage": summary["stage"].replace("_", " ").title(),
            "stage_progress": summary["stage_progress"] * 100,
            "overall_progress": summary["overall_progress"] * 100,
        }

        return stage_table, results, chart_fig, temp_fig, download_btn_style, report_data, chart_fig.to_json()

    # ---- Mode B: Plan Harvest ----
    else:
        if planting_date <= today:
            return (
                stage_table, "Plan mode requires a future planting date.",
                go.Figure(), go.Figure(), {"display": "none"}, {}, {},
            )

        harvest_gdd = crop_params["stages"]["harvest"]
        max_daily = crop_params["t_upper"] - crop_params["t_base"]
        if max_daily > 0:
            estimated_days = int(harvest_gdd / max_daily) + 60
        else:
            estimated_days = 365
        estimated_days = min(estimated_days, 365)

        end_date = planting_date + dt.timedelta(days=estimated_days)
        if end_date > dt.date(2050, 12, 31):
            end_date = dt.date(2050, 12, 31)

        try:
            weather = fetch_climate_temp(lat, lon, planting_date.isoformat(), end_date.isoformat())
        except Exception as e:
            return stage_table, f"Could not fetch climate data: {e}", go.Figure(), go.Figure(), {"display": "none"}, {}, {}

        if weather.empty:
            return stage_table, "No climate data available for this location and date range.", go.Figure(), go.Figure(), {"display": "none"}, {}, {}

        chart_fig, stage_dates = build_planning_chart(
            weather, crop_params, crop_id, location_name, planting_date,
        )
        temp_fig = build_temperature_chart(weather, location_name, planting_date)

        result_items = [
            html.H4("Projected Growth Stages", style={"marginBottom": "8px"}),
            html.P(f"Crop: {crop_label}"),
            html.P(f"Planting Date: {planting_date.isoformat()}"),
            html.Hr(),
        ]
        for stage_name in ["initial", "development", "mid_season", "harvest"]:
            label = stage_name.replace("_", " ").title()
            if stage_name in stage_dates:
                est = stage_dates[stage_name]
                days_from_plant = (est - planting_date).days if isinstance(est, dt.date) else "?"
                result_items.append(html.P(f"{label}: {est} ({days_from_plant} days)"))
            else:
                result_items.append(html.P(f"{label}: beyond projection range"))

        results = html.Div(result_items)

        report_data = {
            "mode": "plan",
            "location": location_name,
            "latitude": lat,
            "longitude": lon,
            "crop_label": crop_label,
            "t_base": crop_params["t_base"],
            "t_upper": crop_params["t_upper"],
            "planting_date": planting_date.isoformat(),
            "stage_dates": {k: str(v) for k, v in stage_dates.items()},
        }

        return stage_table, results, chart_fig, temp_fig, download_btn_style, report_data, chart_fig.to_json()


# Callback 5: Download PDF
@callback(
    Output("download-pdf", "data"),
    Input("btn-download", "n_clicks"),
    State("store-report", "data"),
    State("store-chart", "data"),
    prevent_initial_call=True,
)
def download_pdf(n_clicks, report_data, chart_json):
    if not report_data or not chart_json:
        return no_update

    try:
        chart_fig = go.Figure(pio.from_json(chart_json))
    except Exception:
        chart_fig = go.Figure()

    pdf_bytes = generate_pdf_report(report_data, chart_fig)

    crop = report_data.get("crop_label", "crop").replace(" ", "_")
    filename = f"GDD_Report_{crop}_{dt.date.today().isoformat()}.pdf"

    return dcc.send_bytes(pdf_bytes, filename)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
