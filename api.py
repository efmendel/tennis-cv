"""
Flask API for Tennis Swing Analysis

Provides REST endpoints for video upload, swing analysis, and result retrieval.
Includes automatic video cleanup, CORS support, and comprehensive error handling.
"""

import os
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from swing_analyzer import SwingAnalyzer
from video_processor import PRESET_DIFFICULT_VIDEO, VideoProcessor

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration from environment variables
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
RESULTS_FOLDER = os.getenv("RESULTS_FOLDER", "results")
VIDEO_EXPIRY_HOURS = int(os.getenv("VIDEO_EXPIRY_HOURS", "1"))
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

# Allowed video extensions
ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

# Video cache: {video_id: {path, original_path, created_at, expires_at, analysis}}
video_cache = {}
cache_lock = threading.Lock()

# Ensure upload and results directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_expired_videos():
    """Background thread function to clean up expired videos."""
    while True:
        try:
            time.sleep(300)  # Check every 5 minutes

            with cache_lock:
                now = datetime.now()
                expired_ids = []

                for video_id, metadata in video_cache.items():
                    if now > metadata["expires_at"]:
                        expired_ids.append(video_id)

                # Remove expired videos
                for video_id in expired_ids:
                    metadata = video_cache[video_id]

                    # Delete files
                    try:
                        if os.path.exists(metadata["path"]):
                            os.remove(metadata["path"])
                        if os.path.exists(metadata["original_path"]):
                            os.remove(metadata["original_path"])
                    except Exception as e:
                        print(f"Error deleting files for {video_id}: {e}")

                    # Remove from cache
                    del video_cache[video_id]
                    print(f"Cleaned up expired video: {video_id}")

        except Exception as e:
            print(f"Error in cleanup thread: {e}")


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired_videos, daemon=True)
cleanup_thread.start()


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Analyze a tennis swing video.

    Accepts multipart/form-data with 'video' file and optional parameters.

    Request:
        - video (file, required): Video file to analyze
        - use_adaptive (bool, optional): Use adaptive velocity threshold
        - velocity_threshold (float, optional): Fixed velocity threshold
        - adaptive_percent (float, optional): Percentage of max velocity
        - contact_angle_min (int, optional): Minimum elbow angle at contact
        - kinematic_chain_mode (bool, optional): Use kinematic chain analysis
        - contact_detection_method (str, optional): 'velocity_peak', 'kinematic_chain', or 'hybrid'

    Response:
        200: {
            'video_id': str,
            'video_url': str,
            'download_url': str,
            'analysis': dict
        }
        400: {'error': str}
        500: {'error': str}
    """
    # Check if video file is present
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files["video"]

    # Check if file was selected
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Check file extension
    if not allowed_file(file.filename):
        return jsonify(
            {
                "error": f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            }
        ), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_VIDEO_SIZE_BYTES:
        return jsonify(
            {"error": f"File too large. Maximum size: {MAX_VIDEO_SIZE_MB}MB"}
        ), 400

    try:
        # Generate unique video ID
        video_id = str(uuid.uuid4())

        # Secure filename and save uploaded file
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit(".", 1)[1].lower()
        original_path = os.path.join(
            UPLOAD_FOLDER, f"{video_id}_original.{file_extension}"
        )
        file.save(original_path)

        # Parse optional parameters
        use_adaptive = request.form.get("use_adaptive", "true").lower() == "true"
        velocity_threshold = float(request.form.get("velocity_threshold", "0.5"))
        adaptive_percent = float(request.form.get("adaptive_percent", "0.15"))
        contact_angle_min = int(request.form.get("contact_angle_min", "120"))
        kinematic_chain_mode = (
            request.form.get("kinematic_chain_mode", "true").lower() == "true"
        )
        contact_detection_method = request.form.get(
            "contact_detection_method", "kinematic_chain"
        )

        # Validate contact_detection_method
        valid_methods = ["velocity_peak", "kinematic_chain", "hybrid"]
        if contact_detection_method not in valid_methods:
            return jsonify(
                {
                    "error": f"Invalid contact_detection_method. Must be one of: {', '.join(valid_methods)}"
                }
            ), 400

        # Process video
        print(f"Processing video {video_id}...")
        processor = VideoProcessor(pose_config=PRESET_DIFFICULT_VIDEO)
        video_data = processor.process_video(original_path)

        # Analyze swing
        print(f"Analyzing swing for video {video_id}...")
        analyzer = SwingAnalyzer(
            velocity_threshold=velocity_threshold,
            contact_angle_min=contact_angle_min,
            use_adaptive_velocity=use_adaptive,
            adaptive_velocity_percent=adaptive_percent,
            kinematic_chain_mode=kinematic_chain_mode,
            contact_detection_method=contact_detection_method,
        )
        results = analyzer.analyze_swing(video_data)

        # Generate annotated video
        print(f"Creating annotated video for {video_id}...")
        annotated_path = os.path.join(RESULTS_FOLDER, f"{video_id}_annotated.mp4")

        # Import visualize_swing_phases function
        from visualize_swing import visualize_swing_phases

        # Create annotated video with SwingAnalysisResults
        visualize_swing_phases(
            video_path=original_path,
            analysis_results=results,
            output_path=annotated_path,
        )

        # Store in cache
        with cache_lock:
            video_cache[video_id] = {
                "path": annotated_path,
                "original_path": original_path,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=VIDEO_EXPIRY_HOURS),
                "analysis": results.to_dict(),
            }

        # Return response
        return jsonify(
            {
                "video_id": video_id,
                "video_url": f"/api/video/{video_id}",
                "download_url": f"/api/download/{video_id}",
                "analysis": results.to_dict(),
                "expires_at": video_cache[video_id]["expires_at"].isoformat(),
            }
        ), 200

    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(original_path):
            try:
                os.remove(original_path)
            except:
                pass

        print(f"Error processing video: {e}")
        import traceback

        traceback.print_exc()

        return jsonify({"error": f"Error processing video: {str(e)}"}), 500


@app.route("/api/video/<video_id>")
def get_video(video_id):
    """
    Stream annotated video for browser playback.

    Args:
        video_id: UUID of the video

    Response:
        200: Video stream (video/mp4)
        404: {'error': 'Video not found or expired'}
    """
    with cache_lock:
        if video_id not in video_cache:
            return jsonify({"error": "Video not found or expired"}), 404

        metadata = video_cache[video_id]

        # Check if expired
        if datetime.now() > metadata["expires_at"]:
            return jsonify({"error": "Video expired"}), 404

        video_path = metadata["path"]

    # Check if file exists
    if not os.path.exists(video_path):
        return jsonify({"error": "Video file not found"}), 404

    # Stream video
    return send_file(
        video_path,
        mimetype="video/mp4",
        as_attachment=False,
        download_name=f"analysis_{video_id}.mp4",
    )


@app.route("/api/download/<video_id>")
def download_video(video_id):
    """
    Download annotated video file.

    Args:
        video_id: UUID of the video

    Response:
        200: Video file download (video/mp4)
        404: {'error': 'Video not found or expired'}
    """
    with cache_lock:
        if video_id not in video_cache:
            return jsonify({"error": "Video not found or expired"}), 404

        metadata = video_cache[video_id]

        # Check if expired
        if datetime.now() > metadata["expires_at"]:
            return jsonify({"error": "Video expired"}), 404

        video_path = metadata["path"]

    # Check if file exists
    if not os.path.exists(video_path):
        return jsonify({"error": "Video file not found"}), 404

    # Download video
    return send_file(
        video_path,
        mimetype="video/mp4",
        as_attachment=True,
        download_name=f"swing_analysis_{video_id}.mp4",
    )


@app.route("/api/status/<video_id>")
def get_status(video_id):
    """
    Get processing status for a video.

    This endpoint is for future async processing enhancement.
    Currently, all processing is synchronous.

    Args:
        video_id: UUID of the video

    Response:
        200: {
            'video_id': str,
            'status': 'completed' | 'processing' | 'failed',
            'created_at': str,
            'expires_at': str,
            'analysis': dict (if completed)
        }
        404: {'error': 'Video not found'}
    """
    with cache_lock:
        if video_id not in video_cache:
            return jsonify({"error": "Video not found"}), 404

        metadata = video_cache[video_id]

        response = {
            "video_id": video_id,
            "status": "completed",  # Always completed for now (synchronous)
            "created_at": metadata["created_at"].isoformat(),
            "expires_at": metadata["expires_at"].isoformat(),
            "analysis": metadata["analysis"],
        }

        return jsonify(response), 200


@app.route("/api/analysis/<video_id>")
def get_analysis(video_id):
    """
    Get analysis results only (without video).

    Args:
        video_id: UUID of the video

    Response:
        200: {
            'video_id': str,
            'analysis': dict,
            'created_at': str,
            'expires_at': str
        }
        404: {'error': 'Analysis not found or expired'}
    """
    with cache_lock:
        if video_id not in video_cache:
            return jsonify({"error": "Analysis not found or expired"}), 404

        metadata = video_cache[video_id]

        # Check if expired
        if datetime.now() > metadata["expires_at"]:
            return jsonify({"error": "Analysis expired"}), 404

        return jsonify(
            {
                "video_id": video_id,
                "analysis": metadata["analysis"],
                "created_at": metadata["created_at"].isoformat(),
                "expires_at": metadata["expires_at"].isoformat(),
            }
        ), 200


@app.route("/api/health")
def health_check():
    """
    Health check endpoint.

    Response:
        200: {
            'status': 'healthy',
            'cached_videos': int,
            'config': dict
        }
    """
    with cache_lock:
        cached_count = len(video_cache)

    return jsonify(
        {
            "status": "healthy",
            "cached_videos": cached_count,
            "config": {
                "upload_folder": UPLOAD_FOLDER,
                "results_folder": RESULTS_FOLDER,
                "video_expiry_hours": VIDEO_EXPIRY_HOURS,
                "max_video_size_mb": MAX_VIDEO_SIZE_MB,
                "allowed_formats": list(ALLOWED_EXTENSIONS),
            },
        }
    ), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors."""
    return jsonify(
        {"error": f"File too large. Maximum size: {MAX_VIDEO_SIZE_MB}MB"}
    ), 413


if __name__ == "__main__":
    print("=" * 60)
    print("TENNIS SWING ANALYSIS API")
    print("=" * 60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Results folder: {RESULTS_FOLDER}")
    print(f"Video expiry: {VIDEO_EXPIRY_HOURS} hour(s)")
    print(f"Max video size: {MAX_VIDEO_SIZE_MB}MB")
    print(f"Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print("=" * 60)
    print("\nStarting API server on http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  POST   /api/analyze         - Upload and analyze video")
    print("  GET    /api/video/<id>      - Stream annotated video")
    print("  GET    /api/download/<id>   - Download annotated video")
    print("  GET    /api/status/<id>     - Get processing status")
    print("  GET    /api/analysis/<id>   - Get analysis results only")
    print("  GET    /api/health          - Health check")
    print("=" * 60)

    # Configure max content length
    app.config["MAX_CONTENT_LENGTH"] = MAX_VIDEO_SIZE_BYTES

    # Run Flask app
    app.run(debug=True, port=5001, host="0.0.0.0")
