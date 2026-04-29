
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

    # Save uploaded file
    job_id = str(uuid.uuid4())
    video_path = f"data/{job_id}_{file.filename}"
    output_dir = f"output/{job_id}"
    os.makedirs(output_dir, exist_ok=True)
    file.save(video_path)

    # Track job
    jobs[job_id] = {"status": "processing", "result": None, "error": None}

    def run():
        try:
            result = run_pipeline(
                video=Path(video_path),
                output=Path(output_dir) / "notes.md",
                # no_ai=False,     # add if you want to expose this option
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
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "Notes not ready"}), 404

    notes_path = job["result"]["notes_path"]
    return send_file(notes_path, mimetype="text/markdown", as_attachment=True)