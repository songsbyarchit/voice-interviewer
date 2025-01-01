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

@app.route('/send-to-sheets', methods=['POST'])
def send_to_sheets():
    """Receive transcription from frontend, process it, and append to Google Sheets."""
    try:
        print("Received request at '/send-to-sheets'")  # Log when the route is accessed
        
        # Get the data sent from the frontend (index.html)
        data = request.get_json()  
        transcription = data.get("transcription")

        if not transcription:
            return jsonify({"error": "No transcription provided."}), 400  # Error handling

        # Log the received transcription
        print(f"Received transcription: {transcription}")

        # Parse the transcription using AI
        parsed_data = ai_parse_transcription(transcription)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Format as YYYY-MM-DD HH:MM:SS
        parsed_data.insert(2, timestamp)  # Insert the timestamp at the 3rd column (index 2)

        # Log the parsed data before sending it to Google Sheets
        print(f"Parsed data: {parsed_data}")

        # Append the parsed data to Google Sheets
        append_to_sheet(parsed_data)

        return jsonify({"message": "Data successfully sent to Google Sheets."})
    except Exception as e:
        # If any error occurs, log the error and return a response
        print(f"Error during 'send-to-sheets' request: {e}")
        return jsonify({"error": str(e)}), 500  # Send back the error message

if __name__ == '__main__':
    app.run(debug=True)