import pytest
import datetime as dt
import pandas as pd
from project import compute_daily_gdd, determine_growing_stage, CropSeason, crops


def test_compute_daily_gdd():

    # Test computed GDD if the average temperature is below the base temperature.
    result = compute_daily_gdd(tmin=5.0, tmax=7.0, t_base=10.0, t_upper=30.0)
    assert result == 0.0

    # Test computed GDD if the average temperature is between thresholds.
    result = compute_daily_gdd(tmin=10.0, tmax=20.0, t_base=10.0, t_upper=30.0)
    assert result == 5.0

    # Test computed GDD if the average temperature is above the upper temperature.
    result = compute_daily_gdd(tmin=40.0, tmax=42.0, t_base=10.0, t_upper=30.0)
    assert result == 20.0



def test_determine_growing_stage():

    # Define representative cumulative GDD thresholds for each crop growth stage.
    stages = {"initial": 100.0, "development": 200.0, "mid_season": 300.0, "harvest": 400.0}

    # Evaluate growth stage and progress at cumulative GDD values spanning all phenological phases.
    stage_init, progress_init = determine_growing_stage(50.0, stages)
    stage_dev, progress_dev = determine_growing_stage(150.0, stages)
    stage_mid, progress_mid = determine_growing_stage(250.0, stages)
    stage_harvest, progress_harvest = determine_growing_stage(350.0, stages)
    stage_post, progress_post = determine_growing_stage(450.0, stages)

    # Assert correct stage labels and ensure progress values remain within valid bounds (0 to 1).
    assert stage_init == "initial"
    assert 0.0 <= progress_init <= 1.0

    assert stage_dev == "development"
    assert 0.0 <= progress_dev <= 1.0

    assert stage_mid == "mid_season"
    assert 0.0 <= progress_mid <= 1.0

    assert stage_harvest == "harvest"
    assert 0.0 <= progress_harvest <= 1.0

    assert stage_post == "post_harvest"
    assert 0.0 <= progress_post <= 1.0

# Build a test CropSeason instance for testing.
def build_test_season():

    # Define a test crop containing info on temperature requirements and cumulative GDD per growth stage)
    crops["test_crop"] = {
        "t_base": 5.0,
        "t_upper": 30.0,
        "stages": {
            "initial": 50.0,
            "development": 100.0,
            "mid_season": 200.0,
            "harvest": 300.0,
        },
    }

    # Create a weather dataframe for testing
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    tmin = [6.0, 8.0, 10.0, 12.0, 14.0]
    tmax = [16.0, 18.0, 20.0, 22.0, 24.0]
    weather_df = pd.DataFrame({"date": dates, "tmin": tmin, "tmax": tmax})

    # Compute GDD using .compute_gdd_series() using the predefined testing parameters.
    planting_date = dt.date(2025, 1, 1)
    season = CropSeason("test_crop", planting_date, weather_df, "TestLocation")
    season.compute_gdd_series()

    return season, tmin, tmax

def test_cropseason_gdd():
    season, tmin, tmax = build_test_season()

    # Verify that GDD-related columns are created and correct.
    assert "daily_gdd" in season.weather.columns
    assert "cumulative_gdd" in season.weather.columns
    assert len(season.weather) == 5

def test_cropseason_summary():
    season, tmin, tmax = build_test_season()

    # Valdiate the integrity and bounds of the season summary and phenological growth stage.
    summary = season.summary_today()
    assert summary["crop_id"] == "test_crop"
    assert summary["stage"] in {"initial", "development", "mid_season", "harvest", "post_harvest"}
    assert 0.0 <= summary["stage_progress"] <= 1.0
    assert 0.0 <= summary["overall_progress"] <= 1.0


def test_init():
    dates = pd.date_range("2025-01-01", periods=3, freq="D")
    weather_df = pd.DataFrame(
        {"date": dates, "tmin": [10.0, 10.0, 10.0], "tmax": [20.0, 20.0, 20.0]}
    )
    planting_date = dt.date(2025, 1, 1)

    # If crop_id is not in crops_data

    with pytest.raises(ValueError):
        CropSeason("invalid_crop", planting_date, weather_df, "TestLocation")

    # Invalid weather input
    with pytest.raises(TypeError):
        CropSeason("test_crop", planting_date, "not_a_dataframe", "TestLocation")