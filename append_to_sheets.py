import json
import openai
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Your Google Sheet ID
SHEET_ID = "1U8nbGQ0G8IWEH3uuCearT3c39SNiHGuZGXfxI7TwrZQ"

# Path to your service account JSON key
SERVICE_ACCOUNT_FILE = "/Users/arsachde/Downloads/voice-interviewer-e2d008ff6856.json"

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

def append_to_sheet(data):
    print(f"Data being sent: {data}")  # Debug: Print the data being sent

    # Authenticate with the Google Sheets API
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=credentials)

    # Append data to the sheet
    body = {"values": [data]}
    result = service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="Sheet1",  # Use only the sheet name
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",  # Always append new rows
        body=body
    ).execute()

    # Print the full response to debug
    print(f"Response: {result}")

def ai_parse_transcription(transcription):
    # Use AI to dynamically parse the transcription
    prompt = f"""
    Extract the following details from the transcription:
    1. Physical Win (any achievement related to fitness or physical activities).
    2. Social Highlight (any notable social event, interaction, or highlight).

    Return the result as a JSON object with keys 'Physical Win' and 'Social Highlight'. 
    Please do not format the response with any code blocks or markdown; just provide the JSON object.

    Transcription: "{transcription}"
    """

    # Make the request to OpenAI
    try:
        response = openai.ChatCompletion.create(  # Correct method to call
            model="gpt-3.5-turbo",  # Use a suitable GPT model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Log the full response for debugging
        print("Full AI Response:", response)

        # Extract the result from the response
        result = json.loads(response['choices'][0]['message']['content'].strip())
        return [result.get("Physical Win", ""), result.get("Social Highlight", "")]

    except Exception as e:
        # If parsing or any other error occurs, print the error message and the full response
        print(f"Error while parsing AI response: {e}")
        print("Full AI Response:", response)  # Log the full response for further analysis
        return ["", ""]  # Fallback to empty data

transcriptions = [
    "My physical victory was breaking my personal record in deadlifts, while my social highlight was attending an inspirational TED talk.",
    "Completed my first triathlon today, and I had an insightful meeting with a mentor in my field.",
    "Achieved my physical goal of swimming 3 miles today, and socially, I attended a conference on sustainability.",
    "I ran my first marathon, and my social highlight was participating in a charity fundraising event.",
    "Successfully hit my 100 push-up goal, and I caught up with old friends at a reunion event.",
    "I achieved a physical milestone by completing a half marathon, and socially, I joined a cooking class with colleagues.",
    "Successfully lifted my heaviest squat to date, and spent the evening enjoying a cultural performance with my family.",
    "Hit a new PR in the bench press today, and I spent quality time volunteering at a local shelter.",
    "I completed a grueling 10-mile run and spent time with my coworkers at a team-building event afterward.",
    "I completed my first advanced yoga challenge, and I spent an afternoon bonding with friends at a local park."
]

for transcription in transcriptions:
    print(f"Testing transcription: {transcription}")
    data = ai_parse_transcription(transcription)  # Use AI to parse the transcription
    print(f"Parsed data: {data}")  # Print the parsed result
    append_to_sheet(data)  # Append it to the sheet
    print("-" * 50)  # Separator for readability