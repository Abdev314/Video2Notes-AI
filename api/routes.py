
import os
import uuid
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

# Correct import for your current structure
from src.main import run_pipeline

bp = Blueprint("api", __name__, url_prefix="/api")

jobs = {}

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@bp.route("/process", methods=["POST"])
def process_video():
    """Upload a video and start the pipeline asynchronously."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # === NEW CODE: Use absolute paths from project root ===
    project_root = Path(__file__).parent.parent.resolve()   # Goes from api/ → project root

    job_id = str(uuid.uuid4())

    # Define paths using project root
    video_path = project_root / "data" / f"{job_id}_{file.filename}"
    output_dir = project_root / "output" / job_id

    # Create directories
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path.parent.mkdir(parents=True, exist_ok=True)   # Ensure data/ exists

    # Save uploaded file
    file.save(video_path)

    # Track job
    jobs[job_id] = {
        "status": "processing",
        "result": None,
        "error": None
    }

    # Run pipeline in background thread
    def run():
        try:
            result = run_pipeline(
                video=Path(video_path),
                output=output_dir / "notes.md",        # ← This is where you put the second part
            )
            jobs[job_id] = {"status": "done", "result": result, "error": None}
        except Exception as e:
            jobs[job_id] = {"status": "failed", "result": None, "error": str(e)}

    threading.Thread(target=run, daemon=True).start()

    return jsonify({"job_id": job_id, "status": "processing"}), 202


@bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"job_id": job_id, **job})


@bp.route("/notes/<job_id>", methods=["GET"])
def get_notes(job_id):
    """Download the generated notes.md"""
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "Notes not ready"}), 404

    try:
        notes_path = Path(job["result"]["notes_path"]).resolve()

        if not notes_path.exists():
            return jsonify({"error": "Notes file not found on disk"}), 404

        return send_file(
            notes_path,
            mimetype="text/markdown",
            as_attachment=True,
            download_name=f"notes_{job_id[:8]}.md"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to send file: {str(e)}"}), 500