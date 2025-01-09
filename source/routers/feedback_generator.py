from fastapi import FastAPI, HTTPException, Query, APIRouter
from pydantic import BaseModel
import google.generativeai as genai
from typing import Dict, Any
from collections import Counter
from dotenv import load_dotenv
import os
import json

# Load the .env file
load_dotenv()

# Define the router
feedback_gen_router = APIRouter(
    prefix="/gen_feedback",
    tags=["Generate Feedback"]
)

 # Configure Gemini
api_key = os.getenv('GEMINI_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-pro")



# Analyze feedback logic
def analyze_feedback() -> Dict[str, Any]:
    """
    Analyze feedback based on the extracted reviews data.
    """
    try:
        with open('reviews_data.json','r') as r_file:
            data = json.load(r_file)
        
        # Example Analysis 1: Sentiment Analysis
        def analyze_sentiment(feedback_list):
            positive = sum(1 for feedback in feedback_list if "good" in feedback.lower() or "excellent" in feedback.lower())
            negative = sum(1 for feedback in feedback_list if "bad" in feedback.lower() or "poor" in feedback.lower())
            neutral = len(feedback_list) - positive - negative
            return {"positive": positive, "negative": negative, "neutral": neutral}

        # Example Analysis 2: Topic Frequency
        def count_topics(topics_list):
            all_topics = [topic.lower() for sublist in topics_list for topic in sublist.split(",")]
            return dict(Counter(all_topics))

        # Example Analysis 3: Extract Improvement Suggestions
        def extract_improvements(improvement_list):
            return {
                "most_common": dict(Counter(improvement_list)),
                "total_suggestions": len(improvement_list)
            }

        # Perform analysis on the extracted data
        engineer_feedback = data.get("engineer_feedback", [])
        program_likings = data.get("program_likings", [])
        topics_learned = data.get("topics_learned", [])
        program_improvements = data.get("program_improvements", [])
        engineer_improvements = data.get("engineer_improvements", [])

        sentiment_results = analyze_sentiment(engineer_feedback)
        topic_frequencies = count_topics(topics_learned)

        program_improvements_summary = extract_improvements(program_improvements)
        engineer_improvements_summary = extract_improvements(engineer_improvements)

        # Example Analysis 4: Most Common Program Liking
        program_liking_counts = dict(Counter(program_likings))
        most_liked_aspect = max(program_liking_counts, key=program_liking_counts.get) if program_liking_counts else "N/A"

        # Structure analysis results
        analysis_results = {
            "sentiment_analysis": sentiment_results,
            "topic_frequencies": topic_frequencies,
            "most_liked_aspect": most_liked_aspect,
            "program_improvements": program_improvements_summary,
            "engineer_improvements": engineer_improvements_summary
        }

        return analysis_results

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# FastAPI route to perform feedback analysis
@feedback_gen_router.get("/analyze-feedback", summary="Analyze feedback from extracted data")
def analyze_feedback_endpoint():
    """
    Endpoint to analyze feedback and return insights.
    """
    return analyze_feedback()
