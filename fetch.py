import os
from pathlib import Path

import requests
import pandas as pd

CENSUS_KEY = os.environ.get("CENSUS_API_KEY")
if not CENSUS_KEY:
    raise SystemExit("Set CENSUS_API_KEY in your environment (e.g. source ~/.zshrc).")

OUTPUT_DIR = Path(__file__).resolve().parent / "input"

years = [2009, 2014, 2019, 2024]

variables = {
    "total": "B25040_001E",
    "utility_gas": "B25040_002E",
    "propane": "B25040_003E",
    "electricity": "B25040_004E",
    "fuel_oil": "B25040_005E",
    "coal": "B25040_006E",
    "wood": "B25040_007E",
    "solar": "B25040_008E",
    "other": "B25040_009E",
    "no_fuel": "B25040_010E"
}

frames = []

for year in years:
    host = "api.census.gov"
    url = f"https://{host}/data/{year}/acs/acs5"

    params = {
        "get": "NAME," + ",".join(variables.values()),
        "for": "county:*",
        "in": "state:30",
        "key": CENSUS_KEY
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    data = r.json()
    df = pd.DataFrame(data[1:], columns=data[0])

    # Rename Census variables
    df = df.rename(columns={v: k for k, v in variables.items()})

    # Convert estimates to numbers
    for col in variables:
        df[col] = pd.to_numeric(df[col])

    # Clean county name
    df["county"] = (
        df["NAME"]
        .str.replace(", Montana", "", regex=False)
        .str.replace(" County", "", regex=False)
    )

    # ACS vintage / actual survey period
    df["acs_year"] = year
    df["period"] = {
        2009: "2005–09",
        2014: "2010–14",
        2019: "2015–19",
        2024: "2020–24"
    }[year]

    # Calculate percentage of occupied homes
    fuels = [
        "utility_gas",
        "propane",
        "electricity",
        "fuel_oil",
        "coal",
        "wood",
        "solar",
        "other",
        "no_fuel"
    ]

    for fuel in fuels:
        df[f"{fuel}_pct"] = df[fuel] / df["total"] * 100

    frames.append(df)

heating = pd.concat(frames, ignore_index=True)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
heating.to_csv(OUTPUT_DIR / "montana_county_heating_fuel_2009_2024.csv", index=False)
