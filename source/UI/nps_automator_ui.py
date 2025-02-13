import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from fpdf import FPDF
import requests
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()


def setup_page():
    st.set_page_config(
        page_title="NPS Automator",
        page_icon="📊",
        layout="wide"
    )
    st.title("NPS Automator")

def initialize_session_state():
    if "sheet_url" not in st.session_state:
        st.session_state.sheet_url = ""
    if "wave_number" not in st.session_state:
        st.session_state.wave_number = ""
    if "feedback_data" not in st.session_state:
        st.session_state.feedback_data = None
    if "cleaned_data" not in st.session_state:
        st.session_state.cleaned_data = None
    if "sheet_title" not in st.session_state:
        st.session_state.sheet_title = None
    if "wave_number" not in st.session_state:
        st.session_state.wave_number = None
    if "summary_df" not in st.session_state:
        st.session_state.summary_df = None
    if "nps_results_df" not in st.session_state:
        st.session_state.nps_results_df = None

def call_extract_reviews(spreadsheet_url, wave_number):
    params = {
        "spreadsheet_url": spreadsheet_url,
        "wave_number": "Wave " + wave_number
    }

    try:
        with st.spinner("Trying to fetch data..."):
            fastapi_url = f"{os.getenv('MAIN_URL')}/extract-reviews"
            response = requests.get(fastapi_url, params=params)

            if response.status_code == 200:
                result = response.json()
                st.success("Reviews successfully extracted. Now generating table from it...")
                st.session_state.feedback_data = result['payload']['feedback_generated']
                st.session_state.cleaned_data = result['cleaned_data']
                st.session_state.sheet_title = result['sheet_title']
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def generate_table(data,sheet_title, wave_number):
    # Positive and negative aspects from the cleaned_data
    positive_df = pd.DataFrame(data['positive_aspects'])
    positive_df.rename(columns={'aspect': 'Aspect', 'explanation': 'Explanation'}, inplace=True)

    negative_df = pd.DataFrame(data['improvements_needed'])
    negative_df.rename(columns={'aspect': 'Aspect', 'explanation': 'Explanation'}, inplace=True)

    # Displaying tables
    st.subheader("Positive Aspects")
    positive_df.index = range(1, len(positive_df) + 1)
    st.table(positive_df)

    st.subheader("Improvements Needed Aspects")
    negative_df.index = range(1, len(negative_df) + 1)
    st.table(negative_df)

    # Creating PDF and enabling download
    pdf_file_path = create_pdf(positive_df, negative_df,sheet_title, wave_number)
    if pdf_file_path:
        st.download_button(
            label="Download Feedback as PDF",
            data=open(pdf_file_path, "rb").read(),
            file_name=f"{sheet_title}-Wave-{wave_number}.pdf",
            mime="application/pdf",
        )

def create_pdf(positive_df, negative_df, sheet_title, wave_number):
    try:
        # Check if the dataframes contain the required columns
        if 'Aspect' not in positive_df.columns or 'Explanation' not in positive_df.columns:
            st.error("Positive aspects data is missing required columns.")
            return None
        if 'Aspect' not in negative_df.columns or 'Explanation' not in negative_df.columns:
            st.error("Negative aspects data is missing required columns.")
            return None

        # Create a PDF object
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"Feedback Analysis for {sheet_title}", ln=True, align="C")
        pdf.cell(200, 10, f"Wave Number: {wave_number}", ln=True, align="C")
        pdf.ln(10)  # Line break after title
        pdf.set_font("Arial", "B", 16)

        # Positive aspects
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt="Positive Aspects", ln=True, align="L")
        pdf.set_font("Arial", size=12)
        for index, row in positive_df.iterrows():
            pdf.multi_cell(0, 10, txt=f"{row['Aspect']}: {row['Explanation']}")

        pdf.ln(10)

        # Negative aspects
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt="Improvements Needed Aspects", ln=True, align="L")
        pdf.set_font("Arial", size=12)
        for index, row in negative_df.iterrows():
            pdf.multi_cell(0, 10, txt=f"{row['Aspect']}: {row['Explanation']}")

        # Save the PDF
        pdf_file_path = "feedback_analysis.pdf"
        pdf.output(pdf_file_path)
        return pdf_file_path
    except Exception as e:
        st.error(f"An error occurred while generating the PDF: {e}")
        return None

def analyse_data(data):
    # Convert the cleaned_data from JSON to DataFrame
    data_df = pd.DataFrame(data)
    num_respondents = len(data_df)

    if 'recommendation_score' not in data_df.columns:
        st.error("The dataset does not contain a 'recommendation_score' column.")
        return

    score = data_df['recommendation_score']
    minimal_score = score.min()
    average_score = score.mean()

    # Create a summary DataFrame
    summary_df = pd.DataFrame({
        "Metric": ["Number of Respondents", "Minimum Score", "Average Score"],
        "Value": [num_respondents, minimal_score, f"{average_score:.2f}"]
    })

    # Set the index to start from 1
    summary_df.index = range(1, len(summary_df) + 1)
    st.session_state.summary_df = summary_df

    # Display the summary table
    st.write("### Analysis Overview")
    st.table(summary_df)

    plot_score_distribution(data_df)
    calculate_percentage_below_7(data_df)
    calculate_nps(data_df)


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

    # Save plot as PNG in the 'charts' folder
    if not os.path.exists("charts"):
        os.makedirs("charts")  # Create the folder if it doesn't exist

    plot_filename = f"charts/score_distribution_wave_{wave_number}.png"
    plt.savefig(plot_filename, bbox_inches='tight')

    st.pyplot(plt)

def calculate_percentage_below_7(data):
    scores = data['recommendation_score']
    num_respondents = len(scores)

    if num_respondents == 0:
        st.warning("No data available for the selected wave.")
        return

    below_7 = scores[scores < 7]
    percentage_below_7 = (len(below_7) / num_respondents) * 100

    st.write(f"### Percentage of Respondents with Scores Below 7: {percentage_below_7:.2f}%")

    labels = ['Below 7', '7 and Above']
    sizes = [len(below_7), num_respondents - len(below_7)]
    colors = ['red', 'green']
    explode = (0.1, 0)

    plt.figure(figsize=(6, 4))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=100)
    plt.title('Percentage of Respondents with Scores Below 7', fontsize=16)

     # Save plot as PNG in the 'charts' folder
    if not os.path.exists("charts"):
        os.makedirs("charts")  # Create the folder if it doesn't exist

    plot_filename = f"charts/score_chart_wave_{st.session_state.wave_number}.png"
    plt.savefig(plot_filename, bbox_inches='tight')

    st.pyplot(plt)

def calculate_nps(data):
    scores = data['recommendation_score']

    promoters = scores[scores >= 9]
    passives = scores[(scores >= 7) & (scores <= 8)]
    detractors = scores[scores <= 6]
    total_responses = len(scores)

    if total_responses == 0:
        st.warning("No data available for the selected wave.")
        return None

    promoter_pct = len(promoters) / total_responses * 100
    passive_pct = len(passives) / total_responses * 100
    detractor_pct = len(detractors) / total_responses * 100
    nps = promoter_pct - detractor_pct

    results_df = pd.DataFrame({
        "Metric": ["Total Responses", "Promoters (%)", "Passives (%)", "Detractors (%)", "NPS"],
        "Value": [total_responses, f"{promoter_pct:.2f}%", f"{passive_pct:.2f}%", f"{detractor_pct:.2f}%", f"{nps:.2f}"]
    })

    st.write("### NPS Calculation Results")
    results_df.index = range(1, len(results_df) + 1)
    st.session_state.nps_results_df = results_df
    st.table(results_df)

    categories = ['Promoters', 'Passives', 'Detractors']
    percentages = [promoter_pct, passive_pct, detractor_pct]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(categories, percentages, color=['green', 'yellow', 'red'])
    ax.set_xlabel('Categories')
    ax.set_ylabel('Percentage (%)')
    ax.set_title('Distribution of NPS Categories')
    st.pyplot(fig)

    labels = ['Promoters', 'Passives', 'Detractors']
    sizes = [len(promoters), len(passives), len(detractors)]
    colors = ['green', 'yellow', 'red']
    explode = (0, 0, 0)

    fig, ax = plt.subplots(figsize=(4, 2))
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=80)
    # Set font size for the labels and the percentages
    for text in texts:
        text.set_fontsize(6)  # Decrease label font size

    for autotext in autotexts:
        autotext.set_fontsize(4)
    ax.set_title('Proportion of NPS Categories')
    st.pyplot(fig)
    # Creating PDF and enabling download
    pdf_file_path = create_result_pdf()
    if pdf_file_path:
        st.download_button(
            label="Download Results as PDF",
            data=open(pdf_file_path, "rb").read(),
            file_name=f"{st.session_state.sheet_title}-wave{st.session_state.wave_number}-results.pdf",
            mime="application/pdf",
        )

def create_result_pdf():
    try:
        # Create a PDF object
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"Feedback Result for {st.session_state.sheet_title}", ln=True, align="C")
        pdf.cell(200, 10, f"Wave Number: {st.session_state.wave_number}", ln=True, align="C")
        pdf.ln(10)  # Line break after title

        # Analysis Overview Section
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Analysis Overview", ln=True, align="L")
        pdf.set_font("Arial", size=12)
        if 'nps_results_df' in st.session_state:
            for index, row in st.session_state.nps_results_df.iterrows():
                pdf.multi_cell(0, 10, txt=f"{row['Metric']}: {row['Value']}")
        pdf.ln(10)  # Add space after the analysis overview

        # Add NPS Feedback Score Distribution Chart (if available)
        nps_chart_path = f"charts/score_distribution_wave_Wave {st.session_state.wave_number}.png"
        if os.path.exists(nps_chart_path):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, "NPS Feedback Score Distribution", ln=True, align="L")
            pdf.image(nps_chart_path, x=10, y=pdf.get_y(), w=180)
            pdf.ln(10)  # Add space after the NPS chart

        pdf.ln(100)

        # NPS Calculation Results Section
        pdf.ln(50)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "NPS Calculation Results", ln=True, align="L")
        pdf.set_font("Arial", size=12)
        if 'nps_results_df' in st.session_state:
            for index, row in st.session_state.nps_results_df.iterrows():
                pdf.multi_cell(0, 10, txt=f"{row['Metric']}: {row['Value']}")
        pdf.ln(10)  # Add space after NPS results section
        # Add Feedback Score Distribution Chart (if available)
        pdf.ln(10)
        chart_path = f"charts/score_chart_wave_{st.session_state.wave_number}.png"
        if os.path.exists(chart_path):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, "Feedback Score Distribution", ln=True, align="L")
            pdf.image(chart_path, x=10, y=pdf.get_y(), w=180)
            pdf.ln(10)  # Add space after the chart

        # Final spacing before saving the PDF
        pdf.ln(10)

        # Save the PDF
        pdf_file_path = "feedback_result.pdf"
        pdf.output(pdf_file_path)
        return pdf_file_path
    except Exception as e:
        st.error(f"An error occurred while generating the PDF: {e}")
        return None


def clear_all_data():
    """Clear all session state and input fields after download."""
    st.session_state.clear()  # This clears all session state variables
    st.rerun()

def main():
    setup_page()
    initialize_session_state()

        # Sidebar with Logo
    st.sidebar.image(
    "https://media.licdn.com/dms/image/v2/C510BAQEYyeT3P0H_mw/company-logo_200_200/company-logo_200_200/0/1630611149363/bridgelabz_com_logo?e=2147483647&v=beta&t=TFgRiaA55f57NqQFnUbnsKu3mQo7c-LOfD8_iNSgtNM",
    width=100)

    st.sidebar.title("Please fill the details")
    sheet_url = st.sidebar.text_input("Google Sheets URL", value=st.session_state.sheet_url, key="sheet_url")
    wave_number = st.sidebar.text_input("Wave Number", value=st.session_state.wave_number, key="wave_number")

    if st.sidebar.button("Extract Reviews and Analyze"):
        if sheet_url and wave_number:
            call_extract_reviews(sheet_url, wave_number)
        else:
            st.sidebar.warning("Please enter both Google Sheets URL and Wave Number.")

    # Reset button
    if st.sidebar.button("Reset"):
        clear_all_data()

    if st.session_state.feedback_data is not None:
        selected_tab = option_menu(
            menu_title="",
            options=["Feedback Analysis", "Analysis Results"],
            icons=["table", "bar-chart-line"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0", "background-color": "#000000"},
                "nav-link": {"margin": "0px", "padding": "10px"},
                "nav-link-selected": {"background-color": "#636efa"},
            },
        )

        if selected_tab == "Feedback Analysis":
            st.header("Feedback Analysis")
            generate_table(st.session_state.feedback_data,st.session_state.sheet_title,st.session_state.wave_number)
        elif selected_tab == "Analysis Results":
            st.header("Analysis Results")
            analyse_data(st.session_state.cleaned_data)
    else:
        st.warning("Please extract reviews first by entering a Google Sheet URL.")

if __name__ == "__main__":
    main()
