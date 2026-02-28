# Crops database containing the base temperature (Tbase), upper temperature
# (Tupper), and phenology stage thresholds based on cumulative Growing
# Degree Days (GDD).
#
# The phenological stages follow the FAO56 framework:
#   - initial
#   - development
#   - mid-season
#   - harvest (end of late season)
#
# All temperature thresholds (Tbase, Tupper) and cumulative GDD values for
# each growth stage are derived from:
#
# Paredes, P., López-Urrea, R., Martínez-Romero, Á., Petry, M., Cameira, M.R.,
# Montoya, F., Salman, M., & Pereira, L.S. (2025).
# "Estimating the lengths of crop growth stages to define the crop coefficient
# curves using growing degree days (GDD): Application of the revised FAO56
# guidelines." Agricultural Water Management, 319, 109758.
#
# Notes on crop variants used in this database:
#
# Crop season variants (short, long, market, industry, common) are used to
# distinguish phenological differences in cumulative GDD reported in the
# literature for the same crop under different season-length or use conditions.
#
# Source tables:
#   - Tbase and Tupper: Tables 1–2
#   - Cumulative GDD for phenological stages: Table 5
#
# These values are applicable under non-limiting water and nutrient conditions
# and are intended for temperature-based phenology estimation consistent with
# FAO56rev guidelines.

crops = {
    "barley_long": {
        "t_base": 0,
        "t_upper": 30,
        "stages": {
            "initial": 300,
            "development": 975,
            "mid_season": 1665,
            "harvest": 2330,
        },
    },
    "barley_short": {
        "t_base": 0,
        "t_upper": 30,
        "stages": {
            "initial": 290,
            "development": 745,
            "mid_season": 1090,
            "harvest": 1450,
        },
    },
    "bean_seed_long": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 320,
            "development": 730,
            "mid_season": 1130,
            "harvest": 1350,
        },
    },
    "bean_seed_short": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 160,
            "development": 420,
            "mid_season": 780,
            "harvest": 960,
        },
    },
    "bell_pepper_common": {
        "t_base": 10,
        "t_upper": 35,
        "stages": {
            "initial": 445,
            "development": 1625,
            "mid_season": 2370,
            "harvest": 2415,
        },
    },
    "broccoli_long": {
        "t_base": 4.5,
        "t_upper": 30,
        "stages": {
            "initial": 295,
            "development": 645,
            "mid_season": 1170,
            "harvest": 1280,
        },
    },
    "broccoli_short": {
        "t_base": 4.5,
        "t_upper": 30,
        "stages": {
            "initial": 195,
            "development": 445,
            "mid_season": 655,
            "harvest": 755,
        },
    },
    "canola_long": {
        "t_base": 2,
        "t_upper": 30,
        "stages": {
            "initial": 460,
            "development": 1015,
            "mid_season": 1920,
            "harvest": 2515,
        },
    },
    "canola_short": {
        "t_base": 2,
        "t_upper": 30,
        "stages": {
            "initial": 330,
            "development": 640,
            "mid_season": 1090,
            "harvest": 1685,
        },
    },
    "carrot_common": {
        "t_base": 6,
        "t_upper": 30,
        "stages": {
            "initial": 320,
            "development": 785,
            "mid_season": 1285,
            "harvest": 1575,
        },
    },
    "cotton_long": {
        "t_base": 12.5,
        "t_upper": 35,
        "stages": {
            "initial": 345,
            "development": 1250,
            "mid_season": 1865,
            "harvest": 2150,
        },
    },
    "cotton_short": {
        "t_base": 12.5,
        "t_upper": 35,
        "stages": {
            "initial": 280,
            "development": 800,
            "mid_season": 1600,
            "harvest": 1950,
        },
    },
    "garlic_long": {
        "t_base": 4,
        "t_upper": 30,
        "stages": {
            "initial": 580,
            "development": 1195,
            "mid_season": 1510,
            "harvest": 1750,
        },
    },
    "garlic_short": {
        "t_base": 4,
        "t_upper": 30,
        "stages": {
            "initial": 150,
            "development": 490,
            "mid_season": 825,
            "harvest": 1140,
        },
    },
    "lettuce_long": {
        "t_base": 4,
        "t_upper": 28,
        "stages": {
            "initial": 360,
            "development": 815,
            "mid_season": 1270,
            "harvest": 1290,
        },
    },
    "lettuce_short": {
        "t_base": 4,
        "t_upper": 28,
        "stages": {
            "initial": 365,
            "development": 750,
            "mid_season": 965,
            "harvest": 985,
        },
    },
    "maize_grain_long": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 295,
            "development": 715,
            "mid_season": 1490,
            "harvest": 1955,
        },
    },
    "maize_grain_short": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 200,
            "development": 580,
            "mid_season": 1080,
            "harvest": 1540,
        },
    },
    "maize_silage_long": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 250,
            "development": 750,
            "mid_season": 1350,
            "harvest": 1550,
        },
    },
    "maize_silage_short": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 200,
            "development": 580,
            "mid_season": 1010,
            "harvest": 1130,
        },
    },
    "maize_sweet_long": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 355,
            "development": 855,
            "mid_season": 1285,
            "harvest": 1485,
        },
    },
    "maize_sweet_short": {
        "t_base": 10,
        "t_upper": 32,
        "stages": {
            "initial": 200,
            "development": 510,
            "mid_season": 870,
            "harvest": 985,
        },
    },
    "melon_long": {
        "t_base": 10,
        "t_upper": 38,
        "stages": {
            "initial": 140,
            "development": 685,
            "mid_season": 1145,
            "harvest": 1600,
        },
    },
    "melon_short": {
        "t_base": 10,
        "t_upper": 38,
        "stages": {
            "initial": 185,
            "development": 705,
            "mid_season": 1020,
            "harvest": 1175,
        },
    },
    "oats_common": {
        "t_base": 0,
        "t_upper": 30,
        "stages": {
            "initial": 450,
            "development": 1045,
            "mid_season": 1595,
            "harvest": 1850,
        },
    },
    "onion_common": {
        "t_base": 4.5,
        "t_upper": 35,
        "stages": {
            "initial": 460,
            "development": 930,
            "mid_season": 1810,
            "harvest": 2290,
        },
    },
    "pea_fresh_industry": {
        "t_base": 5,
        "t_upper": 27,
        "stages": {
            "initial": 90,
            "development": 390,
            "mid_season": 900,
            "harvest": 925,
        },
    },
    "pea_fresh_market": {
        "t_base": 5,
        "t_upper": 27,
        "stages": {
            "initial": 155,
            "development": 505,
            "mid_season": 1080,
            "harvest": 1400,
        },
    },
    "potato_long": {
        "t_base": 2,
        "t_upper": 30,
        "stages": {
            "initial": 405,
            "development": 935,
            "mid_season": 1425,
            "harvest": 2260,
        },
    },
    "potato_short": {
        "t_base": 2,
        "t_upper": 30,
        "stages": {
            "initial": 260,
            "development": 750,
            "mid_season": 1275,
            "harvest": 1600,
        },
    },
    "rice_long": {
        "t_base": 12,
        "t_upper": 35,
        "stages": {
            "initial": 255,
            "development": 745,
            "mid_season": 1485,
            "harvest": 1805,
        },
    },
    "rice_short": {
        "t_base": 12,
        "t_upper": 35,
        "stages": {
            "initial": 235,
            "development": 700,
            "mid_season": 1365,
            "harvest": 1660,
        },
    },
    "sorghum_long": {
        "t_base": 10,
        "t_upper": 30,
        "stages": {
            "initial": 280,
            "development": 590,
            "mid_season": 1240,
            "harvest": 1520,
        },
    },
    "sorghum_short": {
        "t_base": 10,
        "t_upper": 30,
        "stages": {
            "initial": 280,
            "development": 580,
            "mid_season": 1150,
            "harvest": 1380,
        },
    },
    "soybean_long": {
        "t_base": 10,
        "t_upper": 40,
        "stages": {
            "initial": 310,
            "development": 720,
            "mid_season": 1400,
            "harvest": 1960,
        },
    },
    "soybean_short": {
        "t_base": 10,
        "t_upper": 40,
        "stages": {
            "initial": 300,
            "development": 650,
            "mid_season": 1300,
            "harvest": 1650,
        },
    },
    "sunflower_long": {
        "t_base": 8,
        "t_upper": 30,
        "stages": {
            "initial": 385,
            "development": 955,
            "mid_season": 1640,
            "harvest": 1905,
        },
    },
    "sunflower_short": {
        "t_base": 8,
        "t_upper": 30,
        "stages": {
            "initial": 345,
            "development": 900,
            "mid_season": 1615,
            "harvest": 1790,
        },
    },
    "tomato_industry": {
        "t_base": 7,
        "t_upper": 28,
        "stages": {
            "initial": 280,
            "development": 800,
            "mid_season": 1680,
            "harvest": 1900,
        },
    },
    "tomato_market": {
        "t_base": 7,
        "t_upper": 28,
        "stages": {
            "initial": 325,
            "development": 985,
            "mid_season": 1865,
            "harvest": 2065,
        },
    },
    "wheat_spring_long": {
        "t_base": 0,
        "t_upper": 35,
        "stages": {
            "initial": 360,
            "development": 1040,
            "mid_season": 1760,
            "harvest": 2300,
        },
    },
    "wheat_spring_short": {
        "t_base": 0,
        "t_upper": 35,
        "stages": {
            "initial": 360,
            "development": 840,
            "mid_season": 1430,
            "harvest": 1620,
        },
    },
    "wheat_winter_long": {
        "t_base": 0,
        "t_upper": 35,
        "stages": {
            "initial": 560,
            "development": 965,
            "mid_season": 1695,
            "harvest": 2105,
        },
    },
    "wheat_winter_short": {
        "t_base": 0,
        "t_upper": 35,
        "stages": {
            "initial": 395,
            "development": 840,
            "mid_season": 1280,
            "harvest": 1645,
        },
    },
}