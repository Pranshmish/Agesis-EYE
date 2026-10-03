#!/usr/bin/env python3
"""
Agesis EYE - Complete Manual Builder (HTML & PDF Compiler)
Compiles all modular documentation chapters into a unified publication-grade
interactive single-page HTML document and an offline PDF manual.
"""

import os
import sys
import re
import subprocess
import markdown

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DOCS_DIR)

CHAPTERS = [
    ("README.md", "Executive Overview & Technology Curriculum"),
    ("01_system_architecture.md", "Chapter 1: System Architecture & End-to-End Integration"),
    ("02_embedded_systems_firmware.md", "Chapter 2: Embedded Systems & Firmware Engineering"),
    ("03_edge_ai_and_vision_pipeline.md", "Chapter 3: Edge AI & Real-Time Computer Vision Pipeline"),
    ("04_robotics_and_kinematics.md", "Chapter 4: Robotics, Kinematics & Visual Servoing"),
    ("05_physical_ai_and_digital_twin.md", "Chapter 5: Physical AI & 3D Kinematic Digital Twin"),
    ("06_ai_ml_engineering.md", "Chapter 6: AI/ML Engineering & Model Optimization"),
    ("07_hardware_assembly_and_wiring.md", "Chapter 7: Hardware Assembly, Wiring & Safety Protocols"),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agesis EYE: Complete Technical Reference & Engineering Manual</title>
  <style>
    :root {
      --primary: #d9232a;
      --primary-dark: #9b1419;
      --primary-light: #ff4d52;
      --bg: #0d1117;
      --surface: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --code-bg: #1f242c;
      --accent-blue: #58a6ff;
      --accent-green: #3fb950;
      --accent-yellow: #d29922;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.65;
      color: var(--text);
      background-color: var(--bg);
      display: flex;
    }

    /* Sidebar Table of Contents */
    #sidebar {
      width: 320px;
      height: 100vh;
      position: sticky;
      top: 0;
      background: var(--surface);
      border-right: 1px solid var(--border);
      padding: 24px 16px;
      overflow-y: auto;
      flex-shrink: 0;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }

    .brand-badge {
      background: var(--primary);
      color: #fff;
      font-weight: 800;
      font-size: 13px;
      padding: 4px 8px;
      border-radius: 4px;
      letter-spacing: 1px;
    }

    .brand-title {
      font-size: 16px;
      font-weight: 700;
      color: #fff;
    }

    .toc-title {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      margin-bottom: 12px;
    }

    .toc-list {
      list-style: none;
    }

    .toc-item {
      margin-bottom: 8px;
    }

    .toc-link {
      display: block;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 13px;
      padding: 6px 10px;
      border-radius: 6px;
      transition: all 0.15s ease;
      line-height: 1.4;
    }

    .toc-link:hover, .toc-link.active {
      color: #fff;
      background: rgba(217, 35, 42, 0.15);
      border-left: 3px solid var(--primary);
      padding-left: 12px;
    }

    .actions-bar {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 8px 14px;
      font-size: 12px;
      font-weight: 600;
      border-radius: 6px;
      text-decoration: none;
      cursor: pointer;
      border: 1px solid var(--border);
      transition: 0.15s ease;
    }

    .btn-primary {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary-dark);
    }
    .btn-primary:hover {
      background: var(--primary-light);
    }

    .btn-outline {
      background: transparent;
      color: var(--text);
    }
    .btn-outline:hover {
      background: rgba(255, 255, 255, 0.05);
    }

    /* Main Content Area */
    #content {
      flex: 1;
      max-width: 980px;
      padding: 48px 64px 120px;
      margin: 0 auto;
    }

    /* Cover / Hero */
    .hero {
      padding: 40px 0 60px;
      border-bottom: 2px solid var(--border);
      margin-bottom: 50px;
    }

    .hero-badge {
      display: inline-block;
      background: rgba(217, 35, 42, 0.15);
      color: var(--primary-light);
      border: 1px solid var(--primary);
      padding: 4px 12px;
      font-size: 12px;
      font-weight: 700;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 16px;
    }

    .hero h1 {
      font-size: 38px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #fff;
      margin-bottom: 14px;
      line-height: 1.2;
    }

    .hero p {
      font-size: 17px;
      color: var(--text-muted);
      max-width: 780px;
      line-height: 1.6;
    }

    .meta-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 24px;
    }

    .pill {
      background: var(--surface);
      border: 1px solid var(--border);
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
    }

    /* Markdown Elements Styling */
    h1, h2, h3, h4 {
      color: #fff;
      font-weight: 700;
      line-height: 1.3;
      margin-top: 36px;
      margin-bottom: 16px;
    }

    h1 {
      font-size: 28px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 10px;
      margin-top: 60px;
    }

    h2 {
      font-size: 22px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      padding-bottom: 6px;
    }

    h3 {
      font-size: 17px;
    }

    p {
      margin-bottom: 16px;
      color: #c9d1d9;
    }

    a {
      color: var(--accent-blue);
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }

    ul, ol {
      margin-bottom: 18px;
      padding-left: 28px;
      color: #c9d1d9;
    }

    li {
      margin-bottom: 6px;
    }

    /* Tables */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0 28px;
      background: var(--surface);
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border);
    }

    th, td {
      padding: 12px 16px;
      text-align: left;
      font-size: 13.5px;
      border-bottom: 1px solid var(--border);
    }

    th {
      background: #1c2128;
      color: #fff;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.5px;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover td {
      background: rgba(255, 255, 255, 0.02);
    }

    /* Code & Fenced Blocks */
    pre {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      margin: 18px 0 24px;
      font-family: "JetBrains Mono", Consolas, Monaco, monospace;
      font-size: 13px;
      line-height: 1.5;
      color: #f0f6fc;
    }

    code {
      font-family: "JetBrains Mono", Consolas, Monaco, monospace;
      font-size: 12.5px;
      background: rgba(110, 118, 129, 0.2);
      padding: 2px 6px;
      border-radius: 4px;
      color: #f0883e;
    }

    pre code {
      background: transparent;
      padding: 0;
      color: inherit;
    }

    /* Blockquotes / Callouts */
    blockquote {
      background: rgba(56, 139, 253, 0.08);
      border-left: 4px solid var(--accent-blue);
      padding: 14px 20px;
      border-radius: 0 8px 8px 0;
      margin: 20px 0 24px;
      color: #c9d1d9;
    }

    blockquote strong {
      color: #fff;
    }

    .chapter-divider {
      margin: 70px 0 40px;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--border), var(--primary), var(--border), transparent);
    }

    /* Diagram Card Containers */
    .diagram-card {
      background: #10151d;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0 28px;
      font-family: "JetBrains Mono", monospace;
      font-size: 12.5px;
      overflow-x: auto;
      color: #79c0ff;
      line-height: 1.4;
    }

    /* PRINT STYLES FOR CRISP PDF GENERATION */
    @media print {
      body {
        background: #fff !important;
        color: #111 !important;
        display: block;
      }
      #sidebar {
        display: none !important;
      }
      #content {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
      }
      h1, h2, h3, h4 {
        color: #000 !important;
      }
      h1 {
        page-break-before: always;
        margin-top: 30px;
      }
      .hero {
        page-break-after: always;
        padding-top: 100px;
        text-align: center;
      }
      .hero p {
        color: #444 !important;
        margin: 0 auto;
      }
      .meta-pills {
        justify-content: center;
      }
      .pill {
        border-color: #ccc !important;
        color: #333 !important;
        background: #f5f5f5 !important;
      }
      p, li {
        color: #222 !important;
      }
      table {
        border-color: #ddd !important;
        background: #fff !important;
      }
      th {
        background: #f0f0f0 !important;
        color: #000 !important;
        border-color: #ccc !important;
      }
      td {
        border-color: #eee !important;
        color: #222 !important;
      }
      pre {
        background: #f8f8f8 !important;
        color: #111 !important;
        border-color: #ddd !important;
        page-break-inside: avoid;
      }
      code {
        color: #b91c1c !important;
        background: #f0f0f0 !important;
      }
      pre code {
        color: #111 !important;
      }
      blockquote {
        background: #f0f7ff !important;
        border-left-color: #0366d6 !important;
        color: #222 !important;
      }
      .chapter-divider {
        display: none;
      }
      .diagram-card {
        background: #fafafa !important;
        border-color: #ccc !important;
        color: #0550ae !important;
      }
    }
  </style>
</head>
<body>

  <!-- Sidebar Navigation -->
  <aside id="sidebar">
    <div class="brand">
      <span class="brand-badge">AGESIS</span>
      <span class="brand-title">EYE Manual</span>
    </div>

    <div class="toc-title">Table of Contents</div>
    <ul class="toc-list">
      __TOC_ITEMS__
    </ul>

    <div class="actions-bar">
      <a href="Agesis_EYE_Complete_Manual.pdf" download class="btn btn-primary">
        📥 Download PDF Manual
      </a>
      <a href="javascript:window.print()" class="btn btn-outline">
        🖨️ Print Document
      </a>
    </div>
  </aside>

  <!-- Main Content Area -->
  <main id="content">
    <div class="hero">
      <span class="hero-badge">Engineering Reference Manual</span>
      <h1>AGESIS EYE</h1>
      <h2 style="margin-top: 0; font-weight: 500; font-size: 22px; color: var(--primary-light);">
        Autonomous Vision, Tactical Tracking &amp; Closed-Loop Pan-Tilt Targeting Ground Station
      </h2>
      <p>
        A comprehensive engineering manual covering Edge AI, Robotics, Physical AI, Machine Learning, and Embedded Firmware for autonomous tracking systems.
      </p>

      <div class="meta-pills">
        <div class="pill">Edge AI: ONNX 45+ FPS</div>
        <div class="pill">Robotics: 2-DoF IBVS Kinematics</div>
        <div class="pill">Embedded: ESP32-CAM 14-bit LEDC</div>
        <div class="pill">Power: 5V 2A Slew-Rate Protected</div>
        <div class="pill">Digital Twin: 3D Perspective Canvas</div>
      </div>
    </div>

    __BODY_CONTENT__
  </main>

  <script>
    // Highlight active section on scroll
    window.addEventListener('scroll', () => {
      const headings = document.querySelectorAll('h1[id]');
      let current = '';
      headings.forEach(h => {
        const top = h.getBoundingClientRect().top;
        if (top <= 120) current = h.id;
      });
      document.querySelectorAll('.toc-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
          link.classList.add('active');
        }
      });
    });
  </script>
</body>
</html>
"""

def clean_mermaid_to_html(content: str) -> str:
    """Converts Mermaid codeblocks into clean readable diagram pre elements."""
    def repl(m):
        raw = m.group(1).strip()
        return f'<div class="diagram-card"><pre>{raw}</pre></div>'
    return re.sub(r'```mermaid\s+(.*?)\s+```', repl, content, flags=re.DOTALL)

def build():
    print("[*] Compiling Agesis EYE Documentation Suite...")
    
    md_parser = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'toc',
        'attr_list',
        'nl2br'
    ])
    
    toc_items = []
    body_parts = []
    
    for idx, (filename, title) in enumerate(CHAPTERS):
        filepath = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[!] Warning: Missing file {filepath}")
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        # Clean local markdown file links to in-page anchor links
        raw_text = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+/(0[1-7]_[^\)]+\.md)\)', r'[\1](#\2)', raw_text)
        raw_text = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+/README\.md\)', r'[\1](#overview)', raw_text)
        
        # Give unique anchor IDs
        chapter_id = "overview" if "README" in filename else filename.replace(".md", "")
        
        # Replace mermaid blocks with diagram cards
        processed_text = clean_mermaid_to_html(raw_text)
        
        # Convert to HTML
        html_segment = md_parser.convert(processed_text)
        
        # Ensure the first h1 has the chapter anchor ID
        html_segment = re.sub(r'<h1([^>]*)>', f'<h1 id="{chapter_id}"\\1>', html_segment, count=1)
        
        toc_items.append(
            f'<li class="toc-item"><a class="toc-link" href="#{chapter_id}">{title}</a></li>'
        )
        
        if idx > 0:
            body_parts.append('<div class="chapter-divider"></div>')
        body_parts.append(f'<section class="chapter-section" id="section-{chapter_id}">\n{html_segment}\n</section>')

    full_html = HTML_TEMPLATE.replace("__TOC_ITEMS__", "\n      ".join(toc_items))
    full_html = full_html.replace("__BODY_CONTENT__", "\n".join(body_parts))
    
    out_html_path = os.path.join(DOCS_DIR, "index.html")
    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[+] Unified HTML Manual generated: {out_html_path} ({len(full_html):,} bytes)")

    # Generate PDF using Headless Edge or Chrome
    pdf_out_path = os.path.join(DOCS_DIR, "Agesis_EYE_Complete_Manual.pdf")
    browser_candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    browser_exe = next((b for b in browser_candidates if os.path.exists(b)), None)
    
    if browser_exe:
        print(f"[*] Rendering high-resolution PDF via: {browser_exe}")
        file_url = f"file:///{out_html_path.replace(os.sep, '/')}"
        cmd = [
            browser_exe,
            "--headless",
            "--disable-gpu",
            "--run-all-compositor-stages-before-draw",
            f"--print-to-pdf={pdf_out_path}",
            "--no-pdf-header-footer",
            file_url
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
            if os.path.exists(pdf_out_path) and os.path.getsize(pdf_out_path) > 1000:
                print(f"[+] PDF Manual successfully compiled: {pdf_out_path} ({os.path.getsize(pdf_out_path):,} bytes)")
            else:
                print(f"[!] PDF generation failed or empty. Stderr: {res.stderr.decode()}")
        except Exception as e:
            print(f"[!] Subprocess error rendering PDF: {e}")
    else:
        print("[!] No compatible browser executable found for headless PDF printing.")

if __name__ == "__main__":
    build()
