import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Define the prompt template
feedback_gen_prompt = """
Using the JSON structure provided below, analyze the feedback from engineers to identify key insights:

1. Summarize the positive aspects of the training program.
2. Highlight areas needing improvement based on suggestions provided.
3. Identify topics where engineers want to deepen their understanding.
4. Recommend actionable steps to enhance the training experience in the future.

JSON Structure:
{
  "engineer_feedback": [Array of feedback comments],
  "program_likings": [Array of liked aspects],
  "topics_learned": [Array of topics learned],
  "program_improvements": [Array of suggested improvements],
  "engineer_improvements": [Array of areas needing better understanding]
}

Feedback Data:
{feedback_data}

The output should be Top 5 positive aspects and Top 5 negative aspects
Explanation should be precise and not more than 1 sentence

Format your response as follows:
TOP 5 POSITIVE ASPECTS:
1. [Aspect]: [Example Quote] - [Explanation]
2. [Aspect]: [Example Quote] - [Explanation]
3. [Aspect]: [Example Quote] - [Explanation]
4. [Aspect]: [Example Quote] - [Explanation]
5. [Aspect]: [Example Quote] - [Explanation]

TOP 5 NEGATIVE ASPECTS:
1. [Aspect]: [Example Quote] - [Explanation]
2. [Aspect]: [Example Quote] - [Explanation]
3. [Aspect]: [Example Quote] - [Explanation]
4. [Aspect]: [Example Quote] - [Explanation]
5. [Aspect]: [Example Quote] - [Explanation]
"""

# Function to read feedback from a JSON file
def read_feedback_from_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_feedback_from_ai():
    json_file_path = '../reviews_data.json'
    # Read the entire feedback data from the JSON file
    feedback_data = read_feedback_from_json(json_file_path)

    # Prepare the full prompt by inserting feedback data into the template using f-string
    full_prompt = f"{feedback_gen_prompt}\nFeedback Data: {json.dumps(feedback_data)}"
    genai.configure(api_key=os.getenv('GEMINI_KEY'))
    model = genai.GenerativeModel("gemini-1.5-flash")
    return  model.generate_content(full_prompt)

