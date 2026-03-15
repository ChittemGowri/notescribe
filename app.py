import pytesseract
from PIL import Image
import cv2
import numpy as np
from flask import Flask, request, render_template_string, send_file
import os
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>NoteScribe — Handwriting to Digital Text</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --ink: #0f0e0c;
      --paper: #f7f4ee;
      --cream: #ede9e0;
      --accent: #c8501a;
      --accent-light: #f0d5c8;
      --muted: #7a7570;
      --border: #d6d0c6;
      --success-bg: #eef5ee;
      --success-border: #3a7a3a;
      --card-bg: #ffffff;
    }

    html { font-size: 16px; }

    body {
      font-family: 'DM Sans', sans-serif;
      background-color: var(--paper);
      color: var(--ink);
      min-height: 100vh;
      background-image:
        radial-gradient(circle at 15% 20%, rgba(200,80,26,0.04) 0%, transparent 50%),
        radial-gradient(circle at 85% 80%, rgba(200,80,26,0.04) 0%, transparent 50%);
    }

    /* ── Header ── */
    header {
      border-bottom: 1px solid var(--border);
      padding: 0 40px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 64px;
      background: rgba(247,244,238,0.85);
      backdrop-filter: blur(8px);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .logo {
      font-family: 'DM Serif Display', serif;
      font-size: 1.4rem;
      letter-spacing: -0.02em;
      color: var(--ink);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .logo-dot {
      width: 8px; height: 8px;
      background: var(--accent);
      border-radius: 50%;
      display: inline-block;
    }

    .badge {
      font-size: 0.72rem;
      font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
      border: 1px solid var(--accent-light);
      background: var(--accent-light);
      padding: 3px 10px;
      border-radius: 20px;
    }

    /* ── Hero ── */
    .hero {
      text-align: center;
      padding: 72px 20px 48px;
      max-width: 640px;
      margin: 0 auto;
    }

    .hero-tag {
      font-size: 0.75rem;
      font-weight: 500;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 16px;
    }

    .hero h1 {
      font-family: 'DM Serif Display', serif;
      font-size: clamp(2.2rem, 5vw, 3.2rem);
      line-height: 1.12;
      letter-spacing: -0.03em;
      color: var(--ink);
      margin-bottom: 18px;
    }

    .hero h1 em {
      font-style: italic;
      color: var(--accent);
    }

    .hero p {
      font-size: 1.05rem;
      font-weight: 300;
      color: var(--muted);
      line-height: 1.7;
      max-width: 480px;
      margin: 0 auto;
    }

    /* ── Main layout ── */
    .container {
      max-width: 900px;
      margin: 0 auto;
      padding: 0 24px 80px;
    }

    /* ── Upload card ── */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 40px;
      margin-bottom: 24px;
    }

    .upload-zone {
      border: 2px dashed var(--border);
      border-radius: 12px;
      padding: 52px 24px;
      text-align: center;
      transition: all 0.2s ease;
      cursor: pointer;
      position: relative;
      background: var(--paper);
    }

    .upload-zone:hover, .upload-zone.dragover {
      border-color: var(--accent);
      background: var(--accent-light);
    }

    .upload-zone input[type=file] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
      width: 100%;
      height: 100%;
    }

    .upload-icon {
      width: 48px; height: 48px;
      margin: 0 auto 16px;
      border: 1.5px solid var(--border);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: white;
    }

    .upload-icon svg { width: 22px; height: 22px; stroke: var(--accent); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }

    .upload-title {
      font-family: 'DM Serif Display', serif;
      font-size: 1.15rem;
      color: var(--ink);
      margin-bottom: 6px;
    }

    .upload-sub {
      font-size: 0.85rem;
      color: var(--muted);
      font-weight: 300;
    }

    #file-name {
      margin-top: 14px;
      font-size: 0.82rem;
      color: var(--accent);
      font-weight: 500;
      min-height: 18px;
    }

    /* ── Tips row ── */
    .tips {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-top: 24px;
    }

    .tip {
      background: var(--paper);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
    }

    .tip-label {
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 4px;
    }

    .tip p {
      font-size: 0.82rem;
      color: var(--muted);
      line-height: 1.5;
      font-weight: 300;
    }

    /* ── Button ── */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--ink);
      color: white;
      border: none;
      padding: 14px 32px;
      font-family: 'DM Sans', sans-serif;
      font-size: 0.95rem;
      font-weight: 500;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.18s ease;
      margin-top: 28px;
      letter-spacing: 0.01em;
    }

    .btn:hover { background: var(--accent); transform: translateY(-1px); }
    .btn:active { transform: translateY(0); }

    .btn svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

    /* ── Result card ── */
    .result-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      overflow: hidden;
      margin-bottom: 24px;
      animation: fadeUp 0.4s ease;
    }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(16px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .result-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 28px;
      border-bottom: 1px solid var(--border);
      background: var(--paper);
    }

    .result-title {
      font-family: 'DM Serif Display', serif;
      font-size: 1.1rem;
      color: var(--ink);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .result-title::before {
      content: '';
      width: 8px; height: 8px;
      background: var(--success-border);
      border-radius: 50%;
      display: inline-block;
    }

    .result-body {
      padding: 28px;
    }

    .text-output {
      font-family: 'DM Serif Display', serif;
      font-size: 1rem;
      line-height: 1.85;
      color: var(--ink);
      white-space: pre-wrap;
      background: var(--paper);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 24px;
      max-height: 360px;
      overflow-y: auto;
      min-height: 80px;
    }

    .text-output::-webkit-scrollbar { width: 4px; }
    .text-output::-webkit-scrollbar-track { background: transparent; }
    .text-output::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

    .result-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-top: 20px;
      flex-wrap: wrap;
    }

    .btn-download {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--accent);
      color: white;
      text-decoration: none;
      padding: 11px 24px;
      font-family: 'DM Sans', sans-serif;
      font-size: 0.88rem;
      font-weight: 500;
      border-radius: 8px;
      transition: all 0.18s ease;
      letter-spacing: 0.01em;
    }

    .btn-download:hover { background: #a8401a; transform: translateY(-1px); }
    .btn-download svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }

    .btn-copy {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: transparent;
      color: var(--ink);
      border: 1px solid var(--border);
      padding: 11px 20px;
      font-family: 'DM Sans', sans-serif;
      font-size: 0.88rem;
      font-weight: 400;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.18s ease;
    }

    .btn-copy:hover { border-color: var(--ink); background: var(--paper); }
    .btn-copy svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

    .word-count {
      margin-left: auto;
      font-size: 0.8rem;
      color: var(--muted);
      font-weight: 300;
    }

    /* ── Error ── */
    .error-card {
      background: #fff8f7;
      border: 1px solid #f5c6bc;
      border-radius: 12px;
      padding: 20px 24px;
      color: #8b2a14;
      font-size: 0.9rem;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      animation: fadeUp 0.3s ease;
    }

    .error-card svg { width: 18px; height: 18px; stroke: #c8501a; fill: none; stroke-width: 2; flex-shrink: 0; margin-top: 1px; }

    /* ── Footer ── */
    footer {
      text-align: center;
      padding: 32px;
      font-size: 0.78rem;
      color: var(--muted);
      border-top: 1px solid var(--border);
      letter-spacing: 0.03em;
    }

    /* ── Responsive ── */
    @media (max-width: 600px) {
      header { padding: 0 20px; }
      .card { padding: 24px 20px; }
      .tips { grid-template-columns: 1fr; }
      .hero { padding: 48px 20px 32px; }
      .word-count { margin-left: 0; }
    }
  </style>
</head>
<body>

<header>
  <div class="logo">
    <span class="logo-dot"></span>
    NoteScribe
  </div>
  <span class="badge">OCR Tool</span>
</header>

<div class="hero">
  <p class="hero-tag">Handwriting Recognition</p>
  <h1>Turn your notes into<br/><em>digital text</em></h1>
  <p>Upload a photo of any handwritten page. Get clean, searchable, downloadable text in seconds.</p>
</div>

<div class="container">

  {% if error %}
  <div class="error-card">
    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    <span>{{ error }}</span>
  </div>
  {% endif %}

  {% if text %}
  <div class="result-card">
    <div class="result-header">
      <span class="result-title">Conversion complete</span>
    </div>
    <div class="result-body">
      <div class="text-output" id="output-text">{{ text }}</div>
      <div class="result-actions">
        <a class="btn-download" href="/download/{{ filename }}">
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
  {% endif %}

  <div class="card">
    <form method="POST" enctype="multipart/form-data" action="/convert" id="upload-form">
      <div class="upload-zone" id="drop-zone">
        <input type="file" name="image" accept="image/*" id="file-input" onchange="updateFileName(this)"/>
        <div class="upload-icon">
          <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        </div>
        <p class="upload-title">Drop your image here</p>
        <p class="upload-sub">or click to browse — JPG, PNG, WEBP supported</p>
        <div id="file-name"></div>
      </div>

      <div class="tips">
        <div class="tip">
          <div class="tip-label">Lighting</div>
          <p>Shoot in natural daylight, avoid harsh shadows across the page.</p>
        </div>
        <div class="tip">
          <div class="tip-label">Angle</div>
          <p>Hold phone directly above the notebook, flat and parallel.</p>
        </div>
        <div class="tip">
          <div class="tip-label">Pen</div>
          <p>Dark ink on white paper gives the best recognition results.</p>
        </div>
      </div>

      <button type="submit" class="btn" id="submit-btn">
        <svg viewBox="0 0 24 24"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
        Convert to text
      </button>
    </form>
  </div>

</div>

<footer>
  NoteScribe &mdash; Built with Python, Flask &amp; Tesseract OCR &mdash; Runs fully offline
</footer>

<script>
  function updateFileName(input) {
    const el = document.getElementById('file-name');
    el.textContent = input.files[0] ? input.files[0].name : '';
  }

  const dropZone = document.getElementById('drop-zone');
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length) {
      document.getElementById('file-input').files = files;
      updateFileName(document.getElementById('file-input'));
    }
  });

  document.getElementById('upload-form').addEventListener('submit', () => {
    const btn = document.getElementById('submit-btn');
    btn.textContent = 'Converting...';
    btn.disabled = true;
  });

  function copyText() {
    const text = document.getElementById('output-text').innerText;
    navigator.clipboard.writeText(text).then(() => {
      const label = document.getElementById('copy-label');
      label.textContent = 'Copied!';
      setTimeout(() => label.textContent = 'Copy text', 2000);
    });
  }

  const outputEl = document.getElementById('output-text');
  if (outputEl) {
    const words = outputEl.innerText.trim().split(/\s+/).filter(Boolean).length;
    const chars = outputEl.innerText.trim().length;
    document.getElementById('word-count').textContent = words + ' words · ' + chars + ' characters';
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
def home():
    return render_template_string(HTML_PAGE)

@app.route('/convert', methods=['POST'])
def convert():
    if 'image' not in request.files:
        return render_template_string(HTML_PAGE, error="No image uploaded.")
    file = request.files['image']
    if file.filename == '':
        return render_template_string(HTML_PAGE, error="No file selected.")
    image_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(image_path)
    try:
        processed_path = preprocess_image(image_path)
        img = Image.open(processed_path)
        text = pytesseract.image_to_string(img, config='--psm 6')
        if not text.strip():
            return render_template_string(HTML_PAGE, error="Could not read text. Try a clearer photo with good lighting.")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'notes_{timestamp}.txt'
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Converted on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n")
            f.write("=" * 40 + "\n\n")
            f.write(text)
        return render_template_string(HTML_PAGE, text=text, filename=output_filename)
    except Exception as e:
        return render_template_string(HTML_PAGE, error=f"Error: {str(e)}")

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    print("App running at: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
