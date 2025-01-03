from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from auth import gsheet_client
import pandas as pd
import json
import os

app = FastAPI()

SPREADSHEET_NAME = "Copy of Digit Insurance-049- Feedback Survey (Responses)"


class Config(BaseModel):
    json_file: str = "col_keys.json"
    csv_file: str = "reviews_data.csv"
    json_output_file: str = "reviews_data.json"


@app.get("/extract-reviews", summary="Extract reviews from Google Sheets")
def extract_reviews(config: Config = Config()):
    """
    Extract reviews from Google Sheets, process them, and save results in CSV and JSON formats.
    """
    try:
        # Open the spreadsheet
        sheet = gsheet_client.open(SPREADSHEET_NAME).sheet1

        # Load JSON keys
        if not os.path.exists(config.json_file):
            raise HTTPException(status_code=404, detail="Column keys JSON file not found.")

        with open(config.json_file, "r") as f:
            json_data = json.load(f)

        # Read data from the spreadsheet
        data = sheet.get_all_records()

        # Convert to a Pandas DataFrame
        df = pd.DataFrame(data)

        # Validate keys in the DataFrame
        keys = json_data.keys() if isinstance(json_data, dict) else []
        if not all(key in df.columns for key in keys):
            raise HTTPException(status_code=400, detail="Some keys in the JSON file do not match the DataFrame columns.")

        # Filter the DataFrame based on the keys
        filtered_df = df[keys]

        # Rename the columns
        renamed_df = filtered_df.rename(columns=dict(json_data))

        # Write to a CSV file
        renamed_df.to_csv(config.csv_file, mode='a', index=False, header=not os.path.exists(config.csv_file))

        # Write to a JSON file
        renamed_df.to_json(config.json_output_file, orient="records", lines=False, indent=4)

        return {
            "message": "Reviews successfully extracted and saved.",
            "csv_file": config.csv_file,
            "json_file": config.json_output_file,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
