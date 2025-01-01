import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from openai import OpenAI

# Your Google Sheet ID
SHEET_ID = "1U8nbGQ0G8IWEH3uuCearT3c39SNiHGuZGXfxI7TwrZQ"

# Path to your service account JSON key
SERVICE_ACCOUNT_FILE = "/Users/arsachde/Downloads/voice-interviewer-e2d008ff6856.json"

# OpenAI API Key
OPENAI_API_KEY = "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"  # Replace with your actual API key

client = OpenAI(api_key=OPENAI_API_KEY)

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
    Transcription: "{transcription}"
    """
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ])
    try:
        result = json.loads(response.choices[0].message.content.strip())
        return [result.get("Physical Win", ""), result.get("Social Highlight", "")]
    except json.JSONDecodeError:
        print("Failed to parse AI response.")
        return ["", ""]  # Fallback to empty data

# Example transcriptions
transcriptions = [
    "My physical achievement today was running my fastest 5K, and my social highlight was having a great dinner with friends.",
    "My physical win was completing a marathon this morning, and my social highlight was catching up with my childhood friend afterward.",
    "I reached a physical milestone with a new deadlift record at the gym, and my social moment was attending a business networking event.",
    "My physical achievement was swimming 2 kilometers without stopping, and my social highlight was enjoying a fun evening at a birthday party.",
    "I had a physical win by finishing a tough hike up the mountain, and my social moment was spending the afternoon with my family.",
    "My physical goal was hitting a new personal best in squats, and my social moment was having coffee with my colleague.",
    "I achieved my physical goal of completing 100 push-ups, and my social highlight was meeting up with old friends for lunch.",
    "My physical milestone was crossing off my 10K running goal today, and my social highlight was volunteering at the community center.",
    "I achieved a physical feat by biking 50 miles today, and my social highlight was hosting a virtual meeting with my professional network.",
    "My physical win was completing my first yoga class, and my social highlight was spending a lovely afternoon with my mentor."
]

for transcription in transcriptions:
    print(f"Testing transcription: {transcription}")
    data = ai_parse_transcription(transcription)  # Use AI to parse the transcription
    print(f"Parsed data: {data}")  # Print the parsed result
    append_to_sheet(data)  # Append it to the sheet
    print("-" * 50)  # Separator for readability