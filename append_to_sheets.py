import json
import openai
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import sys
from datetime import datetime

# Ensure that the virtual environment is activated
def install_requirements():
    if not os.path.exists("requirements.txt"):
        print("No requirements.txt found!")
        return
    
    # Run pip install -r requirements.txt
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# Install requirements when the app is run
install_requirements()

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

CORS(app)

# Google Sheet and OpenAI API configuration
SHEET_ID = os.getenv("SHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def append_to_sheet(data):
    """Append data to Google Sheets."""
    print(f"Data being sent: {data}")  # Debug: Print the data being sent

    try:
        # Authenticate with Google Sheets API
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=credentials)

        # Append data to the sheet
        body = {"values": [data]}
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="Sheet1",  # Sheet name, update if necessary
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",  # Always append new rows
            body=body
        ).execute()

        # Log the response from Google Sheets
        print(f"Response from Google Sheets: {result}")
    except Exception as e:
        print(f"Error during append to Google Sheets: {e}")
        raise e

def ai_parse_transcription(transcription):
    """Use OpenAI to extract physical and social highlights."""
    prompt = f"""
    Extract the following details from the transcription:
    1. Physical Win (any achievement related to fitness or physical activities).
    2. Social Highlight (any notable social event, interaction, or highlight).
    
    Return the result as a JSON object with keys 'Physical Win' and 'Social Highlight'. 
    Please do not format the response with any code blocks or markdown; just provide the JSON object.

    Transcription: "{transcription}"
    """

    # Make the request to OpenAI API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the suitable GPT model
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

@app.route('/')
def home():
    # Return the OpenAI API key to the frontend
    return render_template('index.html', openai_api_key=OPENAI_API_KEY)

temporary_data = {}

@app.route('/send-to-sheets', methods=['POST'])
def send_to_sheets():
    try:
        print("Received request at '/send-to-sheets'")
        
        # Get the data sent from the frontend
        data = request.get_json()
        physical_achievement = data.get("physical_achievement", "").strip()
        social_win = data.get("social_win", "").strip()
        user_session_id = data.get("session_id", "default")

        # Add a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Store session data
        if user_session_id not in temporary_data:
            temporary_data[user_session_id] = {
                "physical_achievement": "",
                "social_win": "",
                "timestamp": datetime.now(),
            }

        # Update session data with provided input
        if physical_achievement:
            temporary_data[user_session_id]["physical_achievement"] = physical_achievement
        if social_win:
            temporary_data[user_session_id]["social_win"] = social_win

        # Check if at least one value is provided
        final_data = [
            temporary_data[user_session_id]["physical_achievement"],
            temporary_data[user_session_id]["social_win"],
        ]

        if not final_data[0] and not final_data[1]:
            return jsonify({
                "message": "No data provided. At least one achievement is required to proceed.",
                "missing": "both",
                "complete": False,
            }), 200

        # If user skips, append available data to Google Sheets
        append_to_sheet([final_data[0] or "N/A", final_data[1] or "N/A", timestamp])
        del temporary_data[user_session_id]

        return jsonify({"message": "Achievements added successfully (skipped fields marked as N/A).", "complete": True}), 200

    except Exception as e:
        print(f"Error during 'send-to-sheets' request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)