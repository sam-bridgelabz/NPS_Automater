from fastapi import FastAPI
from routers.extract_reviews import review_router
import os
import subprocess
import time
import requests
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

app = FastAPI(
    title="Review Extraction API",
    description="An API to extract reviews from Google Sheets and process them.",
    version="1.0.0"
)

# Include the router
app.include_router(review_router)


def start_streamlit():
    """Start Streamlit UI in a new terminal."""
    script_path = os.path.abspath("UI/nps_automator_ui.py")  # Adjust path if needed
    subprocess.Popen(f'start cmd /k streamlit run "{script_path}" --server.port 8501', shell=True)


def start_fastapi():
    """Start FastAPI server in a new terminal."""
    subprocess.Popen('start cmd /k uvicorn main:app --host 127.0.0.1 --port 8000 --reload', shell=True)


def wait_for_fastapi():
    """Wait until FastAPI is fully running before starting Streamlit."""
    url = f"{os.getenv('MAIN_URL')}/docs"
    for _ in range(10):  # Retry for ~10 seconds
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("FastAPI is running!")
                return True
        except requests.ConnectionError:
            print("Waiting for FastAPI to start...")
            time.sleep(1)
    print("FastAPI failed to start.")
    return False


if __name__ == "__main__":
    start_fastapi()
    if wait_for_fastapi():
        start_streamlit()
