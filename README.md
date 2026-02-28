#### Danilo III O. Gonzales (29225)
#### Master's in Green Data Science
### Project in Introduction to Python

# Growing Degree Days (GDD) and Crop Phenology Estimation of a Cropping Season

## Project Description

This project implements a Python-based tool to compute the growing degree days (GDD) and determine the current crop growth stage (phenology) for selected vegetable and field crops. The model uses daily air temperature data retrieved from the Open-Meteo API and applies crop-specific thermal thresholds derived from the revised FAO56 guidelines (FAO56rev).

Unlike cropping calendar-based approaches, this project estimates crop development using cumulative thermal time, providing a biologically meaningful representation of crop growth.

### Project File Structure

- **`app.py`** – Interactive web application built with Dash and Plotly. Provides an interactive map, location search, two operational modes (Check Progress and Plan Harvest), GDD progress charts, and PDF report export.

- **`project.py`** – Core program file containing data retrieval from Open-Meteo, GDD computation, crop growth stage estimation, visualization, and the `CropSeason` class.

- **`crops_data.py`** – Defines crop-specific thermal parameters and cumulative GDD thresholds for phenological stages.

- **`test_project.py`** – Implements unit tests using `pytest` to verify GDD calculations, growth stage logic, class behavior, and error handling.

- **`requirements.txt`** – Lists all Python dependencies required to run the project.

- **`README.md`** – Provides project background, methodology, workflow, inputs and outputs, limitations, and references.

### Growing Degree Days (GDD)

Growing Degree Days (GDD) quantify accumulated thermal time for crop growth using daily air temperature relative to crop-specific base and upper thresholds. Daily GDD values are zero below the base temperature, increase linearly between thresholds, and are capped above the upper threshold. Cumulative GDD from planting indicates crop progress independent of calendar time and is used to estimate phenological stages, schedule management operations, and predict harvest timing.

GDD are calculated using a piecewise temperature-threshold approach (Paredes et al., 2025). Equation 1 expresses daily GDD as a function of mean air temperature relative to crop-specific base and upper thresholds. Equation 2 defines mean air temperature as the average of daily maximum and minimum temperatures.

![eq_1_2](./images/equations_gdd-2.png)

**where:**

- **GDD** is the growing degree days  
- **T<sub>max</sub> (°C)** is the daily maximum air temperature  
- **T<sub>min</sub> (°C)** is the daily minimum air temperature  
- **T<sub>avg</sub> (°C)** is the daily mean air temperature  
- **T<sub>base</sub> (°C)** is the base temperature below which crop development ceases  
- **T<sub>upper</sub> (°C)** is the upper temperature threshold above which crop development no longer increases


While daily GDD values describe short-term thermal accumulation, crop development is more accurately represented by the cumulative sum of GDD over time. Cumulative Growing Degree Days (CGDD), as shown in Equation 3,  are obtained by summing daily GDD values from the planting date onward and serve as a thermal-time proxy for crop phenological progression.



![equation_3](./images/equation_3.png)

**where:**

- **CGDD** is the cumulative growing degree days  
- **GDD<sub>i</sub>** is the growing degree days on day *i*  
- **n** is the number of days elapsed since planting


In this project, cumulative GDD is used as the primary indicator for estimating the progress of the current crop season. Because CGDD integrates the effects of daily temperature variability, it provides a more biologically consistent measure of crop development than calendar-based approaches, particularly under variable or changing climatic conditions.

### FAO-56 Crop Growth Stages

The FAO-56 framework defines crop development as a sequence of four generalized growth stages: initial, development, mid-season, and late season. The initial stage begins immediately after planting and is characterized by slow growth and limited canopy development. During the development stage, vegetative growth accelerates as leaf area expands and thermal accumulation increases rapidly. The mid-season stage corresponds to effective full canopy cover and sustained physiological activity, during which crop development progresses at a relatively steady rate. Finally, the late-season stage marks the transition toward maturity, as growth slows, senescence begins, and the crop approaches harvest. In this project, these stages are represented using crop-specific cumulative Growing Degree Day (GDD) thresholds, allowing phenological progression to respond dynamically to temperature conditions rather than fixed calendar dates (Pereira et al., 2025).

**Figure 1** <br>
*FAO-56 Crop Growth Stage*<br>
![Crop](./images/crop_growth_stage.png)

### Weather Data Source
Open-Meteo is an open-access weather API that provides historical and forecast data (Zippenfenig, 2023). This program uses Open-Meteo to obtain daily minimum and maximum air temperatures for a specified location. These temperatures are used to calculate GDD and estimate crop growth stages.

### Program Workflow Overview

The program's overall workflow is illustrated in Figure 2. The process begins with user-provided inputs that define the crop type, location, and planting date. These inputs are validated before being used to retrieve daily temperature data from the Open-Meteo weather database. The retrieved weather data are then used to initialize a CropSeason object, within which daily and cumulative Growing Degree Days (GDD) are computed, and the current crop growth stage is determined. The program subsequently generates a visualization of GDD progression and prompts the user to save the plot, if desired. This workflow highlights the model's sequential structure, from data input and validation to computation, visualization, and output generation.

**Figure 2** <br>
*Flowchart of GDD-Based Crop Season Modeling*<br>
![program_workflow](./images/program_workflow.png)

#### Inputs
1. `crop_id` - identifies the crop to be modeled and determines the crop-specific temperature requirements as well as cumulative GDD thresholds used for phenological stage estimation.
2. `location` - descriptive name used for labeling outputs and saved figures.
3. `latitude` - specifies the north-south position of the field location and is required for retrieving temperature data from Open-Meteo.
4. `longitude` - specifies the east-west position of the field location and is required for retrieving temperature data from Open-Meteo.
5. `planting_date` - Defines the start of the growing season and serves as the reference date for accumulating daily and cumulative GDD.

**Figure 3** <br>
*Example Input*<br>
<img src="./images/input_sample.png" width="600">

#### Outputs and Visualization

The program produces two types of outputs:
1. The first one is the **textual summary** showing the current date, crop type, location, cumulative GDD, estimated growth stage, and progress within the stage.<br><br>

**Figure 4** <br>
*Example Textual Summary Output*<br>
<img src="./images/summary_sample.png" width="600"><br>

2. The second output is the **GDD Progress Plot**. When selected by the user (by responding “y” to the prompt), the program generates a plot showing the historical cumulative GDD distribution based on Open-Meteo temperature data, an ideal GDD trajectory assuming optimal thermal conditions, and the actual cumulative GDD for the current season. <br>

**Figure 5** <br>
*Example GDD Progress Plot Output*<br>
<img src="./images/2026-01-21_lettuce_short_Benguet.png" width="600">

#### Testing

Unit tests were implemented using `pytest` and are located in `test_project.py`.  
The tests verify the correctness of the GDD calculation, phenological stage determination, `CropSeason` class behavior, and error handling for invalid inputs.

### Web Application (`app.py`)

In addition to the CLI tool, this project includes an interactive web application built with **Dash** and **Plotly**. The web app provides a visual, map-based interface for GDD computation and crop planning.

#### Running the Web App

```
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:8050` in your browser.

#### Features

- **Interactive Map** – OpenStreetMap-based map with location search via the Open-Meteo Geocoding API. Users can search by place name or enter coordinates manually.
- **Crop and Season Selection** – Two linked dropdowns: one for the crop name (e.g., Broccoli, Potato) and one for the season variant (e.g., Long, Short). The season dropdown updates dynamically based on the selected crop.
- **Two Operational Modes:**
  - **Check Progress** – For monitoring an existing crop. Uses the Open-Meteo Archive API to fetch actual weather data from the planting date to the current date and computes cumulative GDD, current growth stage, and progress.
  - **Plan Harvest** – For planning a future planting. Uses the Open-Meteo Climate API (CMIP6 model: EC_Earth3P_HR) to project daily temperatures and estimate when each growth stage will be reached, including the projected harvest date.
- **GDD Progress Chart** – Interactive Plotly chart showing cumulative GDD over time with growth stage threshold lines.
- **PDF Report Export** – One-page PDF report containing location details, crop parameters, GDD results, and the embedded chart. Generated using `fpdf2` and downloadable directly from the browser.

#### Web App Dependencies

The web app requires the following additional packages (included in `requirements.txt`):
- `dash` – Web application framework
- `plotly` – Interactive charting
- `fpdf2` – PDF report generation
- `kaleido` – Plotly static image export for PDF embedding

### Limitations

The CLI tool evaluates crop development only from the user-defined planting date up to the current date, using available historical temperature data to estimate cumulative Growing Degree Days (GDD) and the present phenological stage. The web app extends this capability with a Plan Harvest mode that uses climate model projections (CMIP6) for future date ranges up to 2050. However, climate projections are based on modeled data and may differ from actual conditions. Both tools are limited to vegetables and field crops.

### References

Paredes, P., López-Urrea, R., Martínez-Romero, Á., Petry, M., do Rosário Cameira, M., Montoya, F., … Pereira, L. S. (2025). Estimating the lengths of crop growth stages to define the crop coefficient curves using growing degree days (GDD): Application of the revised FAO56 guidelines. *Agricultural Water Management*, 319, 109758. [doi:10.1016/j.agwat.2025.109758](https://doi.org/10.1016/j.agwat.2025.109758)

Pereira, L. S., Allen, R. G., Paredes, P., López-Urrea, R., Raes, D., Smith, M., Kilic, A., & Salman, M. (2025). Crop evapotranspiration: Guidelines for computing crop water requirements (FAO Irrigation and Drainage Paper No. 56rev). Food and Agriculture Organization of the United Nations. https://www.fao.org/4/x0490e/x0490e00.htm

Zippenfenig, P. (2023). Open-Meteo.com Weather API [Computer software]. Zenodo. https://doi.org/10.5281/ZENODO.7970649