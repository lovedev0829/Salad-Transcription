from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from routes.transcribe_routes import transcribe_bp  # Import Blueprint

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Register Blueprints (routers)
app.register_blueprint(transcribe_bp, url_prefix='/api/transcribe')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
