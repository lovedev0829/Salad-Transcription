from flask import Blueprint, request, jsonify
from transcribe import Transcriber  # Import your transcriber class

transcribe_bp = Blueprint('transcribe', __name__)  # Create a Blueprint

transcriber = Transcriber()

@transcribe_bp.route('/import_file', methods=['POST'])
def import_file():
    return transcriber.import_file()

@transcribe_bp.route('/audio_to_text', methods=['POST'])
def transcribe_audio():
    return transcriber.transcribe_audio(request)
