from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from auth import gsheet_client
import pandas as pd
import json
import os
import argparse

def get_spreadsheet_name():
    parser = argparse.ArgumentParser(description="Process spreadsheet name.")
    parser.add_argument(
        "spreadsheet_name",
        type=str,
        help="Name of the Google Spreadsheet to process."
    )
    args = parser.parse_args()
    return args.spreadsheet_name


app = FastAPI()

# SPREADSHEET_NAME = "Copy of Digit Insurance-049- Feedback Survey (Responses)"
# SPREADSHEET_NAME = get_spreadsheet_name()


class Config(BaseModel):
    json_file: str = "col_keys.json"
    json_output_file: str = "reviews_data.json"


@app.get("/extract-reviews", summary="Extract reviews from Google Sheets")
def extract_reviews(
    spreadsheet_name: str = Query(..., description="Name of the     Google Spreadsheet to process"),
    config: Config = Config()):
    """
    Extract reviews from Google Sheets, process them, and save results in CSV and JSON formats.
    """
    try:
        SPREADSHEET_NAME = spreadsheet_name
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

        # Drop rows with null or NaN values in any of the selected columns
        cleaned_df = renamed_df.dropna(subset=json_data.values())

        # Write to a CSV file
        # renamed_df.to_csv(config.csv_file, mode='a', index=False, header=not os.path.exists(config.csv_file))

        # Create a structured JSON object
        structured_json = {
            "engineer_feedback": cleaned_df["engineer_feedback"].tolist() if "engineer_feedback" in cleaned_df.columns else [],
            "program_likings": cleaned_df["program_likings"].tolist() if "program_likings" in cleaned_df.columns else [],
            "topics_learned": cleaned_df["topics_learned"].tolist() if "topics_learned" in cleaned_df.columns else [],
        }

        # Write the structured JSON object to a file
        with open(config.json_output_file, "w") as json_file:
            json.dump(structured_json, json_file, indent=4)

        return {
            "message": "Reviews successfully extracted and saved.",
            "json_file": config.json_output_file,
            "data_preview": structured_json,  # Optional: Return preview of JSON
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
