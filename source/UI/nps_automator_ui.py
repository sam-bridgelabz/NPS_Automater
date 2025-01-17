import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
from fastapi import HTTPException
import matplotlib.pyplot as plt

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
        "wave_number": "Wave " + wave_number
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
                st.session_state.cleaned_data = result['cleaned_data']
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
    except HTTPException as http_err:
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
    if "cleaned_data" not in st.session_state:
        st.session_state.cleaned_data = None

def generate_table(data):
    st.title("Feedback Analysis")

    # Positive and negative aspects from the cleaned_data
    positive_df = pd.DataFrame(data['positive_aspects'])
    positive_df.rename(columns={'aspect': 'Aspect', 'explanation': 'Explanation'}, inplace=True)

    negative_df = pd.DataFrame(data['improvements_needed'])
    negative_df.rename(columns={'aspect': 'Aspect', 'explanation': 'Explanation'}, inplace=True)

    # Displaying tables
    st.subheader("Positive Aspects")
    st.table(positive_df)

    st.subheader("Improvements Needed Aspects")
    st.table(negative_df)

    # Creating PDF and enabling download
    pdf_file_path = create_pdf(positive_df, negative_df)
    if pdf_file_path:
        st.download_button(
            label="Download Feedback as PDF",
            data=open(pdf_file_path, "rb").read(),
            file_name="Feedback_Analysis.pdf",
            mime="application/pdf",
            on_click=clear_all_data
        )

def create_pdf(positive_df, negative_df):
    try:
        if 'Aspect' not in positive_df.columns or 'Explanation' not in positive_df.columns:
            st.error("Positive aspects data is missing required columns.")
            return None
        if 'Aspect' not in negative_df.columns or 'Explanation' not in negative_df.columns:
            st.error("Negative aspects data is missing required columns.")
            return None

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

def clear_all_data():
    """Clear all session state and input fields after download."""
    st.session_state.sheet_url = ""
    st.session_state.wave_number = ""
    st.session_state.feedback_data = None
    st.session_state.cleaned_data = None
    st.rerun()  # Rerun the app to refresh the page after clearing

# New function: Analyze and Plot
def analyse_data(data):
    # Convert the cleaned_data from JSON to DataFrame
    data_df = pd.DataFrame(data)

    num_respondents = len(data_df)
    st.write(f"### Number of Respondents: {num_respondents}")

    if 'recommendation_score' not in data_df.columns:
        st.error("The dataset does not contain a 'recommendation_score' column.")
        return

    score = data_df['recommendation_score']
    minimal_score = score.min()
    average_score = score.mean()
    st.write(f"### Minimum Score: {minimal_score}")
    st.write(f"### Average Score: {average_score:.2f}")

    plot_score_distribution(data_df)

def plot_score_distribution(data):
    if 'wave_number' not in data.columns or len(data['wave_number'].unique()) > 1:
        st.error("Wave number data is missing or inconsistent.")
        return

    wave_number = data['wave_number'].iloc[0]

    plt.figure(figsize=(8, 4))
    plt.hist(
        data['recommendation_score'],
        bins=10,
        range=(0, 10),
        color='skyblue',
        edgecolor='black',
        alpha=0.7
    )
    plt.title(f'Feedback Score Distribution for Wave {wave_number}', fontsize=16)
    plt.xlabel('Scores (0 to 10)', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.xticks(range(0, 11))
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    st.pyplot(plt)

def calculate_percentage_below_7(data):
    # Filter data by Wave Survey if a specific wave is selected

    wave_data = pd.DataFrame(data)
    wave_number = wave_data['wave_number'].iloc[0]

    # Extract scores using the correct column name
    scores = wave_data['recommendation_score']
    num_respondents = len(scores)

    if num_respondents == 0:
        st.warning("No data available for the selected wave.")
        return

    # Percentage of scores below 7
    below_7 = scores[scores < 7]
    percentage_below_7 = (len(below_7) / num_respondents) * 100

    # Display percentage below 7
    st.write(f"### Percentage of Respondents with Scores Below 7: {percentage_below_7:.2f}%")

    # Pie chart
    labels = ['Below 7', '7 and Above']
    sizes = [len(below_7), num_respondents - len(below_7)]
    colors = ['red', 'green']
    explode = (0.1, 0)  # Explode the below-7 slice

    plt.figure(figsize=(6, 4))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title(f'Feedback Score Distribution for {wave_number}', fontsize=16)

    # Display pie chart in Streamlit
    st.pyplot(plt)

def calculate_nps(data):
    # Convert data to DataFrame
    wave_data = pd.DataFrame(data)

    # Extract scores
    scores = wave_data['recommendation_score']

    # Define categories
    promoters = scores[scores >= 9]
    passives = scores[(scores >= 7) & (scores <= 8)]
    detractors = scores[scores <= 6]
    total_responses = len(scores)

    if total_responses == 0:
        st.warning("No data available for the selected wave.")
        return None

    # Calculate percentages
    promoter_pct = len(promoters) / total_responses * 100
    passive_pct = len(passives) / total_responses * 100
    detractor_pct = len(detractors) / total_responses * 100

    # Calculate NPS
    nps = promoter_pct - detractor_pct

    # Prepare results for the table
    results_df = pd.DataFrame({
        "Metric": ["Total Responses", "Promoters (%)", "Passives (%)", "Detractors (%)", "NPS"],
        "Value": [total_responses, f"{promoter_pct:.2f}%", f"{passive_pct:.2f}%", f"{detractor_pct:.2f}%", f"{nps:.2f}"]
    })

    # Display the results as a table in Streamlit
    st.write("### NPS Calculation Results (Table)")
    st.table(results_df)

    # Visualization: Bar chart for Promoters, Passives, Detractors
    st.write("### NPS Category Distribution")
    categories = ['Promoters', 'Passives', 'Detractors']
    percentages = [promoter_pct, passive_pct, detractor_pct]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(categories, percentages, color=['green', 'yellow', 'red'])
    ax.set_xlabel('Categories')
    ax.set_ylabel('Percentage (%)')
    ax.set_title('Distribution of NPS Categories')
    st.pyplot(fig)

    # Visualization: Pie chart for NPS category distribution
    st.write("### NPS Category Proportion (Pie Chart)")
    labels = ['Promoters', 'Passives', 'Detractors']
    sizes = [len(promoters), len(passives), len(detractors)]
    colors = ['green', 'yellow', 'red']
    explode = (0.1, 0, 0)  # Explode the Promoter slice

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    ax.set_title('Proportion of NPS Categories')
    st.pyplot(fig)

    # Return the DataFrame for further use if needed
    return results_df


def main():
    setup_page()
    initialize_session_state()

    st.sidebar.title("Actions")

    # The "Feedback Analysis" tab will handle both review extraction and analysis
    st.subheader("Google Sheet URL")
    sheet_url = st.text_input(
        "Enter the URL of your Google Sheet",
        value=st.session_state.sheet_url,
        key="sheet_url"
    )
    st.subheader("Wave Number")
    wave_number = st.text_input(
        "Enter the Wave Number",
        value=st.session_state.wave_number,
        key="wave_number"
    )

    if st.button("Extract Reviews and Analyze"):
        if sheet_url and wave_number:
            call_extract_reviews(sheet_url, wave_number)
        else:
            st.warning("Please enter both the Google Sheets URL and the Wave Number.")

    if st.session_state.feedback_data is not None:
        st.header("Analysis Results")
        analyse_data(st.session_state.cleaned_data) # Pass cleaned_data here
        calculate_percentage_below_7(st.session_state.cleaned_data)
        calculate_nps(st.session_state.cleaned_data)
        generate_table(st.session_state.feedback_data)
    else:
        st.warning("Please extract reviews first by entering a Google Sheet URL.")

if __name__ == "__main__":
    main()
