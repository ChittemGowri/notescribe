import pytesseract
from PIL import Image
import cv2
import numpy as np
from flask import Flask, request, render_template_string, send_file, redirect
import os
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Home page ──────────────────────────────────────────────────────────────────
HOME_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>NoteScribe by Gowrishankar</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --ink: #0f0e0c; --paper: #f7f4ee; --accent: #c8501a;
      --accent-light: #f0d5c8; --muted: #7a7570; --border: #d6d0c6;
      --card: #ffffff; --green: #2d7a2d; --green-bg: #eef6ee;
    }
    body { font-family: "Segoe UI", Ubuntu, sans-serif; background: var(--paper); color: var(--ink); min-height: 100vh; animation: pageFade 0.6s ease; }
    @keyframes pageFade { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-18px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes slideUp   { from { opacity: 0; transform: translateY(22px);  } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }
    @keyframes spin  { to { transform: rotate(360deg); } }
    @keyframes checkPop { 0% { transform: scale(0.8); opacity: 0; } 70% { transform: scale(1.04); } 100% { transform: scale(1); opacity: 1; } }

    header {
      border-bottom: 1px solid var(--border); padding: 0 40px;
      display: flex; align-items: center; justify-content: space-between;
      height: 64px; background: rgba(247,244,238,0.92);
      backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 100;
      animation: slideDown 0.5s ease;
    }
    .logo { font-family: Georgia, serif; font-size: 1.35rem; letter-spacing: -0.02em; color: var(--ink); display: flex; align-items: center; gap: 10px; }
    .logo-dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; animation: pulse 2.5s infinite; }
    .by-name { font-size: 0.72rem; font-weight: 500; color: var(--muted); letter-spacing: 0.04em; }
    .badge { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); border: 1px solid var(--accent-light); background: var(--accent-light); padding: 3px 11px; border-radius: 20px; }

    .hero { text-align: center; padding: 70px 20px 44px; max-width: 640px; margin: 0 auto; animation: slideUp 0.6s ease 0.1s both; }
    .hero-tag { font-size: 0.73rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); margin-bottom: 14px; }
    .hero h1 { font-family: Georgia, serif; font-size: clamp(2rem, 5vw, 3rem); line-height: 1.12; letter-spacing: -0.03em; color: var(--ink); margin-bottom: 16px; }
    .hero h1 em { font-style: italic; color: var(--accent); }
    .hero p { font-size: 1rem; color: var(--muted); line-height: 1.75; max-width: 460px; margin: 0 auto; }
    .creator-line { margin-top: 16px; font-size: 0.82rem; color: var(--muted); }
    .creator-line strong { color: var(--accent); font-weight: 600; }

    .container { max-width: 860px; margin: 0 auto; padding: 0 24px 80px; }

    .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 40px; margin-bottom: 20px; animation: slideUp 0.5s ease 0.2s both; }

    .upload-zone {
      border: 2px dashed var(--border); border-radius: 12px; padding: 50px 24px;
      text-align: center; transition: all 0.22s ease; cursor: pointer;
      position: relative; background: var(--paper);
    }
    .upload-zone:hover, .upload-zone.dragover { border-color: var(--accent); background: var(--accent-light); transform: scale(1.01); }
    .upload-zone input[type=file] { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }
    .upload-icon { width: 52px; height: 52px; margin: 0 auto 14px; border: 1.5px solid var(--border); border-radius: 14px; display: flex; align-items: center; justify-content: center; background: white; transition: all 0.2s; }
    .upload-zone:hover .upload-icon { border-color: var(--accent); background: var(--accent-light); }
    .upload-icon svg { width: 24px; height: 24px; stroke: var(--accent); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
    .upload-title { font-family: Georgia, serif; font-size: 1.1rem; color: var(--ink); margin-bottom: 6px; }
    .upload-sub { font-size: 0.84rem; color: var(--muted); }

    #preview-wrap { display: none; margin-top: 18px; border-radius: 10px; overflow: hidden; border: 1px solid var(--border); animation: checkPop 0.4s ease; }
    #preview-img  { width: 100%; max-height: 220px; object-fit: cover; display: block; }
    .upload-success { background: var(--green-bg); border-top: 1px solid #b6ddb6; padding: 10px 16px; display: flex; align-items: center; gap: 10px; }
    .upload-success svg { width: 18px; height: 18px; stroke: var(--green); fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; flex-shrink: 0; }
    .upload-success span { font-size: 0.86rem; color: var(--green); font-weight: 500; }
    #file-label { font-size: 0.78rem; color: var(--muted); margin-left: auto; }

    .tips { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-top: 22px; }
    .tip { background: var(--paper); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; transition: border-color 0.2s; }
    .tip:hover { border-color: var(--accent); }
    .tip-label { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); margin-bottom: 5px; }
    .tip p { font-size: 0.81rem; color: var(--muted); line-height: 1.55; }

    .btn { display: inline-flex; align-items: center; gap: 9px; background: var(--ink); color: white; border: none; padding: 14px 34px; font-family: "Segoe UI", Ubuntu, sans-serif; font-size: 0.95rem; font-weight: 500; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; margin-top: 26px; letter-spacing: 0.01em; }
    .btn:hover { background: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 16px rgba(200,80,26,0.18); }
    .btn:active { transform: translateY(0); }
    .btn svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    .btn.loading { opacity: 0.75; cursor: not-allowed; }
    .spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; }

    .error-card { background: #fff8f7; border: 1px solid #f5c6bc; border-radius: 12px; padding: 18px 22px; color: #8b2a14; font-size: 0.9rem; display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px; animation: slideUp 0.3s ease; }
    .error-card svg { width: 18px; height: 18px; stroke: #c8501a; fill: none; stroke-width: 2; flex-shrink: 0; }

    footer { text-align: center; padding: 28px; font-size: 0.76rem; color: var(--muted); border-top: 1px solid var(--border); letter-spacing: 0.03em; }
    footer strong { color: var(--accent); font-weight: 600; }

    @media (max-width: 600px) {
      header { padding: 0 20px; }
      .card { padding: 22px 18px; }
      .tips { grid-template-columns: 1fr; }
      .hero { padding: 44px 20px 28px; }
    }
  </style>
</head>
<body>

<header>
  <div class="logo">
    <span class="logo-dot"></span>
    NoteScribe
    <span class="by-name">by Gowrishankar</span>
  </div>
  <span class="badge">OCR Tool</span>
</header>

<div class="hero">
  <p class="hero-tag">Handwriting Recognition</p>
  <h1>Turn your notes into<br/><em>digital text</em></h1>
  <p>Upload a photo of any handwritten page. Get clean, searchable, downloadable text in seconds — fully offline.</p>
  <p class="creator-line">Crafted by <strong>Gowrishankar</strong></p>
</div>

<div class="container">

  {% if error %}
  <div class="error-card">
    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    <span>{{ error }}</span>
  </div>
  {% endif %}

  <div class="card">
    <form method="POST" enctype="multipart/form-data" action="/gowrishankar/convert" id="upload-form">
      <div class="upload-zone" id="drop-zone">
        <input type="file" name="image" accept="image/*" id="file-input" onchange="handleFile(this)"/>
        <div class="upload-icon">
          <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        </div>
        <p class="upload-title">Drop your image here</p>
        <p class="upload-sub">or click to browse &mdash; JPG, PNG, WEBP supported</p>
      </div>

      <div id="preview-wrap">
        <img id="preview-img" src="" alt="preview"/>
        <div class="upload-success">
          <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Image uploaded successfully</span>
          <span id="file-label"></span>
        </div>
      </div>

      <div class="tips">
        <div class="tip"><div class="tip-label">Lighting</div><p>Shoot in natural daylight, avoid shadows across the page.</p></div>
        <div class="tip"><div class="tip-label">Angle</div><p>Hold phone directly above the notebook, flat and parallel.</p></div>
        <div class="tip"><div class="tip-label">Pen</div><p>Dark ink on white paper gives the best recognition.</p></div>
      </div>

      <button type="submit" class="btn" id="submit-btn">
        <svg viewBox="0 0 24 24"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
        Convert to text
      </button>
    </form>
  </div>

</div>

<footer>
  NoteScribe &mdash; Built by <strong>Gowrishankar</strong> &mdash; Powered by Python, Flask &amp; Tesseract OCR &mdash; Runs fully offline
</footer>

<script>
  function handleFile(input) {
    const file = input.files[0];
    if (!file) return;
    const wrap = document.getElementById("preview-wrap");
    const img  = document.getElementById("preview-img");
    const lbl  = document.getElementById("file-label");
    const reader = new FileReader();
    reader.onload = e => { img.src = e.target.result; lbl.textContent = file.name; wrap.style.display = "block"; };
    reader.readAsDataURL(file);
  }

  const dropZone = document.getElementById("drop-zone");
  dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("dragover"); });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
  dropZone.addEventListener("drop", e => {
    e.preventDefault(); dropZone.classList.remove("dragover");
    const files = e.dataTransfer.files;
    if (files.length) { document.getElementById("file-input").files = files; handleFile(document.getElementById("file-input")); }
  });

  document.getElementById("upload-form").addEventListener("submit", function(e) {
    const fi = document.getElementById("file-input");
    if (!fi.files.length) { e.preventDefault(); alert("Please select an image first."); return; }
    const btn = document.getElementById("submit-btn");
    btn.innerHTML = "<span class='spinner'></span> Converting...";
    btn.disabled = true; btn.classList.add("loading");
  });
</script>
</body>
</html>
'''

# ── Result page ────────────────────────────────────────────────────────────────
RESULT_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Result — NoteScribe by Gowrishankar</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --ink: #0f0e0c; --paper: #f7f4ee; --accent: #c8501a;
      --accent-light: #f0d5c8; --muted: #7a7570; --border: #d6d0c6;
      --card: #ffffff; --green: #2d7a2d; --green-bg: #eef6ee;
    }
    body { font-family: "Segoe UI", Ubuntu, sans-serif; background: var(--paper); color: var(--ink); min-height: 100vh; animation: pageFade 0.5s ease; }
    @keyframes pageFade { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp  { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse    { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }

    header { border-bottom: 1px solid var(--border); padding: 0 40px; display: flex; align-items: center; justify-content: space-between; height: 64px; background: rgba(247,244,238,0.92); backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 100; }
    .logo { font-family: Georgia, serif; font-size: 1.35rem; letter-spacing: -0.02em; color: var(--ink); display: flex; align-items: center; gap: 10px; }
    .logo-dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; animation: pulse 2.5s infinite; }
    .by-name { font-size: 0.72rem; font-weight: 500; color: var(--muted); letter-spacing: 0.04em; }
    .badge { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); border: 1px solid var(--accent-light); background: var(--accent-light); padding: 3px 11px; border-radius: 20px; }

    .container { max-width: 860px; margin: 0 auto; padding: 36px 24px 80px; }

    .success-banner { background: var(--green-bg); border: 1px solid #b6ddb6; border-radius: 12px; padding: 16px 22px; display: flex; align-items: center; gap: 14px; margin-bottom: 24px; animation: slideUp 0.4s ease; }
    .success-banner svg { width: 22px; height: 22px; stroke: var(--green); fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; flex-shrink: 0; }
    .success-banner span { font-size: 0.92rem; color: var(--green); font-weight: 500; }

    .result-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; margin-bottom: 24px; animation: slideUp 0.45s ease 0.05s both; }
    .result-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 26px; border-bottom: 1px solid var(--border); background: var(--paper); }
    .result-title { font-family: Georgia, serif; font-size: 1.05rem; color: var(--ink); display: flex; align-items: center; gap: 10px; }
    .result-title::before { content: ""; width: 8px; height: 8px; background: var(--green); border-radius: 50%; display: inline-block; }
    .result-meta { font-size: 0.78rem; color: var(--muted); }

    .result-body { padding: 26px; }
    .text-output { font-family: Georgia, serif; font-size: 0.98rem; line-height: 1.9; color: var(--ink); white-space: pre-wrap; background: var(--paper); border: 1px solid var(--border); border-radius: 10px; padding: 22px; max-height: 380px; overflow-y: auto; min-height: 80px; }
    .text-output::-webkit-scrollbar { width: 4px; }
    .text-output::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

    .result-actions { display: flex; align-items: center; gap: 12px; margin-top: 18px; flex-wrap: wrap; }

    .btn-download { display: inline-flex; align-items: center; gap: 8px; background: var(--accent); color: white; text-decoration: none; padding: 11px 24px; font-size: 0.88rem; font-weight: 500; border-radius: 8px; transition: all 0.2s ease; }
    .btn-download:hover { background: #a8401a; transform: translateY(-1px); }
    .btn-download svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }

    .btn-copy { display: inline-flex; align-items: center; gap: 8px; background: transparent; color: var(--ink); border: 1px solid var(--border); padding: 11px 20px; font-size: 0.88rem; font-weight: 400; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; font-family: "Segoe UI", Ubuntu, sans-serif; }
    .btn-copy:hover { border-color: var(--ink); background: var(--paper); }
    .btn-copy svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

    .word-count { margin-left: auto; font-size: 0.78rem; color: var(--muted); }

    .btn-new { display: inline-flex; align-items: center; gap: 9px; background: var(--ink); color: white; text-decoration: none; padding: 13px 28px; font-size: 0.92rem; font-weight: 500; border-radius: 8px; transition: all 0.2s ease; animation: slideUp 0.45s ease 0.15s both; }
    .btn-new:hover { background: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 16px rgba(200,80,26,0.18); }
    .btn-new svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

    footer { text-align: center; padding: 28px; font-size: 0.76rem; color: var(--muted); border-top: 1px solid var(--border); letter-spacing: 0.03em; }
    footer strong { color: var(--accent); font-weight: 600; }

    @media (max-width: 600px) {
      header { padding: 0 20px; }
      .container { padding: 24px 18px 60px; }
      .word-count { margin-left: 0; }
    }
  </style>
</head>
<body>

<header>
  <div class="logo">
    <span class="logo-dot"></span>
    NoteScribe
    <span class="by-name">by Gowrishankar</span>
  </div>
  <span class="badge">OCR Tool</span>
</header>

<div class="container">

  <div class="success-banner">
    <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
    <span>Conversion successful &mdash; your handwriting has been digitised.</span>
  </div>

  <div class="result-card">
    <div class="result-header">
      <span class="result-title">Extracted text</span>
      <span class="result-meta">{{ timestamp }}</span>
    </div>
    <div class="result-body">
      <div class="text-output" id="output-text">{{ text }}</div>
      <div class="result-actions">
        <a class="btn-download" href="/gowrishankar/download/{{ filename }}">
          <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download .txt
        </a>
        <button class="btn-copy" onclick="copyText()">
          <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          <span id="copy-label">Copy text</span>
        </button>
        <span class="word-count" id="word-count"></span>
      </div>
    </div>
  </div>

  <a href="/gowrishankar" class="btn-new">
    <svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
    Add another image
  </a>

</div>

<footer>
  NoteScribe &mdash; Built by <strong>Gowrishankar</strong> &mdash; Powered by Python, Flask &amp; Tesseract OCR &mdash; Runs fully offline
</footer>

<script>
  function copyText() {
    const text = document.getElementById("output-text").innerText;
    navigator.clipboard.writeText(text).then(() => {
      const label = document.getElementById("copy-label");
      label.textContent = "Copied!";
      setTimeout(() => label.textContent = "Copy text", 2000);
    });
  }
  const outputEl = document.getElementById("output-text");
  if (outputEl) {
    const words = outputEl.innerText.trim().split(/\s+/).filter(Boolean).length;
    const chars = outputEl.innerText.trim().length;
    document.getElementById("word-count").textContent = words + " words · " + chars + " chars";
  }
</script>
</body>
</html>
'''

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_path = image_path.replace('.', '_processed.')
    cv2.imwrite(processed_path, thresh)
    return processed_path

@app.route('/')
def root():
    return redirect('/gowrishankar')

@app.route('/gowrishankar')
def home():
    return render_template_string(HOME_PAGE)

@app.route('/gowrishankar/convert', methods=['POST'])
def convert():
    if 'image' not in request.files:
        return render_template_string(HOME_PAGE, error="No image uploaded.")
    file = request.files['image']
    if file.filename == '':
        return render_template_string(HOME_PAGE, error="No file selected.")
    image_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(image_path)
    try:
        processed_path = preprocess_image(image_path)
        img = Image.open(processed_path)
        text = pytesseract.image_to_string(img, config='--psm 6')
        if not text.strip():
            return render_template_string(HOME_PAGE, error="Could not read text. Try a clearer photo with good lighting.")
        timestamp = datetime.now().strftime('%d %B %Y, %I:%M %p')
        output_filename = f'notes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"NoteScribe — by Gowrishankar\n")
            f.write(f"Converted on: {timestamp}\n")
            f.write("=" * 40 + "\n\n")
            f.write(text)
        return render_template_string(RESULT_PAGE, text=text, filename=output_filename, timestamp=timestamp)
    except Exception as e:
        return render_template_string(HOME_PAGE, error=f"Error: {str(e)}")

@app.route('/gowrishankar/download/<filename>')
def download(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    print("\n  NoteScribe by Gowrishankar")
    print("  Open: http://127.0.0.1:5000/gowrishankar\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
