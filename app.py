import os
import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import httpx
from typing import Optional, Literal
from datetime import datetime

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
BASE_URL = "https://api.groq.com/openai/v1"

app = Flask(__name__)
CORS(app)

ResponseFormat = Literal["json", "verbose_json", "text"]
TimestampFormat = Literal["word", "segment"]

def process_audio(
    audio_content: bytes,
    api_key: str,
    model: str,
    response_format: ResponseFormat = "text",
    language: Optional[str] = None,
    translate: bool = False,
    timestamp_granularities: TimestampFormat = "segment",
) -> str:

    endpoint = "translations" if translate else "transcriptions"
    url = f"{BASE_URL}/audio/{endpoint}"
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    audio_file = io.BytesIO(audio_content)
    audio_file.name = "audio.mp3"  # Must have a valid audio extension

    files = {"file": audio_file}
    data = {
        "model": model,
        "response_format": response_format,
        # "timestamp_granularities": timestamp_granularities
    }

    if language:
        data["language"] = language

    with httpx.Client(verify=False) as client:
        response = client.post(url, headers=headers, files=files, data=data, timeout=None)
        response.raise_for_status()

        if response_format == "text":
            return response.text.strip()
        return response.json()


@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Read audio content as bytes
    audio_content = file.read()
    filename = file.filename  # Save original file name
    now = datetime.now()

    # Get optional language parameter
    language = request.form.get("lang")

    # Transcribe using the Groq API
    result = process_audio(
        audio_content=audio_content,
        api_key=GROQ_API_KEY,
        model='whisper-large-v3',
        response_format='verbose_json',
        language=language,
        translate=False,
        timestamp_granularities='segment',
    )

    current_date_time = now.strftime("%b %d, %Y, %I:%M %p")

    # Encode audio to Base64 (for demonstration only)
    audio_base64 = base64.b64encode(audio_content).decode('utf-8')

    # Return JSON with filename, base64 audio, and transcription
    return jsonify({
        "filename": filename,
        "audio_data": audio_base64,
        "segments": result['segments'],
        "dateTime": current_date_time
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)