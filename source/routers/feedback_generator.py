import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import re

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
the above output should be in json format with structure {"positive_aspects":[],"improvements_needed":[]}
"""

# Function to read feedback from a JSON file
def read_feedback_from_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_data_between_braces(json_string):
    """
    Extracts the data between curly braces `{}` from a JSON string or text.

    Args:
        json_string (str): The input JSON string or text.

    Returns:
        dict: Parsed data between curly braces as a Python dictionary.
    """
    try:
        # Use regex to extract the content between the outermost curly braces
        match = re.search(r'\{.*\}', json_string, re.DOTALL)
        if match:
            data = match.group(0)
            # Parse the JSON string into a dictionary
            return json.loads(data)
        else:
            raise ValueError("No data found between curly braces.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON: {e}")


def generate_feedback_from_ai():
    json_file_path = '../reviews_data.json'
    # Read the entire feedback data from the JSON file
    feedback_data = read_feedback_from_json(json_file_path)
    # print(feedback_data)
    # Prepare the full prompt by inserting feedback data into the template using f-string
    full_prompt = f"{feedback_gen_prompt}\nFeedback Data: {json.dumps(feedback_data)}"
    print("os.getenv('GEMINI_KEY')",os.getenv('GEMINI_KEY'))
    genai.configure(api_key=os.getenv('GEMINI_KEY'))
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(full_prompt).text
    return extract_data_between_braces(response) # Return the response

