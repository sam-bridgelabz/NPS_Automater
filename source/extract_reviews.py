from auth import gsheet_client
import pandas as pd

# returns a list of reviews from the spreadsheet
def extract_reviews():
    # Open the spreadsheet by its name or URL
    SPREADSHEET_NAME = "Python-DailyStandup"
    sheet = gsheet_client.open(SPREADSHEET_NAME).sheet1  # Access the first sheet

    # Read data from the spreadsheet
    data = sheet.get_all_records()

    # Convert to a Pandas DataFrame
    df = pd.DataFrame(data)

    # Extract data from the "Review" column
    if "Date" in df.columns:
        review_list = df["Date"].tolist()
        print("Review Column Data as List:")
        print(review_list)
        return review_list
    else:
        print("The 'Review' column does not exist in the spreadsheet.")
        return None

