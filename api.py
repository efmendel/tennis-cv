from dotenv import load_dotenv

load_dotenv()

import json
import os
import threading
import uuid
from pathlib import Path

import boto3
import requests
from botocore.config import Config
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import tempfile
import subprocess

# Import your existing modules
from swing_analyzer import SwingAnalyzer
from video_processor import PRESET_DIFFICULT_VIDEO, VideoProcessor
from visualize_swing import visualize_swing_phases

app = Flask(__name__)

# --- CONFIGURATION ---
# Local temporary storage (Render wipes this on restart, which is fine for temp processing)
TEMP_DIR = tempfile.gettempdir()
UPLOAD_FOLDER = os.path.join(TEMP_DIR, "shotvision_uploads")
RESULTS_FOLDER = os.path.join(TEMP_DIR, "shotvision_results")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# B2 / Cloud Configuration
B2_BUCKET_NAME = os.environ.get("B2_BUCKET_NAME")
B2_ENDPOINT = os.environ.get(
    "B2_ENDPOINT"
)  # e.g. https://s3.us-west-004.backblazeb2.com
B2_KEY_ID = os.environ.get("B2_KEY_ID")
B2_APP_KEY = os.environ.get("B2_APP_KEY")

# Next.js Webhook Configuration
WEBHOOK_URL = os.environ.get(
    "NEXT_WEBHOOK_URL"
)  # e.g. https://your-app.vercel.app/api/ai-completion
AI_SECRET = os.environ.get(
    "AI_SERVICE_SECRET"
)  # Must match the secret in your Next.js env

# Initialize B2 Client
b2_client = boto3.client(
    service_name="s3",
    endpoint_url=B2_ENDPOINT,
    aws_access_key_id=B2_KEY_ID,
    aws_secret_access_key=B2_APP_KEY,
    config=Config(signature_version="s3v4"),
)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "AI Worker Running"})


def process_and_callback(video_id, download_url, raw_key, user_id):
    """
    Background task to download, process, upload, and notify.
    """
    local_input_path = os.path.join(UPLOAD_FOLDER, f"{video_id}.mp4")
    local_output_path = os.path.join(RESULTS_FOLDER, f"{video_id}_annotated.mp4")

    try:
        print(f"[{video_id}] Starting processing...")

        # 1. Download Video from Signed URL
        print(f"[{video_id}] Downloading from B2...")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_input_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # 2. Analyze Video
        print(f"[{video_id}] Analyzing swing...")
        processor = VideoProcessor(pose_config=PRESET_DIFFICULT_VIDEO)
        video_data = processor.process_video(local_input_path)

        analyzer = SwingAnalyzer(
            velocity_threshold=0.5,
            use_adaptive_velocity=True,
            kinematic_chain_mode=True,
        )
        results = analyzer.analyze_swing(video_data)

        # 3. Create Annotated Video (Temp file with mp4v)
        temp_output_path = os.path.join(RESULTS_FOLDER, f"{video_id}_temp.mp4")
        
        # NOTE: Make sure your visualize_swing_phases uses 'mp4v' as the codec now
        visualize_swing_phases(
            video_path=local_input_path, 
            analysis_results=results, 
            output_path=temp_output_path 
        )

        # 3b. Convert to Web-Ready H.264 using FFmpeg
        print(f"[{video_id}] Converting to H.264 for Web...")
        
        # This command reads the temp file and re-encodes it to H.264
        # -y overwrites output, -vcodec libx264 ensures browser compatibility
        # -crf 23 is a good balance of quality vs size
        ffmpeg_cmd = [
            'ffmpeg', '-y', 
            '-i', temp_output_path,
            '-vcodec', 'libx264',
            '-f', 'mp4',
            local_output_path
        ]
        
        # Run the command
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up the non-web-ready temp file
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

        # --- SAFETY CHECK: Ensure video actually exists and is not empty ---
        if not os.path.exists(local_output_path):
            raise Exception("Output video file was NOT created (File Missing)")

        file_size = os.path.getsize(local_output_path)
        print(f"[{video_id}] Generated Video Size: {file_size} bytes")

        if file_size < 1000:  # If less than 1KB, something is definitely wrong
            raise Exception(
                f"Output video is too small ({file_size} bytes). Encoding failed."
            )
        # -------------------------------------------------------------------

        # 4. Upload Result to B2
        # Saving to 'videos/' folder as requested
        annotated_key = f"videos/{user_id}/{video_id}_annotated.mp4"
        print(f"[{video_id}] Uploading to B2 Key: {annotated_key}")

        b2_client.upload_file(
            local_output_path,
            B2_BUCKET_NAME,
            annotated_key,
            ExtraArgs={"ContentType": "video/mp4"},
        )

        # 5. Call Next.js Webhook
        print(f"[{video_id}] Calling Webhook...")
        webhook_payload = {
            "videoId": video_id,
            "annotatedKey": annotated_key,
            "analysis": results.to_dict(),
            "rawKey": raw_key,
            "status": "completed",
        }

        response = requests.post(
            WEBHOOK_URL,
            json=webhook_payload,
            headers={"x-secret": AI_SECRET, "Content-Type": "application/json"},
        )
        print(f"[{video_id}] Webhook Response: {response.status_code}")

    except Exception as e:
        print(f"[{video_id}] ERROR: {str(e)}")
        import traceback

        traceback.print_exc()

        # Notify Webhook of failure
        try:
            requests.post(
                WEBHOOK_URL,
                json={"videoId": video_id, "status": "failed", "error": str(e)},
                headers={"x-secret": AI_SECRET},
            )
        except:
            pass
    finally:
        # Cleanup local temp files
        if os.path.exists(local_input_path):
            os.remove(local_input_path)
        if os.path.exists(local_output_path):
            os.remove(local_output_path)


@app.route("/process", methods=["POST"])
def trigger_analysis():
    """
    Endpoint called by Next.js.
    Payload: { videoId, userId, videoUrl, rawKey }
    """
    data = request.json

    if not data or "videoUrl" not in data:
        return jsonify({"error": "Missing parameters"}), 400

    video_id = data.get("videoId")
    download_url = data.get("videoUrl")
    raw_key = data.get("rawKey")
    user_id = data.get("userId")

    if request.headers.get("x-secret") != AI_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    thread = threading.Thread(
        target=process_and_callback, args=(video_id, download_url, raw_key, user_id)
    )
    thread.start()

    return jsonify({"success": True, "message": "Processing started"}), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
