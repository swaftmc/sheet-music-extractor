"""Local web UI: upload audio/video, pick an instrument, get sheet music."""
import tempfile
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from transcribe import INSTRUMENTS, SOURCES, transcribe

JOBS = Path(tempfile.gettempdir()) / "sheetmusic_jobs"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB, enough for phone videos


@app.get("/")
def index():
    return render_template("index.html", instruments=list(INSTRUMENTS))


@app.post("/transcribe")
def run():
    f = request.files.get("file")
    name = request.form.get("instrument", "piano")
    if not f or not f.filename:
        return jsonify(error="Choose a file first."), 400
    if name not in INSTRUMENTS:
        return jsonify(error="Unknown instrument."), 400
    source = request.form.get("source", "piano")
    if source not in SOURCES:
        return jsonify(error="Unknown recording type."), 400
    bpm = request.form.get("bpm", type=int)
    if bpm is not None and not 30 <= bpm <= 300:
        return jsonify(error="Tempo must be between 30 and 300 BPM."), 400

    job = uuid.uuid4().hex
    out = JOBS / job
    out.mkdir(parents=True)
    src = out / ("input" + Path(f.filename).suffix.lower()[:10])  # never trust the uploaded name as a path
    f.save(src)
    try:
        info = transcribe(src, out, name, bpm, source)
    except ValueError as e:
        return jsonify(error=str(e)), 422
    finally:
        src.unlink(missing_ok=True)
    return jsonify(job=job, **info)


@app.get("/jobs/<job>/<fname>")
def download(job, fname):
    if len(job) != 32 or not all(c in "0123456789abcdef" for c in job) or fname not in ("score.musicxml", "score.mid"):
        abort(404)
    return send_from_directory(JOBS / job, fname, as_attachment=request.args.get("dl") == "1")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
