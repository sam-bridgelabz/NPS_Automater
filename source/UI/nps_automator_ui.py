import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
from fastapi import HTTPException

def setup_page():
    st.set_page_config(
        page_title="NPS Automator",
        page_icon="📊",
        layout="wide"
    )
    st.title("NPS Automator")

def call_extract_reviews(spreadsheet_url, wave_number):
    params = {
        "spreadsheet_url": spreadsheet_url,
        "wave_number": "Wave "+wave_number
    }

    try:
        # Display "Trying to fetch data" message
        with st.spinner("Trying to fetch data..."):
            fastapi_url = "http://localhost:8000/extract-reviews"
            response = requests.get(fastapi_url, params=params)

            if response.status_code == 200:
                result = response.json()
                st.success("Reviews successfully extracted. Now generating table from it...")
                st.session_state.feedback_data = result['payload']['feedback_generated']
                generate_table(st.session_state.feedback_data)
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
    except HTTPException as http_err:
        # Display the error message from HTTPException
        st.error(f"HTTP Error occurred: {http_err.detail}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def initialize_session_state():
    if "sheet_url" not in st.session_state:
        st.session_state.sheet_url = ""
    if "wave_number" not in st.session_state:
        st.session_state.wave_number = ""
    if "feedback_data" not in st.session_state:
        st.session_state.feedback_data = None

def generate_table(data):
    st.title("Feedback Analysis")

    # Modify the function to use lowercase keys
    positive_df = pd.DataFrame(data['positive_aspects'])
    positive_df.rename(columns={'aspect': 'Aspect', 'explanation': 'Explanation'}, inplace=True)

    negative_df = pd.DataFrame(data['improvements_needed'])
    negative_df.rename(columns={'aspect': 'Aspect', 'explanation': 'Explanation'}, inplace=True)

    st.subheader("Positive Aspects")
    st.table(positive_df)

    st.subheader("Improvements Needed Aspects")
    st.table(negative_df)

    # Generate PDF and create a download button
    pdf_file_path = create_pdf(positive_df, negative_df)
    if pdf_file_path:
        st.download_button(
            label="Download Feedback as PDF",
            data=open(pdf_file_path, "rb").read(),
            file_name="Feedback_Analysis.pdf",
            mime="application/pdf",
            on_click=clear_input_field  # Clear input field when download is clicked
        )

def create_pdf(positive_df, negative_df):
    try:
        # Check if required columns exist in both DataFrames
        if 'Aspect' not in positive_df.columns or 'Explanation' not in positive_df.columns:
            st.error("Positive aspects data is missing required columns.")
            return None
        if 'Aspect' not in negative_df.columns or 'Explanation' not in negative_df.columns:
            st.error("Negative aspects data is missing required columns.")
            return None

        # Create PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="Feedback Analysis", ln=True, align="C")

        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt="Positive Aspects", ln=True, align="L")
        pdf.set_font("Arial", size=12)
        for index, row in positive_df.iterrows():
            pdf.multi_cell(0, 10, txt=f"{row['Aspect']}: {row['Explanation']}")

        pdf.ln(10)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt="Improvements Needed Aspects", ln=True, align="L")
        pdf.set_font("Arial", size=12)
        for index, row in negative_df.iterrows():
            pdf.multi_cell(0, 10, txt=f"{row['Aspect']}: {row['Explanation']}")

        pdf_file_path = "feedback_analysis.pdf"
        pdf.output(pdf_file_path)
        return pdf_file_path
    except Exception as e:
        st.error(f"An error occurred while generating the PDF: {e}")
        return None

def clear_input_field():
    """Clear the input field after the file is downloaded."""
    st.session_state.sheet_url = ""  # Clear the URL input field
    st.session_state.wave_number = ""

def main():
    setup_page()
    initialize_session_state()

    # Create a navigation bar using radio buttons
    nav_items = ["Extract Reviews", "Feedback Analysis"]
    st.sidebar.title("Actions")
    nav_choice = st.sidebar.radio("Select an action", nav_items)  # Sidebar radio for navigation

    if nav_choice == "Extract Reviews":
        # Show Extract Reviews Section
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Google Sheet URL")
            st.text_input(
                "Enter the URL of your Google Sheet",
                value=st.session_state.sheet_url,
                key="sheet_url"
            )
            st.subheader("Wave Number")
            st.text_input(
                "Enter the Wave Number",
                value=st.session_state.wave_number,
                key="wave_number"
            )
            if st.button("Submit"):
                if st.session_state.sheet_url and st.session_state.wave_number:
                    call_extract_reviews(st.session_state.sheet_url, st.session_state.wave_number)
                else:
                    st.warning("Please enter both the Google Sheets URL and the Wave Number.")


    elif nav_choice == "Feedback Analysis":
        # Show Feedback Analysis Section
        if st.session_state.feedback_data:
            st.header("Analysis Results")
            generate_table(st.session_state.feedback_data)
        else:
            st.warning("Please extract reviews first by entering a Google Sheet URL.")

if __name__ == "__main__":
    main()
