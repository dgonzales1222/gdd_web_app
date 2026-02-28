import datetime as dt
import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from crops_data import crops 

# Fetch daily temperature data using Open-Meteo API
def fetch_daily_temp(latitude, longitude, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_min,temperature_2m_max",
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmins = daily.get("temperature_2m_min", [])
    tmaxs = daily.get("temperature_2m_max", [])

    if not (len(dates) == len(tmins) == len(tmaxs)):
        raise ValueError("Open-Meteo response arrays have different lengths.")

    df = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "tmin": [float(t) for t in tmins],
        "tmax": [float(t) for t in tmaxs],
    })

    return df

# Compute the daily growing degree days (GDD)
def compute_daily_gdd(tmin, tmax, t_base, t_upper):
    t_avg = (tmin + tmax) / 2.0

    if t_avg < t_base:
        return 0.0
    if t_avg > t_upper:
        return t_upper - t_base
    return t_avg - t_base

# Determine the Growing Stage of the CropSeason based on the current CGDD
def determine_growing_stage(cumulative_gdd, stages_cumulative):
    initial = stages_cumulative["initial"]
    development = stages_cumulative["development"]
    mid_season = stages_cumulative["mid_season"]
    harvest = stages_cumulative["harvest"]

    if cumulative_gdd <= initial:
        stage = "initial"
        stage_start, stage_end = 0.0, initial
    elif cumulative_gdd <= development:
        stage = "development"
        stage_start, stage_end = initial, development
    elif cumulative_gdd <= mid_season:
        stage = "mid_season"
        stage_start, stage_end = development, mid_season
    elif cumulative_gdd <= harvest:
        stage = "harvest"
        stage_start, stage_end = mid_season, harvest
    else:
        stage = "post_harvest"
        stage_start, stage_end = harvest, harvest

    if stage_start == stage_end:
        progress = 1.0
    else:
        progress = (cumulative_gdd - stage_start) / (stage_end - stage_start)

    progress = max(0.0, min(1.0, progress))
    return stage, progress

# Build a dataframe of historical temperature data for visualization (relplot)
def build_historical_gdd_dataframe(
    latitude,
    longitude,
    planting_date,
    window_days,
    t_base,
    t_upper,
    earliest_year=1979,
):
    current_year = dt.date.today().year
    # use all past years from earliest_year up to last year
    start_year = earliest_year
    years = list(range(start_year, current_year))

    records = []
    for y in years:
        start = planting_date.replace(year=y)
        end = start + dt.timedelta(days=window_days - 1)

        weather_hist = fetch_daily_temp(
            latitude,
            longitude,
            start.isoformat(),
            end.isoformat(),
        )

        if len(weather_hist) < window_days:
            continue

        daily_gdd = weather_hist.apply(
            lambda row: compute_daily_gdd(row["tmin"], row["tmax"], t_base, t_upper),
            axis=1,
        )
        cumulative_gdd = daily_gdd.cumsum().tolist()

        for day_index, cgdd in enumerate(cumulative_gdd, start=1):
            records.append(
                {
                    "day": day_index,
                    "cgdd": cgdd,
                    "year": y,
                }
            )

    if not records:
        return pd.DataFrame(columns=["day", "cgdd", "year"])

    return pd.DataFrame.from_records(records)

# Visualize cumulative GDD with ideal gdd line and historical gdd line.
def plot_gdd_progress(season, latitude, longitude):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    dates = season.weather["date"]
    actual_cumulative = season.weather["cumulative_gdd"]

    if len(dates) == 0 or len(actual_cumulative) == 0:
        print("No GDD data available to plot.")
        return

    window_days = len(dates)
    t_base = season.params["t_base"]
    t_upper = season.params["t_upper"]

    upper_daily = t_upper - t_base
    upper_bound = [upper_daily * (i + 1) for i in range(window_days)]

    hist_df = build_historical_gdd_dataframe(
        latitude,
        longitude,
        season.planting_date,
        window_days,
        t_base,
        t_upper,
    )

    sns.set_theme(style="whitegrid")

    if not hist_df.empty:
        g = sns.relplot(
        data=hist_df,
        x="day",
        y="cgdd",
        kind="line",
        errorbar="sd",
        linewidth=1,
        )
        ax = g.axes[0, 0]

        # Dummy line for legend entry
        ax.plot(
            [],
            [],
            color="C0",
            linewidth=2,
            label="Historical GDD (Open-Meteo, past years)",
        )
    else:
        fig, ax = plt.subplots()

    x_days = list(range(1, window_days + 1))

    ax.plot(
        x_days,
        upper_bound,
        linestyle="--",
        linewidth=1.5,
        label="Ideal GDD",
    )

    ax.plot(
        x_days,
        actual_cumulative,
        linewidth=2,
        label="Actual GDD (Open-Meteo)",
    )
    ax.scatter(
        x_days[-1],
        actual_cumulative.iloc[-1],
    )

    ax.set_title(f"Cumulative GDD Progress – {season.crop_id} ({season.location})")
    ax.set_xlabel("Days since planting")
    ax.set_ylabel("Cumulative GDD")
    ax.legend()
    plt.tight_layout()

    safe_location = season.location.replace(" ", "_")
    filename = f"{dt.date.today().isoformat()}_{season.crop_id}_{safe_location}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=200)
    plt.close()

    print(f"Saved plot to: {filepath}")

# Create CropSeason class
class CropSeason:
    # Initialize CropSeason
    def __init__(self, crop_id, planting_date, weather_series, location):
        if crop_id not in crops:
            raise ValueError(f"Unsupported crop_id: {crop_id}")

        if not isinstance(weather_series, pd.DataFrame):
            raise TypeError("weather_series must be a pandas DataFrame")

        self.crop_id = crop_id
        self.location = location
        self.params = crops[crop_id]
        self.planting_date = planting_date

        weather_df = weather_series.copy()
        weather_df = weather_df[weather_df["date"].dt.date >= planting_date]
        weather_df = weather_df.sort_values("date").reset_index(drop=True)

        self.weather = weather_df

    # Compute gdd time series (from planting date to current date)
    def compute_gdd_series(self):
        t_base = self.params["t_base"]
        t_upper = self.params["t_upper"]

        self.weather["daily_gdd"] = self.weather.apply(
            lambda row: compute_daily_gdd(row["tmin"], row["tmax"], t_base, t_upper),
            axis=1,
        )
        self.weather["cumulative_gdd"] = self.weather["daily_gdd"].cumsum()

    # Get current crop stage based on the given date
    def stage_on_date(self, target_date):
        if "cumulative_gdd" not in self.weather.columns:
            self.compute_gdd_series()

        subset = self.weather[self.weather["date"].dt.date <= target_date]
        if subset.empty:
            return "pre_planting", 0.0, 0.0

        cumulative_gdd = subset.iloc[-1]["cumulative_gdd"]
        stage, progress = determine_growing_stage(
            cumulative_gdd,
            self.params["stages"],
        )
        return stage, progress, cumulative_gdd

    # Generate the current summary of the cropping season
    def summary_today(self):
        if self.weather.empty:
            return {
                "crop_id": self.crop_id,
                "date": None,
                "cumulative_gdd": 0.0,
                "stage": "no_data",
                "stage_progress": 0.0,
                "overall_progress": 0.0,
            }

        last_row = self.weather.iloc[-1]
        last_date = last_row["date"].date()

        if "cumulative_gdd" not in self.weather.columns:
            self.compute_gdd_series()
            last_row = self.weather.iloc[-1]

        cumulative_gdd = last_row["cumulative_gdd"]
        stage, stage_progress, _ = self.stage_on_date(last_date)

        harvest_gdd = self.params["stages"]["harvest"]
        overall_progress = 1.0 if harvest_gdd == 0 else cumulative_gdd / harvest_gdd
        overall_progress = max(0.0, min(1.0, overall_progress))

        return {
            "crop_id": self.crop_id,
            "date": last_date.isoformat(),
            "cumulative_gdd": cumulative_gdd,
            "stage": stage,
            "stage_progress": stage_progress,
            "overall_progress": overall_progress,
        }
    
# Main program execution
def main():

    crop_id = input("\nEnter crop_id: ").strip()
    if crop_id not in crops:
        print("Invalid crop_id.")
        return

    location = input("Location: ").strip()

    try:
        latitude = float(input("Latitude: "))
        longitude = float(input("Longitude: "))
    except ValueError:
        print("Invalid coordinates.")
        return

    try:
        planting_date = dt.date.fromisoformat(
            input("Planting date (YYYY-MM-DD): ").strip()
        )
    except ValueError:
        print("Invalid planting date.")
        return

    today = dt.date.today()
    if planting_date > today:
        print("Planting date cannot be in the future.")
        return

    weather = fetch_daily_temp(
        latitude,
        longitude,
        planting_date.isoformat(),
        today.isoformat(),
    )

    season = CropSeason(crop_id, planting_date, weather, location)
    season.compute_gdd_series()
    summary = season.summary_today()

    print("\n=== Results ===")
    print(f"Current Date    : {summary['date']}")
    print(f"Crop            : {summary['crop_id']}")
    print(f"Location        : {season.location}")
    print(f"Cumulative GDD  : {summary['cumulative_gdd']:.2f}")
    print(f"Stage           : {summary['stage']}")
    print(f"Stage progress  : {summary['stage_progress']*100:.2f}%")
    print(f"Overall progress: {summary['overall_progress']*100:.2f}%")

    save_plot = input("\nSave GDD progress plot to file? (y/n): ").strip().lower()
    if save_plot == "y":
        plot_gdd_progress(season, latitude, longitude)

# Runs the main program when the script is executed directly
if __name__ == "__main__":
    main()