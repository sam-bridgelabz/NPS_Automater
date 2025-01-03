from auth import gsheet_client
import pandas as pd
import json
import os

# returns a list of reviews from the spreadsheet
def extract_reviews():
    # Open the spreadsheet by its name or URL
    SPREADSHEET_NAME = "Copy of Digit Insurance-049- Feedback Survey (Responses)"
    sheet = gsheet_client.open(SPREADSHEET_NAME).sheet1  # Access the first sheet

    with open("col_keys.json", "r") as f:
        json_data = json.load(f)

    # Read data from the spreadsheet
    data = sheet.get_all_records()

    # Convert to a Pandas DataFrame
    df = pd.DataFrame(data)

    # Get the keys of the JSON data
    keys = json_data.keys() if isinstance(json_data, dict) else []

    # Filter the DataFrame based on the keys
    filtered_df = df[keys]
    print(filtered_df)

    # Select and rename the columns
    renamed_df = filtered_df[keys].rename(columns=dict(json_data))

    # # Write to DataFrame to a CSV file
    file_name = "reviews_data.csv"
    renamed_df.to_csv(file_name, mode='a', index=False, header=not os.path.exists(file_name))

    # Write the DataFrame to a JSON file
    file_name = "reviews_data.json"
    renamed_df.to_json(file_name, orient="records", lines=False, indent=4)

    # Extract data from the column data from the DataFrame
    # review_list = df[keys].to_dict(orient='records')
    # review_list = [
    #     {json_data[key]: value for key, value in record.items()}
    #     for record in df[keys].to_dict(orient='records')
    # ]
    # print(review_list)
