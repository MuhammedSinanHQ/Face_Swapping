# Face Swapping App

A lightweight Flask web application that lets you swap faces between two photos directly in your browser.  
Upload a **source** image (the face you want to use) and a **target** image (where the face will be placed), then click **Swap** — the result appears on the same page and can be downloaded instantly.

---

## Features

- 📸 **Two-image upload** — source and target previewed in-browser before processing
- 🔄 **OpenCV-powered face swap** — Haar-cascade face detection + `cv2.seamlessClone` for natural blending
- ⚡ **Single-page UI** — no page reloads; result shown immediately via Fetch API
- ✅ **Secure uploads** — extension validation, `secure_filename`, and unique UUIDs prevent collisions
- 🎨 **Orange-themed responsive UI** — matches provided design mockups; works on mobile
- 🚀 **Render-ready** — includes `render.yaml` for one-click free-tier deployment
- 🛡️ **Graceful error handling** — clear messages for missing files, wrong types, and undetected faces

---

## Project Structure

```
Face_Swapping/
├── app.py                  # Flask application & face-swap logic
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment config
├── README.md
├── templates/
│   └── index.html          # Single-page UI template
└── static/
    ├── css/
    │   └── style.css       # Orange-themed stylesheet
    └── uploads/            # Temporary upload / output storage
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/MuhammedSinanHQ/Face_Swapping.git
cd Face_Swapping

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

> **Requirements:** Python 3.9+, pip

---

## Local Run

```bash
python app.py
```

Open your browser at **http://localhost:5000**.

### Usage

1. Click **Browse** under *Source Image* and choose the face you want to graft.
2. Click **Browse** under *Target Image* and choose the photo to receive the face.
3. Click the orange **Swap** button.
4. The swapped result appears in the *Output* panel.  Click **Download** to save it.

---

## Deployment on Render (free tier)

1. Push this repository to GitHub.
2. Go to [render.com](https://render.com) and create a **New Web Service**.
3. Connect your GitHub repo.
4. Render auto-detects `render.yaml` and pre-fills:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. Click **Create Web Service** — deployment completes in ~2 minutes.

> The free tier spins down after inactivity; the first request after sleep may take ~30 s.

---

## Algorithm Notes

| Step | Detail |
|------|--------|
| Face detection | `haarcascade_frontalface_default.xml` (included with OpenCV) |
| Face selection | Largest detected bounding box is chosen in both images |
| Alignment | Source face region resized to target face dimensions |
| Blending | `cv2.seamlessClone` with an elliptical mask for seamless integration |

### Known edge cases

- **No face detected** → returns a 422 error with a descriptive message.
- **Multiple faces** → the largest face in each image is used.
- **Profile / heavily-occluded faces** → Haar cascades may miss non-frontal faces; a DLIB or MediaPipe-based detector can be substituted in `swap_faces()` for better accuracy.
- **Very large images** → capped at 16 MB; resize before uploading if needed.

---

## License

MIT
