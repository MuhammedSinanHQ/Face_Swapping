import os
import uuid
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def unique_filename(original: str) -> str:
    ext = original.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def load_haarcascade() -> cv2.CascadeClassifier:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    return face_cascade


def detect_faces(gray: np.ndarray, cascade: cv2.CascadeClassifier):
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return faces if len(faces) > 0 else []


def swap_faces(src_path: str, tgt_path: str) -> np.ndarray:
    """
    Perform a seamless face swap from source onto target.

    Algorithm:
    1. Detect the largest face in both images.
    2. Align the source face bounding box to the target face bounding box
       (scale + translate via perspective warp).
    3. Create an elliptical mask over the target face region.
    4. Use cv2.seamlessClone to blend the warped source face into the target image.
    """
    cascade = load_haarcascade()

    src_img = cv2.imread(src_path)
    tgt_img = cv2.imread(tgt_path)

    if src_img is None:
        raise ValueError("Could not read source image.")
    if tgt_img is None:
        raise ValueError("Could not read target image.")

    src_gray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
    tgt_gray = cv2.cvtColor(tgt_img, cv2.COLOR_BGR2GRAY)

    src_faces = detect_faces(src_gray, cascade)
    tgt_faces = detect_faces(tgt_gray, cascade)

    if len(src_faces) == 0:
        raise ValueError("No face detected in the source image.")
    if len(tgt_faces) == 0:
        raise ValueError("No face detected in the target image.")

    # Pick the largest face in each image
    src_x, src_y, src_w, src_h = max(src_faces, key=lambda f: f[2] * f[3])
    tgt_x, tgt_y, tgt_w, tgt_h = max(tgt_faces, key=lambda f: f[2] * f[3])

    # Crop source face region
    src_face = src_img[src_y : src_y + src_h, src_x : src_x + src_w]

    # Resize source face to target face dimensions; choose interpolation by scale
    if src_w * src_h >= tgt_w * tgt_h:
        interp = cv2.INTER_AREA
    else:
        interp = cv2.INTER_CUBIC
    src_face_resized = cv2.resize(src_face, (tgt_w, tgt_h), interpolation=interp)

    # Place resized source face on a copy of the target image
    output = tgt_img.copy()
    output[tgt_y : tgt_y + tgt_h, tgt_x : tgt_x + tgt_w] = src_face_resized

    # Build elliptical mask (single-channel) centered on the target face region
    mask = np.zeros(tgt_img.shape[:2], dtype=np.uint8)
    center = (tgt_x + tgt_w // 2, tgt_y + tgt_h // 2)
    axes = (tgt_w // 2, tgt_h // 2)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)

    # Seamless clone for natural blending (seamlessClone expects a single-channel mask)
    result = cv2.seamlessClone(output, tgt_img, mask, center, cv2.NORMAL_CLONE)

    return result


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/swap", methods=["POST"])
def swap():
    source_file = request.files.get("source")
    target_file = request.files.get("target")

    errors = []
    if not source_file or source_file.filename == "":
        errors.append("Source image is required.")
    elif not allowed_file(source_file.filename):
        errors.append("Source image must be a PNG, JPG, JPEG, or WEBP file.")

    if not target_file or target_file.filename == "":
        errors.append("Target image is required.")
    elif not allowed_file(target_file.filename):
        errors.append("Target image must be a PNG, JPG, JPEG, or WEBP file.")

    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    src_filename = unique_filename(secure_filename(source_file.filename))
    tgt_filename = unique_filename(secure_filename(target_file.filename))
    src_path = os.path.join(UPLOAD_FOLDER, src_filename)
    tgt_path = os.path.join(UPLOAD_FOLDER, tgt_filename)

    source_file.save(src_path)
    target_file.save(tgt_path)

    try:
        result_img = swap_faces(src_path, tgt_path)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception:
        return jsonify({"error": "An unexpected error occurred during face swapping."}), 500

    out_filename = f"result_{uuid.uuid4().hex}.jpg"
    out_path = os.path.join(UPLOAD_FOLDER, out_filename)
    cv2.imwrite(out_path, result_img)

    return jsonify(
        {
            "output_url": url_for("static", filename=f"uploads/{out_filename}"),
            "source_url": url_for("static", filename=f"uploads/{src_filename}"),
            "target_url": url_for("static", filename=f"uploads/{tgt_filename}"),
        }
    )


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)
