from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel
import os
import json
import pandas as pd
from auth import gsheet_client
from .feedback_generator import generate_feedback_from_ai
from urllib.parse import urlparse, parse_qs


# Define the router
review_router = APIRouter(
    prefix="/extract-reviews",
    tags=["Extract Reviews"]
)

class Config(BaseModel):
    json_file: str = "col_keys.json"
    json_output_file: str = "../reviews_data.json"

@review_router.get("/", summary="Extract reviews from Google Sheets")
def extract_reviews(
    spreadsheet_url: str = Query(..., description="URL of the Google Spreadsheet to process"),
    config: Config = Config(),
):
    """
    Extract reviews from Google Sheets, process them, and save results in JSON format.
    """
    try:
        # Extract the spreadsheet ID from the URL
        parsed_url = urlparse(spreadsheet_url)
        print("parsed_url -->",parsed_url,"\n")
        # query_params = parse_qs(parsed_url.query)
        # print("query_params -->",query_params,"\n")
        path_segments = parsed_url.path.split("/")
        print("path_segments -->",path_segments,"\n")

        # Ensure the path is valid
        if len(path_segments) > 2 and path_segments[2] == "d":
            spreadsheet_id = path_segments[3]
        else:
            raise HTTPException(status_code=400, detail="Invalid Google Sheets URL. Spreadsheet ID not found.")
        print("spreadsheet_id -->",spreadsheet_id,"\n")
        if not spreadsheet_id:
            raise HTTPException(status_code=400, detail="Invalid Google Sheets URL. Spreadsheet ID not found.")

        # Open the spreadsheet
        sheet = gsheet_client.open_by_key(spreadsheet_id).sheet1

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

        # Replace empty strings with NaN
        renamed_df.replace("", pd.NA, inplace=True)

        # Drop rows with NaN values or empty strings in the selected columns
        cleaned_df = renamed_df.dropna(subset=json_data.values())

        # Create a structured JSON object
        structured_json = {
            "engineer_feedback": cleaned_df["engineer_feedback"].tolist() if "engineer_feedback" in cleaned_df.columns else [],
            "program_likings": cleaned_df["program_likings"].tolist() if "program_likings" in cleaned_df.columns else [],
            "topics_learned": cleaned_df["topics_learned"].tolist() if "topics_learned" in cleaned_df.columns else [],
            "program_improvements": cleaned_df["program_improvements"].tolist() if "program_improvements" in cleaned_df.columns else [],
            "engineer_improvements": cleaned_df["engineer_improvements"].tolist() if "engineer_improvements" in cleaned_df.columns else []
        }

        # Write the structured JSON object to a file
        with open(config.json_output_file, "w") as json_file:
            json.dump(structured_json, json_file, indent=4)
        ai_rep = generate_feedback_from_ai()
        print("ai_rep -->",ai_rep)
        return {
            "message": "Reviews successfully extracted and saved.",
            "payload": {
                "json_file_name": config.json_output_file,
                "feedback_generated": ai_rep
            },
            "status": status.HTTP_200_OK
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
