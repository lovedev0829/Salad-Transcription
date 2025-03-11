import os
import subprocess
from datetime import datetime

class Download:
    def __init__(self, output_dir=os.getcwd(), debug=False):
        self.output_dir = output_dir
        self.debug_flag = debug
        self.model_bin = "yt-dlp.exe"  # Assuming yt-dlp.exe is in the system path
        self.opts = []

        # Ensure 'uploads' directory exists
        self.uploads_dir = os.path.join(self.output_dir, "uploads")
        os.makedirs(self.uploads_dir, exist_ok=True)

    def download_from_url(self, url):
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"output_file_{timestamp}.mp4"
            output_filepath = os.path.join(self.uploads_dir, output_filename)

            # Run yt-dlp command
            process = subprocess.Popen(
                [self.model_bin, url, "-o", output_filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = process.communicate()

            # Ensure the process is fully cleaned up
            process.wait()

            # Check for errors
            if process.returncode != 0:
                raise Exception(f"Download failed: {stderr.decode('utf-8')}")

            return output_filepath
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
