import uuid
import threading
import subprocess
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

bp = Blueprint("api", __name__)

jobs = {}
_job_lock = threading.Lock()
_job_procs: dict[str, subprocess.Popen] = {}

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

    project_root = Path(__file__).parent.parent.resolve()
    job_id = str(uuid.uuid4())

    video_path = project_root / "data" / f"{job_id}_{file.filename}"
    output_dir = project_root / "output" / job_id

    output_dir.mkdir(parents=True, exist_ok=True)
    video_path.parent.mkdir(parents=True, exist_ok=True)

    file.save(video_path)

    with _job_lock:
        jobs[job_id] = {
            "status": "processing",
            "result": None,
            "error": None,
            "output_dir": str(output_dir),
            "logs": None,
        }

    # Run the pipeline in a separate OS process so we can actually stop it.
    # `run_pipeline()` already generates both `notes.md` and `notes_embedded.md`.
    project_root = Path(__file__).parent.parent.resolve()
    notes_path = output_dir / "notes.md"
    embedded_notes_path = output_dir / "notes_embedded.md"
    cmd = [
        sys.executable,
        "-m",
        "src.main",
        str(video_path),
        "-o",
        str(notes_path),
        "--config",
        str(project_root / "config.yaml"),
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    with _job_lock:
        _job_procs[job_id] = proc

    def _monitor() -> None:
        try:
            stdout, stderr = proc.communicate()
            combined = (stdout or "") + ("\n" if stdout and stderr else "") + (stderr or "")
            # Keep logs bounded so status payload stays sane.
            if len(combined) > 8000:
                combined = combined[-8000:]

            with _job_lock:
                job = jobs.get(job_id)
                if not job:
                    return
                job["logs"] = combined or None

                # If the user canceled, keep it canceled even if the process
                # returns non-zero due to termination.
                if job["status"] == "canceled":
                    job["result"] = None
                    job["error"] = "Canceled by user"
                    return

                if proc.returncode == 0:
                    job["status"] = "done"
                    job["result"] = {
                        "notes_path": str(notes_path),
                        "embedded_notes_path": str(embedded_notes_path),
                        "output_dir": str(output_dir),
                    }
                    job["error"] = None
                else:
                    job["status"] = "failed"
                    job["result"] = None
                    job["error"] = f"Pipeline failed (exit {proc.returncode})"
        finally:
            with _job_lock:
                _job_procs.pop(job_id, None)

    threading.Thread(target=_monitor, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "processing"}), 202




@bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    with _job_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"job_id": job_id, **job})


@bp.route("/notes/<job_id>", methods=["GET"])
def get_notes(job_id):
    """Download the generated notes with embedded images"""
    with _job_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "Notes not ready"}), 404

    try:
        result = job["result"]
        # Prefer embedded version
        notes_path = Path(result.get("embedded_notes_path") or result["notes_path"])

        if not notes_path.exists():
            return jsonify({"error": "Notes file not found"}), 404

        return send_file(
            notes_path,
            mimetype="text/markdown",
            as_attachment=True,
            download_name=f"notes_{job_id[:8]}.md"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to send file: {str(e)}"}), 500


@bp.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    """Cancel a running job (frontend + backend)."""
    with _job_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job["status"] in ["done", "failed", "canceled"]:
            return jsonify({"message": f"Job already in {job['status']} state"}), 200

        job["status"] = "canceled"
        job["error"] = "Canceled by user"

        proc = _job_procs.get(job_id)

    # Terminate outside the lock.
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            # Give it a moment to shut down cleanly (flush files, close handles).
            proc.wait(timeout=3.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    return jsonify({"status": "canceled", "message": "Job has been canceled"}), 200
