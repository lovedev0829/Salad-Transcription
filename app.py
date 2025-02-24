import os
import time
import requests
from flask import Flask, request, render_template, redirect, flash, url_for, send_from_directory

app = Flask(__name__)
app.secret_key = 'ZureilTranScript'  # Replace with a strong secret key
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def poll_transcription(job_id, headers, timeout=60, interval=5):
    """
    Poll the Salad API GET endpoint until the job status is "succeeded" or a timeout occurs.
    """
    job_url = f"https://api.salad.com/api/public/organizations/maariv/inference-endpoints/transcribe/jobs/{job_id}"
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(job_url, headers=headers)
        print("poll transcription >>>>>>>", response.json())

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

def transcribe_audio(file_url, speaker_name=None):
    """
    Post a transcription job to Salad and poll for the completed transcript.
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
            "return_as_file": False,  # Set to False to receive the full transcription in the response
            "language_code": "en",
            "sentence_level_timestamps": True,
            "word_level_timestamps": True,
            "diarization": True,
            "sentence_diarization": True,
            "srt": True,
            "summarize": 0  # No summarization; set a positive integer if needed
        },
        "metadata": {}
    }
    # Include the selected speaker in metadata if provided.
    if speaker_name:
        payload["metadata"]["selected_speaker"] = speaker_name

    response = requests.post(API_ENDPOINT, headers=headers, json=payload)
    print("transcribe response >>>>>>", response)

    # Accept both 200 and 201 as success codes
    if response.status_code in (200, 201):
        job_data = response.json()
        job_id = job_data.get("id")
        print("job_id", job_id)
        if job_id:
            # Poll for the completed transcription
            final_data = poll_transcription(job_id, headers)
            return final_data
        else:
            print("No job id returned.")
            return None
    else:
        print("Error:", response.status_code, response.text)
        return None

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Serve the uploaded file so that it can be accessed via a public URL.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
            # Save the uploaded file locally
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            # Generate a public URL for the uploaded file
            file_url = url_for('uploaded_file', filename=file.filename, _external=True)
            # Get the selected speaker (from the single-select dropdown)
            speaker_name = request.form.get('speaker_names')
            # Start the transcription job
            result = transcribe_audio(file_url, speaker_name=speaker_name)
            # Expecting transcript output in the "output" field
            transcript = result.get("output", {}) if result else {}
            return render_template('transcript.html', transcript=transcript)
    return render_template('index.html')

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
