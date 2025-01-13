import streamlit as st # type: ignore
import pandas as pd
from textblob import TextBlob
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict

def setup_page():
    st.set_page_config(
        page_title="NPS Automator",
        page_icon="📊",
        layout="wide"
    )
    st.title("NPS Automator")

def initialize_session_state():
    if 'sheet_url' not in st.session_state:
        st.session_state.sheet_url = ""
    if 'feedback_data' not in st.session_state:
        st.session_state.feedback_data = None

# def connect_to_sheets(sheet_url):
#     try:
#         # Use your Google Sheets API credentials
#         scope = ['https://spreadsheets.google.com/feeds',
#                 'https://www.googleapis.com/auth/drive']
        
#         credentials = ServiceAccountCredentials.from_json_keyfile_name(
#             'your-credentials.json', scope)
        
#         client = gspread.authorize(credentials)
#         sheet = client.open_by_url(sheet_url).sheet1
#         data = sheet.get_all_records()
#         return pd.DataFrame(data)
#     except Exception as e:
#         st.error(f"Error connecting to Google Sheet: {str(e)}")
#         return None

def analyze_sentiment(feedback):
    if pd.isna(feedback) or not isinstance(feedback, str):
        return 0
    
    analysis = TextBlob(feedback)
    return analysis.sentiment.polarity

def get_top_feedback(df, feedback_column, n=5, sentiment_type='positive'):
    if df is None or feedback_column not in df.columns:
        return []
    
    df['sentiment'] = df[feedback_column].apply(analyze_sentiment)
    
    if sentiment_type == 'positive':
        sorted_df = df.nlargest(n, 'sentiment')
    else:
        sorted_df = df.nsmallest(n, 'sentiment')
    
    return sorted_df[feedback_column].tolist()

def main():
    setup_page()
    initialize_session_state()
    
    # Create sidebar
    with st.sidebar:
        st.header("Controls")
        if st.button("Analyze Feedback"):
            if st.session_state.sheet_url:
                with st.spinner("Analyzing feedback..."):
                    df = connect_to_sheets(st.session_state.sheet_url)
                    if df is not None:
                        st.session_state.feedback_data = df
                        st.success("Analysis complete!")
            else:
                st.warning("Please enter a Google Sheet URL first")
    
    # Main content area
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Google Sheet URL")
        sheet_url = st.text_input(
            "Enter the URL of your Google Sheet",
            value=st.session_state.sheet_url,
            key="sheet_url_input"
        )
        if st.button("Submit"):
            st.session_state.sheet_url = sheet_url
            st.success("URL submitted successfully!")
    
    # Display results if data is available
    if st.session_state.feedback_data is not None:
        st.header("Analysis Results")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Top 5 Positive Feedback")
            positive_feedback = get_top_feedback(
                st.session_state.feedback_data,
                'feedback_column',  # Replace with your actual column name
                5,
                'positive'
            )
            for i, feedback in enumerate(positive_feedback, 1):
                st.write(f"{i}. {feedback}")
        
        with col4:
            st.subheader("Top 5 Negative Feedback")
            negative_feedback = get_top_feedback(
                st.session_state.feedback_data,
                'feedback_column',  # Replace with your actual column name
                5,
                'negative'
            )
            for i, feedback in enumerate(negative_feedback, 1):
                st.write(f"{i}. {feedback}")

if __name__ == "__main__":
    main()