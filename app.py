import os
import time
import requests
from flask import Flask, request, render_template, redirect, flash
from werkzeug.utils import secure_filename
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'ZureilTranScript'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.template_filter('mmss')
def format_mmss(seconds):
    """Convert seconds to mm:ss format."""
    return str(timedelta(seconds=seconds))[:-3]

def upload_file_to_bunny(file, filename):

    """
    Uploads the file to Bunny CDN Storage using the Bunny File API.
    Returns a publicly accessible URL.
    """

    STORAGE_ZONE = "israel01"
    upload_url = f"https://storage.bunnycdn.com/{STORAGE_ZONE}/{filename}"
    headers = {
        "AccessKey": "0fef67b2-4255-4299-a07a57722d9f-7c84-4c61"
    }

    file.seek(0)
    response = requests.put(upload_url, headers=headers, data=file)

    if response.status_code in (200, 201):
        public_url = f"https://{STORAGE_ZONE}.b-cdn.net/{filename}"
        return public_url
    else:
        print("Error uploading to Bunny:", response.status_code, response.text)
        return None


def poll_transcription(job_id, headers, timeout=60, interval=5):
    """
    Poll the Salad API GET endpoint until the job status is "succeeded" or a timeout occurs.
    """
    job_url = f"https://api.salad.com/api/public/organizations/maariv/inference-endpoints/transcribe/jobs/{job_id}"
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(job_url, headers=headers)
        print("Poll transcription >>>>>>>", response.json())
        if response.status_code == 200:
            job_data = response.json()
            if job_data.get("status") == "succeeded":
                return job_data
            elif job_data.get("status") == "failed":
                print("Transcription job failed.")
                return None
        time.sleep(interval)

    print("Polling timed out.")
    return None


def transcribe_audio(file_url, file_name, speaker=None):
    """
    Post a transcription job to Salad using the provided file URL and poll for the completed transcript.
    """

    API_ENDPOINT = "https://api.salad.com/api/public/organizations/maariv/inference-endpoints/transcribe/jobs"
    API_KEY = "salad_cloud_user_2411tVI5kemHUAwAYZ56nmrswDKmR1bFkNnGZYPulAf2lm15E"  # Replace with your actual Salad API key
    headers = {
        "Salad-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "input": {
            "url": file_url,
            "return_as_file": False,
            "language_code": "en",
            "sentence_level_timestamps": True,
            "word_level_timestamps": True,
            "diarization": True,
            "sentence_diarization": True,
            "srt": True,
            "summarize": 0
        },
        "metadata": {
            "file_name": file_name
        }
    }
    
    if speaker:
        payload["metadata"]["selected_speaker"] = speaker

    response = requests.post(API_ENDPOINT, headers=headers, json=payload)

    if response.status_code in (200, 201):
        job_data = response.json()
        job_id = job_data.get("id")
        if job_id:
            final_data = poll_transcription(job_id, headers)
            return final_data
        else:
            print("No job id returned.")
            return None
    else:
        print("Error:", response.status_code, response.text)
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file provided')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file_url = upload_file_to_bunny(file, filename)
            if not file_url:
                flash("File upload to Bunny failed")
                return redirect(request.url)
            speaker = request.form.get('speakers')
            result = transcribe_audio(file_url, filename, speaker)
            transcript = result.get("output", {}) if result else {}

            return render_template('transcript.html', transcript=transcript, file_name=filename, file_url=file_url)
    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
