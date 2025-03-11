import os
import io
import base64
import httpx
import tempfile
import time
from datetime import datetime
from flask import request, jsonify, send_file, after_this_request
from utils.download_best import Download

# Load environment variables
GROQ_API_KEY = "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"
BASE_URL = "https://api.groq.com/openai/v1"

class Transcriber:
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = BASE_URL

    def process_audio(self, audio_content: bytes, model: str, language: str = None):
        """Sends audio content to Groq API for transcription."""
        try:
            endpoint = "transcriptions"
            url = f"{self.base_url}/audio/{endpoint}"

            headers = {"Authorization": f"Bearer {self.api_key}"}

            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_content)
            audio_file.name = "audio.mp3"  # Set a valid file name
            
            files = {"file": audio_file}
            data = {
                "model": model,
                "response_format": "verbose_json",
            }
            if language:
                data["language"] = language

            # Send request to API
            with httpx.Client(verify=False) as client:
                response = client.post(url, headers=headers, files=files, data=data, timeout=30)
                response.raise_for_status()  # Raise error for bad responses
                
                return response.json()
        except Exception as e:
            return {"error": f"Transcription failed: {str(e)}"}
    
    def import_file(self):
        try:
            file_url = request.json.get('file_url')
            if not file_url:
                return jsonify({"error": "No file URL provided"}), 400

            download_instance = Download()
            downloaded_file = download_instance.download_from_url(file_url)

            if not downloaded_file or not os.path.exists(downloaded_file):
                return jsonify({"error": "Failed to import the file"}), 500

            # Make sure file is fully closed before deletion
            response = send_file(downloaded_file, as_attachment=True)

            # @after_this_request
            # def remove_file(response):
            #     try:
            #         if os.path.exists(downloaded_file):
            #             os.remove(downloaded_file)
            #             print(f"Deleted file: {downloaded_file}")
            #     except Exception as e:
            #         print(f"Error deleting file: {e}")
            #     return response

            return response  # Send the file

        except Exception as e:
            return jsonify({"error": f"Failed to import file: {str(e)}"}), 500

    def transcribe_audio(self, request):
        """Handles transcription API endpoint."""
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        try:
            # Read file content
            audio_content = file.read()
            filename = file.filename
            now = datetime.now()

            # Get optional language parameter
            language = request.form.get("lang")

            # Process audio file
            result = self.process_audio(
                audio_content=audio_content,
                model='whisper-large-v3',
                language=language
            )

            if "error" in result:
                return jsonify(result), 500

            # Convert audio to Base64 (for frontend display)
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')

            return jsonify({
                "filename": filename,
                "audio_data": audio_base64,
                "segments": result.get("segments", []),
                "dateTime": now.strftime("%b %d, %Y, %I:%M %p")
            })

        except Exception as e:
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
