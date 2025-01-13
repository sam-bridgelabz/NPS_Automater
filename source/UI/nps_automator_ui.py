import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests

def setup_page():
    st.set_page_config(
        page_title="NPS Automator",
        page_icon="📊",
        layout="wide"
    )
    st.title("NPS Automator")

def call_extract_reviews(spreadsheet_name):
    params = {
        "spreadsheet_url": spreadsheet_name
    }

    try:
        fastapi_url = "http://localhost:8000/extract-reviews"
        response = requests.get(fastapi_url, params=params)

        if response.status_code == 200:
            result = response.json()
            print("\n\nresult--->",result,"\n\n")
            st.success("Reviews successfully extracted and saved.")
            generate_table(result['payload']['feedback_generated'])
            # generate_table(result)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def initialize_session_state():
    if "sheet_url" not in st.session_state:
        st.session_state.sheet_url = ""
    if "feedback_data" not in st.session_state:
        st.session_state.feedback_data = None

def generate_table(data):
    st.title("Feedback Analysis")

    st.subheader("Positive Aspects")
    positive_df = pd.DataFrame(data['positive_aspects'])
    st.table(positive_df)

    st.subheader("Improvements Needed Aspects")
    negative_df = pd.DataFrame(data['improvements_needed'])
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
        # Print the columns of the DataFrames to check if 'Aspect' exists
        print("Positive DF Columns:", positive_df.columns)
        print("Negative DF Columns:", negative_df.columns)

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
        pdf.cell(200, 10, txt="Negative Aspects", ln=True, align="L")
        pdf.set_font("Arial", size=12)
        for index, row in negative_df.iterrows():
            pdf.multi_cell(0, 10, txt=f"{row['Aspect']}: {row['Explanation']}")

        pdf_file_path = "feedback_analysis.pdf"
        try:
            pdf.output(pdf_file_path)
            print("PDF saved successfully!")
        except Exception as e:
            print(f"Error saving PDF: {e}")

        return pdf_file_path
    except Exception as e:
        st.error(f"An error occurred while generating the PDF: {e}")
        return None


def clear_input_field():
    """Clear the input field after the file is downloaded."""
    st.session_state.sheet_url = ""  # Clear the URL input field

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
            if st.button("Submit"):
                if st.session_state.sheet_url:
                    call_extract_reviews(st.session_state.sheet_url)
                else:
                    st.warning("Please enter a valid Google Sheets URL.")

    elif nav_choice == "Feedback Analysis":
        # Show Feedback Analysis Section
        if st.session_state.feedback_data:
            st.header("Analysis Results")
            generate_table(st.session_state.feedback_data)
        else:
            st.warning("Please extract reviews first by entering a Google Sheet URL.")

if __name__ == "__main__":
    main()

