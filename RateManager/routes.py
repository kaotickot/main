import os
import uuid
from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from services.processor import read_file_columns, process_to_csv
from io import BytesIO

main_blueprint = Blueprint("main", __name__)

ALLOWED_EXT = {"csv", "xls", "xlsx", "xlsm"}


def allowed_filename(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@main_blueprint.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@main_blueprint.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("source_file")
    if not file or file.filename == "":
        flash("No file selected", "danger")
        return redirect(url_for("main.index"))

    if not allowed_filename(file.filename):
        flash("Unsupported file type", "danger")
        return redirect(url_for("main.index"))

    filename = secure_filename(file.filename)
    uid = uuid.uuid4().hex
    save_name = f"{uid}_{filename}"
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], save_name)
    file.save(dest)

    try:
        columns = read_file_columns(dest)
    except Exception as e:
        flash(f"Error reading file: {e}", "danger")
        return redirect(url_for("main.index"))

    required_fields = [
        "destination",
        "prefix",
        "rate",
        "setup",
        "currency",
        "description",
    ]

    return render_template(
        "map.html",
        columns=columns,
        required_fields=required_fields,
        filepath=save_name,
    )


@main_blueprint.route("/generate", methods=["POST"])
def generate():
    form = request.form
    filepath = form.get("filepath")
    if not filepath:
        flash("Missing file reference", "danger")
        return redirect(url_for("main.index"))

    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filepath)
    if not os.path.exists(upload_path):
        flash("Uploaded file not found on server", "danger")
        return redirect(url_for("main.index"))

    # Build mapping and defaults
    mapping = {}
    defaults = {}
    for key, value in form.items():
        if key.startswith("map_"):
            field = key[len("map_") :]
            mapping[field] = value if value != "__DEFAULT__" else None
        if key.startswith("def_"):
            field = key[len("def_") :]
            val = form.get(key)
            if val != "":
                defaults[field] = val

    try:
        discount = float(form.get("discount", 0))
    except ValueError:
        discount = 0.0
    try:
        gain = float(form.get("gain", 0))
    except ValueError:
        gain = 0.0

    try:
        csv_bytes = process_to_csv(upload_path, mapping, defaults, discount, gain)
    except Exception as e:
        flash(f"Error processing file: {e}", "danger")
        return redirect(url_for("main.index"))

    return send_file(
        BytesIO(csv_bytes),
        mimetype="text/csv",
        as_attachment=True,
        download_name="rates_generated.csv",
    )
