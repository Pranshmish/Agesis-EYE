#!/usr/bin/env python3
r"""
Agesis EYE - Professional Technical Reference Manual & Engineering Whitepaper Generator
Theme: Pure Pitch Black (#030305) & Bloody Red (#ff0f3d) with Translucent Glassmorphism.
Flowcharts: High-Impact Glowing Neon Pink (#ff2a85) & Electric Yellow (#ffd600) Vector SVGs.
Formulas: Crystal-Clear Mathematical Formulations with Intuitive Parameter Breakdowns & Step-by-Step Examples.
PDF Mode: Clean, High-Contrast Pure White (#ffffff) Background with Crisp Typography.
Rules: ZERO emojis, ZERO raw code blocks, strictly rigorous engineering content.
"""

import os
import sys
import subprocess

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agesis EYE: Engineering Reference Manual & Technical Whitepaper</title>
  
  <!-- Modern Technical Typography -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  
  <!-- KaTeX Mathematical Formatting Engine -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

  <style>
    /* =========================================================
       THEME VARIABLES: PITCH BLACK & BLOODY RED GLASSMORPHISM
       ========================================================= */
    :root {
      --bg: #030305;
      --bg-gradient: radial-gradient(circle at 10% 5%, rgba(139, 0, 24, 0.22) 0%, transparent 48%),
                     radial-gradient(circle at 90% 90%, rgba(255, 15, 61, 0.12) 0%, transparent 45%),
                     #030305;
      
      /* Glassmorphic Surfaces */
      --glass-surface: rgba(16, 12, 18, 0.72);
      --glass-surface-card: rgba(22, 14, 26, 0.65);
      --glass-surface-hover: rgba(36, 20, 38, 0.85);
      --glass-border: rgba(255, 15, 61, 0.25);
      --glass-border-glow: rgba(255, 15, 61, 0.55);
      --glass-shadow: 0 12px 40px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.08);

      /* Accent Palettes */
      --crimson: #ff0f3d;
      --crimson-dark: #8b0018;
      --crimson-glow: 0 0 16px rgba(255, 15, 61, 0.45);
      
      --neon-pink: #ff2a85;
      --neon-pink-glow: 0 0 14px rgba(255, 42, 133, 0.55);
      
      --neon-yellow: #ffd600;
      --neon-yellow-glow: 0 0 14px rgba(255, 214, 0, 0.55);
      
      --neon-cyan: #00f0ff;
      --neon-cyan-glow: 0 0 12px rgba(0, 240, 255, 0.4);

      /* Typography Colors */
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg-gradient);
      color: var(--text-main);
      line-height: 1.72;
      display: flex;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Fixed Glassmorphic Navigation Sidebar */
    #sidebar {
      width: 320px;
      height: 100vh;
      position: sticky;
      top: 0;
      background: rgba(8, 6, 10, 0.85);
      backdrop-filter: blur(28px);
      -webkit-backdrop-filter: blur(28px);
      border-right: 1px solid var(--glass-border);
      padding: 32px 20px;
      overflow-y: auto;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      gap: 22px;
      box-shadow: 6px 0 28px rgba(0, 0, 0, 0.7);
      z-index: 100;
    }

    #sidebar::-webkit-scrollbar {
      width: 4px;
    }
    #sidebar::-webkit-scrollbar-thumb {
      background: var(--glass-border);
      border-radius: 4px;
    }

    .brand-box {
      border-left: 3px solid var(--crimson);
      padding-left: 14px;
    }

    .brand-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 2px;
      color: var(--crimson);
      text-transform: uppercase;
      text-shadow: var(--crimson-glow);
    }

    .brand-title {
      font-size: 20px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.5px;
      margin-top: 3px;
    }

    .brand-subtitle {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 3px;
      letter-spacing: 0.3px;
    }

    .toc-title {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 1.5px;
      color: var(--neon-yellow);
      text-transform: uppercase;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--glass-border);
    }

    .toc-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .toc-item a {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 13px;
      font-weight: 500;
      border-radius: 6px;
      transition: all 0.2s ease;
      border: 1px solid transparent;
    }

    .toc-item a:hover {
      color: #ffffff;
      background: rgba(255, 15, 61, 0.12);
      border-color: rgba(255, 15, 61, 0.3);
      padding-left: 16px;
    }

    .toc-item a.active {
      color: #ffffff;
      background: rgba(255, 15, 61, 0.2);
      border-color: var(--crimson);
      box-shadow: 0 0 14px rgba(255, 15, 61, 0.3);
      font-weight: 700;
    }

    .toc-item .num {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: var(--neon-pink);
      font-weight: 700;
    }

    .sidebar-footer {
      margin-top: auto;
      padding-top: 16px;
      border-top: 1px solid var(--glass-border);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .pdf-download-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 12px 14px;
      background: linear-gradient(135deg, var(--crimson-dark), var(--crimson));
      color: #ffffff;
      text-decoration: none;
      border-radius: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 1px;
      text-transform: uppercase;
      box-shadow: 0 4px 18px rgba(255, 15, 61, 0.45);
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: all 0.25s ease;
      cursor: pointer;
    }

    .pdf-download-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 24px rgba(255, 15, 61, 0.7);
      background: linear-gradient(135deg, #a50020, #ff1a48);
    }

    /* Main Document Area */
    #main-content {
      flex: 1;
      padding: 48px 56px 96px 56px;
      max-width: 1060px;
      margin: 0 auto;
    }

    /* Document Header */
    .doc-header {
      padding-bottom: 36px;
      border-bottom: 1px solid var(--glass-border);
      margin-bottom: 48px;
    }

    .doc-classification {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 2px;
      text-transform: uppercase;
      padding: 5px 12px;
      background: rgba(255, 15, 61, 0.15);
      border: 1px solid var(--crimson);
      color: var(--crimson);
      border-radius: 4px;
      margin-bottom: 18px;
      box-shadow: 0 0 12px rgba(255, 15, 61, 0.25);
    }

    .doc-title {
      font-size: 40px;
      font-weight: 900;
      line-height: 1.15;
      letter-spacing: -1px;
      color: #ffffff;
      margin-bottom: 14px;
      text-shadow: 0 2px 20px rgba(0, 0, 0, 0.8);
    }

    .doc-subtitle {
      font-size: 18px;
      color: var(--text-muted);
      font-weight: 400;
      line-height: 1.5;
      margin-bottom: 24px;
    }

    .doc-meta-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      padding: 14px 20px;
      background: var(--glass-surface-card);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--glass-border);
      border-radius: 8px;
      font-size: 12px;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }

    .meta-item strong {
      color: #ffffff;
    }

    .domain-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 20px;
    }

    .domain-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      padding: 5px 12px;
      background: rgba(255, 42, 133, 0.12);
      border: 1px solid rgba(255, 42, 133, 0.35);
      color: var(--neon-pink);
      border-radius: 20px;
      letter-spacing: 0.5px;
    }

    /* Section Typography */
    section {
      margin-bottom: 64px;
      scroll-margin-top: 30px;
    }

    .chapter-heading {
      display: flex;
      align-items: center;
      gap: 14px;
      font-size: 26px;
      font-weight: 900;
      letter-spacing: -0.5px;
      color: #ffffff;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 2px solid var(--glass-border);
    }

    .chapter-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 800;
      color: #ffffff;
      background: var(--crimson);
      padding: 4px 10px;
      border-radius: 4px;
      letter-spacing: 1px;
      box-shadow: var(--crimson-glow);
    }

    .section-title {
      font-size: 19px;
      font-weight: 800;
      color: #ffffff;
      margin: 32px 0 14px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-title::before {
      content: '';
      display: inline-block;
      width: 4px;
      height: 18px;
      background: var(--neon-yellow);
      border-radius: 2px;
      box-shadow: var(--neon-yellow-glow);
    }

    p {
      color: #cbd5e1;
      font-size: 15px;
      margin-bottom: 18px;
      line-height: 1.75;
    }

    p strong {
      color: #ffffff;
      font-weight: 700;
    }

    /* Glassmorphic KPI Cards Grid */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin: 26px 0;
    }

    .glass-card {
      background: var(--glass-surface-card);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid var(--glass-border);
      border-radius: 10px;
      padding: 22px 20px;
      box-shadow: var(--glass-shadow);
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }

    .glass-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--crimson), transparent);
    }

    .glass-card:hover {
      background: var(--glass-surface-hover);
      border-color: var(--glass-border-glow);
      transform: translateY(-2px);
      box-shadow: 0 16px 45px rgba(0, 0, 0, 0.8), 0 0 20px rgba(255, 15, 61, 0.15);
    }

    .kpi-label {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      color: var(--neon-yellow);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 8px;
    }

    .kpi-value {
      font-size: 28px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.5px;
      margin-bottom: 6px;
      text-shadow: 0 0 12px rgba(255, 255, 255, 0.3);
    }

    .kpi-desc {
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.5;
    }

    /* Glassmorphic Table Styling */
    .table-container {
      background: var(--glass-surface);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid var(--glass-border);
      border-radius: 10px;
      overflow: hidden;
      margin: 28px 0;
      box-shadow: var(--glass-shadow);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    th {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      color: #ffffff;
      background: rgba(30, 16, 32, 0.85);
      padding: 16px 20px;
      border-bottom: 1px solid var(--glass-border);
    }

    td {
      padding: 14px 20px;
      font-size: 14px;
      color: #e2e8f0;
      border-bottom: 1px solid rgba(255, 15, 61, 0.1);
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover td {
      background: rgba(255, 15, 61, 0.05);
    }

    /* Diagram Panels: High-Tech Glowing SVGs */
    .diagram-panel {
      background: rgba(8, 6, 12, 0.85);
      backdrop-filter: blur(28px);
      -webkit-backdrop-filter: blur(28px);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      padding: 28px 24px;
      margin: 32px 0;
      box-shadow: 0 16px 50px rgba(0, 0, 0, 0.8), inset 0 0 30px rgba(255, 15, 61, 0.04);
    }

    .diagram-caption {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 1.5px;
      color: var(--neon-yellow);
      text-transform: uppercase;
      text-align: center;
      margin-top: 20px;
      border-top: 1px solid var(--glass-border);
      padding-top: 14px;
      text-shadow: var(--neon-yellow-glow);
    }

    svg text {
      font-family: 'Inter', -apple-system, sans-serif;
    }

    svg .mono {
      font-family: 'JetBrains Mono', monospace;
    }

    /* Mathematical Formula Cards: Crystal-Clear Formulation */
    .math-block {
      background: var(--glass-surface-card);
      backdrop-filter: blur(26px);
      -webkit-backdrop-filter: blur(26px);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      padding: 26px 24px;
      margin: 28px 0;
      box-shadow: var(--glass-shadow);
      position: relative;
    }

    .math-header {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 1px;
      color: var(--neon-pink);
      text-transform: uppercase;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .math-header::before {
      content: 'EQUATION';
      font-size: 9px;
      background: var(--neon-pink);
      color: #000;
      padding: 2px 6px;
      border-radius: 3px;
      font-weight: 900;
    }

    .math-display-box {
      background: rgba(10, 8, 14, 0.9);
      border: 1px solid rgba(255, 42, 133, 0.3);
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      margin-bottom: 18px;
      box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.6), 0 0 15px rgba(255, 42, 133, 0.08);
    }

    .katex-display {
      margin: 0 !important;
      font-size: 1.25em !important;
      color: #ffffff !important;
    }

    /* Step-by-Step Parameter & Meaning Grid */
    .math-params-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      margin-top: 14px;
    }

    .param-item {
      background: rgba(14, 10, 18, 0.6);
      border-left: 3px solid var(--neon-yellow);
      padding: 10px 14px;
      border-radius: 0 6px 6px 0;
      font-size: 13px;
      color: #cbd5e1;
      border-top: 1px solid rgba(255, 255, 255, 0.04);
      border-right: 1px solid rgba(255, 255, 255, 0.04);
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }

    .param-name {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
      color: var(--neon-yellow);
      display: block;
      margin-bottom: 3px;
    }

    .math-walkthrough {
      background: rgba(255, 15, 61, 0.08);
      border: 1px solid rgba(255, 15, 61, 0.25);
      border-radius: 6px;
      padding: 12px 16px;
      margin-top: 14px;
      font-size: 13px;
      color: #e2e8f0;
      line-height: 1.6;
    }

    .math-walkthrough strong {
      color: #ffffff;
    }

    /* Callout Panels */
    .callout {
      border-radius: 8px;
      padding: 20px 22px;
      margin: 26px 0;
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      box-shadow: var(--glass-shadow);
    }

    .callout-hazard {
      background: rgba(36, 12, 18, 0.7);
      border: 1px solid var(--crimson);
      border-left: 5px solid var(--crimson);
    }

    .callout-hazard .callout-title {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 1px;
      color: var(--crimson);
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    .callout-theorem {
      background: rgba(30, 16, 34, 0.7);
      border: 1px solid var(--neon-pink);
      border-left: 5px solid var(--neon-pink);
    }

    .callout-theorem .callout-title {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 1px;
      color: var(--neon-pink);
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    /* =========================================================
       PRINT / PDF STYLES: CLEAN HIGH-CONTRAST PURE WHITE
       ========================================================= */
    @media print {
      @page {
        margin: 12mm 14mm;
        size: A4 portrait;
        background: #ffffff !important;
      }

      html, body {
        background: #ffffff !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        display: block !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
      }

      #sidebar {
        display: none !important;
      }

      #main-content {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
      }

      .doc-header {
        border-bottom: 2px solid #e2e8f0 !important;
        padding-bottom: 24px !important;
        margin-bottom: 30px !important;
      }

      .doc-classification {
        background: #fee2e2 !important;
        color: #991b1b !important;
        border: 1px solid #f87171 !important;
        box-shadow: none !important;
      }

      .doc-title {
        color: #0f172a !important;
        font-size: 28px !important;
        text-shadow: none !important;
      }

      .doc-subtitle {
        color: #475569 !important;
        font-size: 14px !important;
      }

      .doc-meta-bar {
        background: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        color: #475569 !important;
      }

      .doc-meta-bar strong {
        color: #0f172a !important;
      }

      .domain-pill {
        background: #f1f5f9 !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
      }

      .chapter-heading {
        color: #0f172a !important;
        border-bottom: 2px solid #94a3b8 !important;
        font-size: 20px !important;
        page-break-after: avoid;
        break-after: avoid;
        margin-top: 36px !important;
      }

      .chapter-badge {
        background: #991b1b !important;
        color: #ffffff !important;
        box-shadow: none !important;
      }

      .section-title {
        color: #0f172a !important;
        font-size: 16px !important;
        page-break-after: avoid;
      }

      .section-title::before {
        background: #b91c1c !important;
        box-shadow: none !important;
      }

      p {
        color: #1e293b !important;
      }

      p strong {
        color: #0f172a !important;
      }

      .glass-card, .table-container, .diagram-panel, .math-block, .callout {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        page-break-inside: avoid;
        break-inside: avoid;
      }

      .kpi-label {
        color: #991b1b !important;
      }

      .kpi-value {
        color: #0f172a !important;
        text-shadow: none !important;
      }

      .kpi-desc {
        color: #475569 !important;
      }

      .math-display-box {
        background: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
      }

      .katex-display {
        color: #0f172a !important;
      }

      .param-item {
        background: #ffffff !important;
        border-left: 3px solid #b91c1c !important;
        border-top: 1px solid #e2e8f0 !important;
        border-right: 1px solid #e2e8f0 !important;
        border-bottom: 1px solid #e2e8f0 !important;
        color: #334155 !important;
      }

      .param-name {
        color: #b91c1c !important;
      }

      .math-walkthrough {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
        color: #334155 !important;
      }

      .callout-hazard {
        background: #fff5f5 !important;
        border-color: #fca5a5 !important;
        border-left: 5px solid #b91c1c !important;
      }

      .callout-hazard .callout-title {
        color: #991b1b !important;
      }

      .callout-theorem {
        background: #fdf2f8 !important;
        border-color: #fbcfe8 !important;
        border-left: 5px solid #be185d !important;
      }

      .callout-theorem .callout-title {
        color: #be185d !important;
      }

      th {
        background: #f1f5f9 !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
      }

      td {
        color: #1e293b !important;
        border-color: #e2e8f0 !important;
      }

      .diagram-caption {
        color: #0f172a !important;
        border-color: #e2e8f0 !important;
        text-shadow: none !important;
      }

      /* Invert SVG colors for crisp white PDF printing */
      .diagram-panel svg rect[fill^="rgba(16"],
      .diagram-panel svg rect[fill^="rgba(12"],
      .diagram-panel svg rect[fill^="rgba(8"] {
        fill: #f8fafc !important;
        stroke: #94a3b8 !important;
      }

      .diagram-panel svg text {
        fill: #0f172a !important;
      }

      .diagram-panel svg text.mono {
        fill: #334155 !important;
      }
    }
  </style>
</head>
<body>

  <!-- Sticky Glassmorphic Sidebar -->
  <aside id="sidebar">
    <div class="brand-box">
      <div class="brand-tag">Agesis Aerospace</div>
      <div class="brand-title">Agesis EYE</div>
      <div class="brand-subtitle">Autonomous Turret Tracking System</div>
    </div>

    <div class="toc-title">Documentation Contents</div>
    <ul class="toc-list">
      <li class="toc-item"><a href="#executive" class="active"><span class="num">00</span> Executive Overview</a></li>
      <li class="toc-item"><a href="#architecture"><span class="num">01</span> System Architecture</a></li>
      <li class="toc-item"><a href="#embedded"><span class="num">02</span> Embedded Systems &amp; PWM</a></li>
      <li class="toc-item"><a href="#edge-ai"><span class="num">03</span> Edge AI Vision Pipeline</a></li>
      <li class="toc-item"><a href="#robotics"><span class="num">04</span> Robotics &amp; Kinematics</a></li>
      <li class="toc-item"><a href="#physical-ai"><span class="num">05</span> Physical AI &amp; Digital Twin</a></li>
      <li class="toc-item"><a href="#ai-ml"><span class="num">06</span> Neural Loss Formulation</a></li>
      <li class="toc-item"><a href="#safety"><span class="num">07</span> Assembly &amp; Safety Protocols</a></li>
    </ul>

    <div class="sidebar-footer">
      <a href="Agesis_EYE_Complete_Manual.pdf" download class="pdf-download-btn">
        Save PDF Document
      </a>
      <div style="font-size: 11px; color: var(--text-dim); text-align: center; font-family: 'JetBrains Mono', monospace;">
        CONFIDENTIAL &bull; REV 3.2.0
      </div>
    </div>
  </aside>

  <!-- Main Technical Whitepaper Document -->
  <main id="main-content">

    <!-- Document Header -->
    <header class="doc-header" id="executive">
      <div class="doc-classification">Engineering Specification &bull; Distribution Class A</div>
      <h1 class="doc-title">Agesis EYE: Closed-Loop Optical Turret Tracking System</h1>
      <p class="doc-subtitle">
        Comprehensive Technical Reference Manual Covering Embedded Firmware, 14-Bit Hardware PWM Timers, Slew-Rate Current Safeguards, Edge Neural Inference, Image-Based Visual Servoing Invariance, and Real-Time 3D Digital Twin Simulation.
      </p>

      <div class="doc-meta-bar">
        <div class="meta-item">Document: <strong>ENG-AGE-2026-V3</strong></div>
        <div class="meta-item">Revision: <strong>3.2.0-STABLE</strong></div>
        <div class="meta-item">Classification: <strong>Technical Reference</strong></div>
        <div class="meta-item">Power Envelope: <strong>5.0V DC / 2.0A Regulated</strong></div>
      </div>

      <div class="domain-pills">
        <span class="domain-pill">Edge AI / ONNX Runtime</span>
        <span class="domain-pill">Robotics Kinematics</span>
        <span class="domain-pill">Physical AI Embodiment</span>
        <span class="domain-pill">Computer Vision</span>
        <span class="domain-pill">Embedded Micro-Actuation</span>
      </div>
    </header>

    <!-- Executive Overview -->
    <section>
      <h2 class="section-title">Executive Summary</h2>
      <p>
        <strong>Agesis EYE</strong> is an autonomous optical targeting ground station designed to eliminate the severe latency bottlenecks inherent in traditional cloud-tethered tracking architectures. By tightly integrating edge microcontrollers, localized neural vision inference, and closed-loop visual servoing kinematics, Agesis EYE achieves deterministic interception trajectories at sub-50 millisecond total system latency.
      </p>

      <div class="kpi-grid">
        <div class="glass-card">
          <div class="kpi-label">Latency Envelope</div>
          <div class="kpi-value">&le; 48.7 ms</div>
          <div class="kpi-desc">Cumulative photon-to-actuation response time across camera, Wi-Fi, and motor.</div>
        </div>
        <div class="glass-card">
          <div class="kpi-label">Vision Throughput</div>
          <div class="kpi-value">45+ FPS</div>
          <div class="kpi-desc">Quantized single-stage neural inference running on localized CPU SIMD cores.</div>
        </div>
        <div class="glass-card">
          <div class="kpi-label">Actuation Precision</div>
          <div class="kpi-value">&plusmn; 0.0135&deg;</div>
          <div class="kpi-desc">14-bit hardware timer resolution across both Pan and Tilt positioning axes.</div>
        </div>
      </div>
    </section>

    <!-- Section 1: Architecture -->
    <section id="architecture">
      <h1 class="chapter-heading"><span class="chapter-badge">SEC 01</span> System Architecture &amp; Integration</h1>
      
      <p>
        The Agesis EYE architecture cleanly decouples responsibilities across three physical and computational domains: the Edge Sensor/Actuator Node, the High-Speed Network Fabric, and the Ground Command &amp; Inference Station.
      </p>

      <!-- SVG Architecture Diagram: Glowing Pink, Electric Yellow & Blood Red -->
      <div class="diagram-panel">
        <svg viewBox="0 0 880 340" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <filter id="glow-pink" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <filter id="glow-yellow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <filter id="glow-red" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          <!-- TIER 1: Edge Node -->
          <rect x="20" y="20" width="250" height="300" rx="10" fill="rgba(16, 12, 18, 0.75)" stroke="#ff0f3d" stroke-width="1.8" filter="url(#glow-red)"/>
          <text x="35" y="48" fill="#ff0f3d" font-size="12" font-weight="800" class="mono">TIER 1: EDGE SENSOR NODE</text>
          
          <rect x="35" y="70" width="220" height="48" rx="6" fill="rgba(255, 42, 133, 0.15)" stroke="#ff2a85" stroke-width="1.5" filter="url(#glow-pink)"/>
          <text x="50" y="94" fill="#fff" font-size="12" font-weight="700">OV2640 Optical Sensor</text>
          <text x="50" y="108" fill="#ff2a85" font-size="10" class="mono">QVGA 320x240 @ 30 FPS</text>

          <rect x="35" y="130" width="220" height="68" rx="6" fill="rgba(255, 214, 0, 0.12)" stroke="#ffd600" stroke-width="1.5" filter="url(#glow-yellow)"/>
          <text x="50" y="154" fill="#fff" font-size="12" font-weight="700">ESP32-CAM Dual-Core MCU</text>
          <text x="50" y="170" fill="#ffd600" font-size="10" class="mono">LEDC 14-Bit PWM Timers</text>
          <text x="50" y="184" fill="#ff2a85" font-size="10" class="mono">50Hz S-Curve Slew Limiter</text>

          <rect x="35" y="210" width="220" height="90" rx="6" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d" stroke-width="1.5"/>
          <text x="50" y="234" fill="#fff" font-size="12" font-weight="700">Actuation &amp; Weapon Emitter</text>
          <text x="50" y="252" fill="#ffd600" font-size="10" class="mono">Pan SG90 (IO12) &bull; Tilt SG90 (IO13)</text>
          <text x="50" y="268" fill="#ff2a85" font-size="10" class="mono">Laser Diode Trigger (IO14)</text>

          <!-- Middle Network Bridge -->
          <rect x="310" y="60" width="260" height="220" rx="10" fill="rgba(12, 10, 16, 0.85)" stroke="#ffd600" stroke-dasharray="5 5" stroke-width="1.5"/>
          <text x="330" y="90" fill="#ffd600" font-size="11" font-weight="800" class="mono" filter="url(#glow-yellow)">TIER 2: NETWORK FABRIC</text>

          <!-- Arrows & Pipes -->
          <path d="M 255 94 L 330 120" stroke="#ff2a85" stroke-width="2.5" fill="none" filter="url(#glow-pink)"/>
          <rect x="330" y="105" width="220" height="36" rx="6" fill="rgba(255, 42, 133, 0.2)" stroke="#ff2a85" stroke-width="1.2"/>
          <text x="345" y="127" fill="#ff2a85" font-size="11" font-weight="700" class="mono">Port 81: MJPEG Video Stream</text>

          <path d="M 610 215 L 255 165" stroke="#ffd600" stroke-width="2.5" fill="none" filter="url(#glow-yellow)"/>
          <rect x="330" y="175" width="220" height="36" rx="6" fill="rgba(255, 214, 0, 0.18)" stroke="#ffd600" stroke-width="1.2"/>
          <text x="345" y="197" fill="#ffd600" font-size="11" font-weight="700" class="mono">Port 8888: Sub-ms UDP Commands</text>

          <!-- Right Ground Station -->
          <rect x="610" y="20" width="250" height="300" rx="10" fill="rgba(16, 12, 18, 0.75)" stroke="#ff0f3d" stroke-width="1.8" filter="url(#glow-red)"/>
          <text x="625" y="48" fill="#ff0f3d" font-size="12" font-weight="800" class="mono">TIER 3: GROUND COMMAND AI</text>

          <rect x="625" y="70" width="220" height="52" rx="6" fill="rgba(255, 42, 133, 0.15)" stroke="#ff2a85" stroke-width="1.5"/>
          <text x="640" y="92" fill="#fff" font-size="12" font-weight="700">Zero-Lag Ingestion Daemon</text>
          <text x="640" y="108" fill="#ff2a85" font-size="10" class="mono">Buffer-Draining Thread (&lt;2ms)</text>

          <rect x="625" y="132" width="220" height="52" rx="6" fill="rgba(255, 214, 0, 0.15)" stroke="#ffd600" stroke-width="1.5"/>
          <text x="640" y="154" fill="#fff" font-size="12" font-weight="700">ONNX Edge Vision Core</text>
          <text x="640" y="170" fill="#ffd600" font-size="10" class="mono">agesis06.onnx (45+ FPS CPU)</text>

          <rect x="625" y="194" width="220" height="52" rx="6" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d" stroke-width="1.5"/>
          <text x="640" y="216" fill="#fff" font-size="12" font-weight="700">Kinematics &amp; Safety Master</text>
          <text x="640" y="232" fill="#ffd600" font-size="10" class="mono">d-Invariant Visual Servoing</text>

          <rect x="625" y="256" width="220" height="52" rx="6" fill="rgba(255, 255, 255, 0.05)" stroke="rgba(255, 15, 61, 0.4)"/>
          <text x="640" y="278" fill="#fff" font-size="12" font-weight="700">Tactical HUD &amp; Digital Twin</text>
          <text x="640" y="294" fill="#94a3b8" font-size="10" class="mono">3D Perspective Canvas Engine</text>
        </svg>
        <div class="diagram-caption">Figure 1.0: Agesis EYE Multi-Tier Distributed Architecture &amp; Signal Pipeline</div>
      </div>

      <h2 class="section-title">End-to-End Latency Budget Analysis</h2>
      <p>
        Maintaining stability in optical visual servoing requires the total closed-loop system delay to remain well below the mechanical settling time of the micro-actuator. Any cumulative delay exceeding 80 ms produces violent oscillatory overshoot and control divergency. Agesis EYE restricts the cumulative pipeline delay to <strong>48.7 milliseconds</strong>.
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Pipeline Phase</th>
              <th>Hardware Component</th>
              <th>Latency</th>
              <th>Optimization Strategy</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>1. Optical Exposure</strong></td>
              <td>OmniVision OV2640</td>
              <td>12.0 ms</td>
              <td>QVGA format (320x240) with AGC ceiling clamp.</td>
            </tr>
            <tr>
              <td><strong>2. JPEG Encoding</strong></td>
              <td>ESP32 Hardware Core</td>
              <td>4.5 ms</td>
              <td>Fixed DMA buffer transfers with compression factor 14.</td>
            </tr>
            <tr>
              <td><strong>3. Network Transit</strong></td>
              <td>Wi-Fi 802.11 b/g/n</td>
              <td>3.5 ms</td>
              <td>Dedicated non-blocking TCP socket directly on port 81.</td>
            </tr>
            <tr>
              <td><strong>4. Ingestion &amp; Decompression</strong></td>
              <td>Zero-Lag Background Worker</td>
              <td>2.2 ms</td>
              <td>Atomic memory pointer swap discarding queued stale frames.</td>
            </tr>
            <tr>
              <td><strong>5. Edge Neural Inference</strong></td>
              <td>ONNX Runtime (AVX-512 SIMD)</td>
              <td>16.5 ms</td>
              <td>Quantized single-stage decoupled anchor-free head.</td>
            </tr>
            <tr>
              <td><strong>6. Kinematics &amp; Servoing</strong></td>
              <td>Aiming Computer</td>
              <td>0.5 ms</td>
              <td>Direct trigonometric image-space angle conversion.</td>
            </tr>
            <tr>
              <td><strong>7. UDP Command Telemetry</strong></td>
              <td>UDP Non-Blocking Socket</td>
              <td>1.5 ms</td>
              <td>Raw binary packet dispatch over port 8888.</td>
            </tr>
            <tr>
              <td><strong>8. LEDC Motor Settling</strong></td>
              <td>TowerPro SG90 Actuators</td>
              <td>8.0 ms</td>
              <td>14-bit hardware PWM timer with S-curve acceleration.</td>
            </tr>
            <tr style="background: rgba(255, 15, 61, 0.12); font-weight: 800;">
              <td><strong>TOTAL LATENCY BUDGET</strong></td>
              <td>Closed-Loop System</td>
              <td style="color: var(--neon-yellow);">48.7 ms</td>
              <td>Guaranteed sub-50ms deterministic real-time tracking.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Section 2: Embedded Systems -->
    <section id="embedded">
      <h1 class="chapter-heading"><span class="chapter-badge">SEC 02</span> Embedded Systems &amp; 14-Bit PWM Control</h1>

      <p>
        Power distribution and hardware timer precision represent the most critical physical engineering challenges when deploying hobby-grade micro-servos under a compact 5V 2A electrical envelope.
      </p>

      <!-- SVG Wiring Schematic: Glowing Pink & Yellow -->
      <div class="diagram-panel">
        <svg viewBox="0 0 880 340" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
          <!-- Power Supply Block -->
          <rect x="30" y="30" width="180" height="280" rx="8" fill="rgba(16, 12, 18, 0.75)" stroke="#ffd600" stroke-width="2" filter="url(#glow-yellow)"/>
          <text x="50" y="60" fill="#ffd600" font-size="12" font-weight="800" class="mono">REGULATED DC SUPPLY</text>
          <text x="50" y="80" fill="#fff" font-size="18" font-weight="900">5.0V &bull; 2.0A</text>
          
          <rect x="50" y="110" width="140" height="50" rx="4" fill="rgba(255, 214, 0, 0.15)" stroke="#ffd600"/>
          <text x="65" y="132" fill="#ffd600" font-size="10" font-weight="700" class="mono">Peak Limit: 2000mA</text>
          <text x="65" y="148" fill="#cbd5e1" font-size="10">Continuous: 1800mA</text>

          <rect x="50" y="180" width="140" height="110" rx="4" fill="rgba(255, 42, 133, 0.12)" stroke="#ff2a85"/>
          <text x="65" y="204" fill="#ff2a85" font-size="10" font-weight="800" class="mono">DECOUPLING CAPACITOR</text>
          <text x="65" y="222" fill="#fff" font-size="14" font-weight="700">1000 &mu;F / 16V</text>
          <text x="65" y="240" fill="#94a3b8" font-size="9">Low-ESR Electrolytic</text>
          <text x="65" y="258" fill="#ffd600" font-size="9">Absorbs 800mA surge</text>

          <!-- Distribution Rails -->
          <path d="M 210 100 L 320 100" stroke="#ff0f3d" stroke-width="4"/>
          <text x="235" y="90" fill="#ff0f3d" font-size="11" font-weight="800" class="mono">+5V RAIL</text>

          <path d="M 210 240 L 320 240" stroke="#64748b" stroke-width="4"/>
          <text x="235" y="260" fill="#64748b" font-size="11" font-weight="800" class="mono">COMMON GND</text>

          <!-- ESP32-CAM MCU -->
          <rect x="320" y="30" width="280" height="280" rx="8" fill="rgba(16, 12, 18, 0.75)" stroke="#ff2a85" stroke-width="2" filter="url(#glow-pink)"/>
          <text x="340" y="60" fill="#ff2a85" font-size="12" font-weight="800" class="mono">ESP32-CAM CORE LOGIC</text>
          
          <rect x="340" y="80" width="240" height="40" rx="4" fill="rgba(255, 15, 61, 0.2)" stroke="#ff0f3d"/>
          <text x="355" y="104" fill="#fff" font-size="11" font-weight="700">Power Input: 5V &amp; GND</text>

          <rect x="340" y="130" width="240" height="40" rx="4" fill="rgba(255, 214, 0, 0.2)" stroke="#ffd600"/>
          <text x="355" y="154" fill="#ffd600" font-size="11" font-weight="700">GPIO 12: Pan LEDC Channel 2</text>

          <rect x="340" y="180" width="240" height="40" rx="4" fill="rgba(255, 42, 133, 0.2)" stroke="#ff2a85"/>
          <text x="355" y="204" fill="#ff2a85" font-size="11" font-weight="700">GPIO 13: Tilt LEDC Channel 3</text>

          <rect x="340" y="230" width="240" height="40" rx="4" fill="rgba(255, 15, 61, 0.2)" stroke="#ff0f3d"/>
          <text x="355" y="254" fill="#ff0f3d" font-size="11" font-weight="700">GPIO 14: Laser Diode Trigger</text>

          <!-- Peripheral Actuators -->
          <path d="M 600 150 L 660 150" stroke="#ffd600" stroke-width="3"/>
          <path d="M 600 200 L 660 200" stroke="#ff2a85" stroke-width="3"/>
          <path d="M 600 250 L 660 250" stroke="#ff0f3d" stroke-width="3"/>

          <!-- Pan Servo -->
          <rect x="660" y="125" width="190" height="60" rx="6" fill="rgba(255, 214, 0, 0.15)" stroke="#ffd600" stroke-width="1.5" filter="url(#glow-yellow)"/>
          <text x="675" y="148" fill="#fff" font-size="12" font-weight="700">PAN SERVO (SG90)</text>
          <text x="675" y="166" fill="#ffd600" font-size="10" class="mono">GPIO 12 &bull; LEDC Channel 2</text>

          <!-- Tilt Servo -->
          <rect x="660" y="195" width="190" height="60" rx="6" fill="rgba(255, 42, 133, 0.15)" stroke="#ff2a85" stroke-width="1.5" filter="url(#glow-pink)"/>
          <text x="675" y="218" fill="#fff" font-size="12" font-weight="700">TILT SERVO (SG90)</text>
          <text x="675" y="236" fill="#ff2a85" font-size="10" class="mono">GPIO 13 &bull; LEDC Channel 3</text>

          <!-- Laser Diode -->
          <rect x="660" y="265" width="190" height="45" rx="6" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d" stroke-width="1.5"/>
          <text x="675" y="285" fill="#fff" font-size="11" font-weight="700">LASER EMITTER DIODE</text>
          <text x="675" y="299" fill="#ff0f3d" font-size="9" class="mono">GPIO 14 &bull; Interlock Protected</text>
        </svg>
        <div class="diagram-caption">Figure 2.0: Electrical Power Distribution &amp; Isolated Peripheral Wiring Schematic</div>
      </div>

      <h2 class="section-title">LEDC 14-Bit Hardware PWM Timer Formulation</h2>
      <p>
        The TowerPro SG90 micro-servo operates on a 50 Hz PWM carrier ($T = 20\text{ ms} = 20,000\,\mu\text{s}$). To eliminate visible motor jitter and achieve smooth trajectory interpolation without CPU-blocking software delays, the ESP32 LEDC timer peripheral is configured for 14-bit counter resolution.
      </p>

      <!-- Formula Block 1: LEDC PWM Ticks -->
      <div class="math-block">
        <div class="math-header">Hardware PWM Duty Cycle &amp; Angular Step Equation</div>
        
        <div class="math-display-box">
          $$\text{Pulse}(\theta) = 544\,\mu\text{s} + \left(\frac{\theta}{180^\circ}\right) \times (2400\,\mu\text{s} - 544\,\mu\text{s})$$
          $$\text{Duty Ticks}(\theta) = \left[ \frac{\text{Pulse}(\theta)}{20,000\,\mu\text{s}} \right] \times \left(2^{14} - 1\right) = \left[ \frac{\text{Pulse}(\theta)}{20,000\,\mu\text{s}} \right] \times 16,383$$
        </div>

        <div class="math-params-grid">
          <div class="param-item">
            <span class="param-name">&theta; (Target Mechanical Angle)</span>
            Mechanical command angle ranging continuously from 0.0&deg; (extreme limit) to 180.0&deg; (opposing limit).
          </div>
          <div class="param-item">
            <span class="param-name">544 &mu;s / 2400 &mu;s</span>
            Empirically calibrated minimum and maximum pulse widths for TowerPro SG90 micro-servo gearboxes.
          </div>
          <div class="param-item">
            <span class="param-name">16,383 Discrete Ticks</span>
            Total counts available across the 20,000 &mu;s period under the 14-bit hardware timer peripheral.
          </div>
          <div class="param-item">
            <span class="param-name">0.0135&deg; / Tick Resolution</span>
            Fine angular granularity per discrete register step, completely eliminating stepping cogging.
          </div>
        </div>

        <div class="math-walkthrough">
          <strong>Step-by-Step Numerical Example:</strong> To position the Pan turret dead-center at $\theta = 90.0^\circ$:
          First compute the pulse duration: $\text{Pulse}(90^\circ) = 544 + (0.5 \times 1856) = 1472\,\mu\text{s}$.
          Then convert to register ticks: $\text{Duty Ticks} = (1472 / 20,000) \times 16,383 = 1,206\text{ ticks}$. Writing 1,206 to LEDC registers produces the exact physical boresight alignment.
        </div>
      </div>

      <h2 class="section-title">5V 2A Inrush Current Math &amp; S-Curve Slew-Rate Limiting</h2>
      <p>
        When an unconstrained micro-servo receives a step command across a large angle, the motor instantaneously demands stall current of up to 800 mA. If both Pan and Tilt servos step concurrently while the ESP32 Wi-Fi radio is actively transmitting (380 mA peak), the cumulative instantaneous current demand spikes:
      </p>

      <!-- Formula Block 2: Current Surge -->
      <div class="math-block">
        <div class="math-header">Worst-Case Current Surge Equation</div>
        
        <div class="math-display-box">
          $$I_{\text{peak}} = I_{\text{WiFi Radio}} + I_{\text{Pan Motor}} + I_{\text{Tilt Motor}} + I_{\text{Laser}} = 380\text{ mA} + 800\text{ mA} + 800\text{ mA} + 40\text{ mA} = 2,020\text{ mA} \approx 2.02\text{ A}$$
        </div>

        <div class="math-params-grid">
          <div class="param-item">
            <span class="param-name">2,020 mA Peak Draw</span>
            Instantaneous current demand exceeding the 2,000 mA maximum rating of a standard 5V wall adapter.
          </div>
          <div class="param-item">
            <span class="param-name">Rail Voltage Sag &le; 4.2V</span>
            Drawing over 2.0A induces immediate voltage collapse below the 4.3V threshold of the onboard AMS1117 regulator.
          </div>
        </div>
      </div>

      <div class="callout callout-hazard">
        <div class="callout-title">Hardware Brownout Hazard &amp; Infinite Boot Loop</div>
        When the internal DC rail drops below 4.2V, the ESP32 silicon brownout detection circuit triggers an involuntary hardware reset. When the microcontroller reboots, Wi-Fi initialization repeats the current surge, plunging the turret into an unrecoverable infinite boot loop.
      </div>

      <p>
        <strong>Firmware Mitigation:</strong> The ESP32 firmware executes a 50 Hz discrete S-curve slew rate limiter. Velocity is capped at <strong>120&deg;/second</strong> ($2.4^\circ$ per 20 ms timer tick). Under this controlled acceleration envelope, the motors never enter the dead-stall electrical regime, reducing peak current by <strong>65%</strong> to &le; 280 mA per actuator and maintaining total system draw at 980 mA (a healthy 51% safety margin).
      </p>
    </section>

    <!-- Section 3: Edge AI Vision -->
    <section id="edge-ai">
      <h1 class="chapter-heading"><span class="chapter-badge">SEC 03</span> Edge AI Vision Pipeline</h1>

      <p>
        High-speed aerial tracking presents extreme challenges for standard video stream ingestion. Standard video capture libraries buffer multiple sequential frames internally. If network jitter delays packet arrival, standard readers deliver frames that are 200 ms to 500 ms stale.
      </p>

      <!-- SVG Ingestion Diagram: Glowing Pink & Yellow -->
      <div class="diagram-panel">
        <svg viewBox="0 0 880 260" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
          <!-- Left: Conventional Buffered Stream -->
          <rect x="30" y="30" width="380" height="200" rx="8" fill="rgba(16, 12, 18, 0.75)" stroke="#ff0f3d" stroke-width="1.8"/>
          <text x="50" y="60" fill="#ff0f3d" font-size="12" font-weight="800" class="mono">CONVENTIONAL STREAM (STALE FIFO)</text>
          
          <rect x="50" y="80" width="55" height="40" rx="4" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d"/><text x="65" y="105" fill="#94a3b8" font-size="10" class="mono">F_t-5</text>
          <rect x="115" y="80" width="55" height="40" rx="4" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d"/><text x="130" y="105" fill="#94a3b8" font-size="10" class="mono">F_t-4</text>
          <rect x="180" y="80" width="55" height="40" rx="4" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d"/><text x="195" y="105" fill="#94a3b8" font-size="10" class="mono">F_t-3</text>
          <rect x="245" y="80" width="55" height="40" rx="4" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d"/><text x="260" y="105" fill="#94a3b8" font-size="10" class="mono">F_t-2</text>
          <rect x="310" y="80" width="55" height="40" rx="4" fill="#ff0f3d"/><text x="325" y="105" fill="#fff" font-size="10" class="mono">F_t-1</text>
          
          <text x="50" y="150" fill="#ff0f3d" font-size="12" font-weight="700">Socket FIFO Buffer Queue (Stale Frames)</text>
          <text x="50" y="172" fill="#94a3b8" font-size="11">Model processes frame t-5 while target has already moved.</text>
          <text x="50" y="194" fill="#ff0f3d" font-size="12" font-weight="800" class="mono">Result: Severe Oscillation &amp; Overshoot</text>

          <!-- Right: Zero-Lag Ingestion -->
          <rect x="470" y="30" width="380" height="200" rx="8" fill="rgba(16, 12, 18, 0.75)" stroke="#ffd600" stroke-width="1.8" filter="url(#glow-yellow)"/>
          <text x="490" y="60" fill="#ffd600" font-size="12" font-weight="800" class="mono">ZERO-LAG INGESTION ENGINE</text>

          <rect x="490" y="80" width="220" height="45" rx="6" fill="rgba(255, 214, 0, 0.18)" stroke="#ffd600"/>
          <text x="510" y="102" fill="#fff" font-size="11" font-weight="800" class="mono">ATOMIC FRAME POINTER (RAM)</text>
          <text x="510" y="116" fill="#ffd600" font-size="10" class="mono">Always Overwritten by Freshest Frame</text>

          <text x="490" y="150" fill="#ffd600" font-size="12" font-weight="700">Continuous Buffer Drain Thread</text>
          <text x="490" y="172" fill="#94a3b8" font-size="11">Stale intermediary bytes are discarded instantly in memory.</text>
          <text x="490" y="194" fill="#ff2a85" font-size="12" font-weight="800" class="mono">Latency: &lt; 2.0 ms Guaranteed Ingestion</text>
        </svg>
        <div class="diagram-caption">Figure 3.0: FIFO Socket Buffer Stalling vs. Atomic Zero-Lag Stream Ingestion</div>
      </div>

      <h2 class="section-title">Optical Boresight Error Formulation</h2>
      <p>
        The localized neural model outputs normalized bounding box coordinates $[X_{\min}, Y_{\min}, X_{\max}, Y_{\max}]$. The aiming computer transforms these coordinates into pixel offsets relative to the camera central boresight:
      </p>

      <!-- Formula Block 3: Boresight Offsets -->
      <div class="math-block">
        <div class="math-header">Centroid &amp; Optical Boresight Error Equations</div>
        
        <div class="math-display-box">
          $$X_{\text{centroid}} = \frac{X_{\min} + X_{\max}}{2}, \quad Y_{\text{centroid}} = \frac{Y_{\min} + Y_{\max}}{2}$$
          $$\Delta X = X_{\text{centroid}} - \frac{W}{2}, \quad \Delta Y = Y_{\text{centroid}} - \frac{H}{2}$$
        </div>

        <div class="math-params-grid">
          <div class="param-item">
            <span class="param-name">W = 320 px, H = 240 px</span>
            Native optical frame resolution (QVGA format), placing the camera boresight center at $(160, 120)$.
          </div>
          <div class="param-item">
            <span class="param-name">&Delta;X &gt; 0 (Positive X-Offset)</span>
            Target is situated to the <strong>RIGHT</strong> of the boresight &rarr; Command Pan servo clockwise.
          </div>
          <div class="param-item">
            <span class="param-name">&Delta;X &lt; 0 (Negative X-Offset)</span>
            Target is situated to the <strong>LEFT</strong> of the boresight &rarr; Command Pan servo counter-clockwise.
          </div>
          <div class="param-item">
            <span class="param-name">&Delta;Y &gt; 0 (Positive Y-Offset)</span>
            Target is situated <strong>BELOW</strong> the boresight &rarr; Command Tilt servo downward.
          </div>
        </div>

        <div class="math-walkthrough">
          <strong>Concrete Calculation Example:</strong> Suppose the neural network detects a balloon with bounding box $[200, 80, 280, 160]$.
          Centroid $X_{\text{centroid}} = (200 + 280)/2 = 240\text{ px}$, and $Y_{\text{centroid}} = (80 + 160)/2 = 120\text{ px}$.
          Offsets: $\Delta X = 240 - 160 = +80\text{ px}$, and $\Delta Y = 120 - 120 = 0\text{ px}$.
          Result: The control law immediately commands Pan right by $+6.0^\circ$ while holding Tilt elevation stationary.
        </div>
      </div>
    </section>

    <!-- Section 4: Robotics & Kinematics -->
    <section id="robotics">
      <h1 class="chapter-heading"><span class="chapter-badge">SEC 04</span> Robotics, Kinematics &amp; Visual Servoing</h1>

      <p>
        Agesis EYE implements an **eye-in-hand** kinematic configuration where the optical sensor and weapon emitter are mounted directly onto the pivoting elevation C-arm. The Pan axis and Tilt axis are separated vertically by a mechanical standoff riser of height $d$.
      </p>

      <!-- SVG Kinematics Diagram: Glowing Pink, Electric Yellow & Red -->
      <div class="diagram-panel">
        <svg viewBox="0 0 880 320" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
          <!-- Base Pedestal -->
          <rect x="180" y="260" width="120" height="30" rx="4" fill="#ff0f3d" stroke="#8b0018"/>
          <text x="205" y="280" fill="#fff" font-size="11" font-weight="800" class="mono">GROUND BASE</text>

          <rect x="220" y="190" width="40" height="70" rx="4" fill="rgba(255, 214, 0, 0.2)" stroke="#ffd600" stroke-width="1.5"/>
          <text x="140" y="230" fill="#ffd600" font-size="11" font-weight="800" class="mono">Pedestal H0</text>

          <!-- Pan Joint J1 -->
          <circle cx="240" cy="190" r="14" fill="#ff2a85" stroke="#fff" stroke-width="2" filter="url(#glow-pink)"/>
          <text x="265" y="195" fill="#ff2a85" font-size="11" font-weight="800" class="mono">Pan Joint J1 (Z-Axis)</text>

          <!-- Standoff d -->
          <line x1="240" y1="190" x2="240" y2="80" stroke="#ffd600" stroke-width="4" stroke-dasharray="3 3"/>
          <line x1="220" y1="190" x2="210" y2="190" stroke="#ffd600" stroke-width="1.5"/>
          <line x1="220" y1="80" x2="210" y2="80" stroke="#ffd600" stroke-width="1.5"/>
          <line x1="215" y1="190" x2="215" y2="80" stroke="#ffd600" stroke-width="1.5"/>
          <text x="145" y="140" fill="#ffd600" font-size="12" font-weight="800" class="mono">Standoff d</text>

          <!-- Tilt Joint J2 -->
          <circle cx="240" cy="80" r="14" fill="#ff2a85" stroke="#fff" stroke-width="2" filter="url(#glow-pink)"/>
          <text x="265" y="85" fill="#ff2a85" font-size="11" font-weight="800" class="mono">Tilt Joint J2</text>

          <!-- C-Arm Assembly -->
          <path d="M 240 80 L 310 80 L 310 40 L 360 40 M 310 80 L 310 120 L 360 120" stroke="#ff0f3d" stroke-width="6" fill="none"/>
          <rect x="340" y="60" width="50" height="40" rx="4" fill="rgba(255, 42, 133, 0.25)" stroke="#ff2a85" stroke-width="2"/>
          <text x="345" y="84" fill="#ff2a85" font-size="10" font-weight="800" class="mono">Camera</text>

          <!-- Laser Line of Sight -->
          <line x1="390" y1="80" x2="720" y2="80" stroke="#ff0f3d" stroke-width="3" stroke-dasharray="6 3" filter="url(#glow-red)"/>
          <circle cx="720" cy="80" r="16" fill="rgba(255, 15, 61, 0.3)" stroke="#ff0f3d" stroke-width="2"/>
          <text x="750" y="85" fill="#ff0f3d" font-size="12" font-weight="800" class="mono">Target Lock</text>

          <!-- Invariance Annotation -->
          <rect x="440" y="170" width="380" height="100" rx="6" fill="rgba(18, 14, 22, 0.9)" stroke="#ffd600" stroke-width="1.2"/>
          <text x="460" y="195" fill="#ffd600" font-size="12" font-weight="800" class="mono">MATHEMATICAL PROOF: d-INVARIANCE</text>
          <text x="460" y="218" fill="#cbd5e1" font-size="11">1. Pan axis rotates around vertical Z-axis; independent of d.</text>
          <text x="460" y="236" fill="#cbd5e1" font-size="11">2. Camera on J2 makes optical line-of-sight error independent of d.</text>
          <text x="460" y="254" fill="#ff2a85" font-size="11" font-weight="700" class="mono">Visual error law holds for any physical stanchion height.</text>
        </svg>
        <div class="diagram-caption">Figure 4.0: 2-DoF Kinematic Coordinate Frames &amp; Mechanical Standoff Decoupling</div>
      </div>

      <h2 class="section-title">Geometric Proof of Standoff Distance d Invariance</h2>
      <p>
        In traditional open-loop robotics, spatial distance between joints induces severe geometric parallax, forcing engineers to recalculate inverse kinematics whenever a riser height changes. Agesis EYE employs <strong>Image-Based Visual Servoing (IBVS)</strong>, driving actuators strictly from image-space optical error:
      </p>

      <!-- Formula Block 4: Invariance Proof -->
      <div class="math-block">
        <div class="math-header">Visual Servoing &amp; Invariance Law</div>
        
        <div class="math-display-box">
          $$\Delta \theta_{\text{pan}} = -\arctan\left(\frac{\Delta X}{f_x}\right), \quad \Delta \theta_{\text{tilt}} = \arctan\left(\frac{\Delta Y}{f_y}\right)$$
        </div>

        <div class="math-params-grid">
          <div class="param-item">
            <span class="param-name">f_x, f_y (Focal Length)</span>
            Effective optical focal length expressed in pixels ($f \approx 250\text{ px}$ for the OV2640 lens).
          </div>
          <div class="param-item">
            <span class="param-name">Small-Angle Approximation</span>
            When target is near center ($\Delta X \ll f_x$), $\arctan(u) \approx u \implies \Delta \theta \approx -K_p \cdot \Delta X$.
          </div>
        </div>

        <div class="math-walkthrough">
          <strong>Formal Proof of d-Independence:</strong>
          Because the optical sensor and weapon emitter are co-located on Joint 2, the line of sight vector originates at Joint 2. The vertical riser simply offsets Joint 2 along the vertical Z-axis. Since rotation about the Z-axis is identical at all heights along the axis, the variable distance $d$ completely drops out of the differential equations:
          $$\frac{\partial (\Delta \theta_{\text{pan}})}{\partial d} \equiv 0, \quad \frac{\partial (\Delta \theta_{\text{tilt}})}{\partial d} \equiv 0$$
          The visual servoing convergence law remains 100% mathematically invariant regardless of physical stanchion height.
        </div>
      </div>
    </section>

    <!-- Section 5: Physical AI & Digital Twin -->
    <section id="physical-ai">
      <h1 class="chapter-heading"><span class="chapter-badge">SEC 05</span> Physical AI &amp; 3D Kinematic Digital Twin</h1>

      <p>
        Unlike disembodied AI models that operate strictly in virtual spaces (such as text models), <strong>Physical AI</strong> embodies perception directly in real physical hardware that must respect motor torque constraints, gear backlash, inertia, and power limits.
      </p>

      <!-- SVG CAD Matching Diagram: Pink & Yellow Accents -->
      <div class="diagram-panel">
        <svg viewBox="0 0 880 280" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
          <!-- Physical Assembly Render Block -->
          <rect x="40" y="25" width="380" height="235" rx="8" fill="rgba(16, 12, 18, 0.75)" stroke="#ff0f3d" stroke-width="1.8"/>
          <text x="55" y="48" fill="#ff0f3d" font-size="11" font-weight="800" class="mono">PHYSICAL TINKERCAD CAD ASSEMBLY</text>
          
          <rect x="70" y="210" width="160" height="24" rx="3" fill="#ff0f3d" stroke="#8b0018"/><text x="80" y="226" fill="#fff" font-size="10" class="mono">Red Baseplate</text>
          <rect x="240" y="190" width="100" height="44" rx="4" fill="rgba(255, 214, 0, 0.2)" stroke="#ffd600"/><text x="250" y="216" fill="#ffd600" font-size="10" font-weight="800" class="mono">Electronics Box</text>
          <rect x="110" y="120" width="50" height="90" rx="4" fill="rgba(255, 42, 133, 0.2)" stroke="#ff2a85"/><text x="116" y="165" fill="#ff2a85" font-size="10" class="mono">Pedestal</text>
          <rect x="122" y="90" width="26" height="30" rx="3" fill="#ffd600" stroke="#fff"/><text x="155" y="108" fill="#ffd600" font-size="10" class="mono">Pan SG90</text>
          <rect x="130" y="65" width="10" height="25" fill="#ff2a85"/>
          <rect x="145" y="62" width="60" height="28" rx="4" fill="#ff0f3d"/><text x="215" y="80" fill="#fff" font-size="10" class="mono">Red C-Arm</text>

          <!-- Right Digital Twin Mirror -->
          <rect x="460" y="30" width="380" height="220" rx="8" fill="rgba(16, 12, 18, 0.75)" stroke="#ffd600" stroke-width="1.8" filter="url(#glow-yellow)"/>
          <text x="480" y="58" fill="#ffd600" font-size="12" font-weight="800" class="mono">3D KINEMATIC DIGITAL TWIN</text>

          <circle cx="650" cy="140" r="60" fill="none" stroke="#ff0f3d" stroke-width="1.2" stroke-dasharray="4 4"/>
          <circle cx="650" cy="140" r="35" fill="none" stroke="#ff2a85" stroke-width="1.2" stroke-dasharray="4 4"/>
          <line x1="580" y1="140" x2="720" y2="140" stroke="rgba(255,15,60,0.4)"/>
          <line x1="650" y1="70" x2="650" y2="210" stroke="rgba(255,15,60,0.4)"/>

          <circle cx="650" cy="140" r="10" fill="#ffd600" filter="url(#glow-yellow)"/>
          <text x="480" y="216" fill="#ff2a85" font-size="11" class="mono">Real-Time WebSocket State Sync @ 25Hz</text>
          <text x="480" y="234" fill="#ffd600" font-size="11" class="mono">Thermal Weapon Accumulation &amp; Shrapnel Physics</text>
        </svg>
        <div class="diagram-caption">Figure 5.0: Physical CAD Assembly vs. Real-Time Perspective Digital Twin Engine</div>
      </div>

      <h2 class="section-title">3D Perspective Projection Mathematics</h2>
      <p>
        The digital twin renders multi-body geometry directly onto an HTML5 Canvas at 60 FPS without external graphical engine bloat. The perspective projection converts 3D world coordinates $[X, Y, Z]^T$ to screen pixels $[X_{\text{screen}}, Y_{\text{screen}}]^T$:
      </p>

      <!-- Formula Block 5: 3D Projection -->
      <div class="math-block">
        <div class="math-header">3D Camera Coordinate &amp; Screen Projection Model</div>
        
        <div class="math-display-box">
          $$\mathbf{P}_{\text{cam}} = \mathbf{R}_x(\theta_{\text{pitch}}) \cdot \mathbf{R}_y(\theta_{\text{yaw}}) \cdot (\mathbf{P}_{\text{world}} + \mathbf{T}_{\text{pan}})$$
          $$\text{Scale} = \frac{f_{\text{fov}}}{\max(50, Z_{\text{cam}} + D)}, \quad X_{\text{screen}} = \frac{W}{2} + X_{\text{cam}} \cdot \text{Scale}, \quad Y_{\text{screen}} = \frac{H}{2} - Y_{\text{cam}} \cdot \text{Scale}$$
        </div>

        <div class="math-params-grid">
          <div class="param-item">
            <span class="param-name">R_x, R_y (Rotation Matrices)</span>
            Euler rotation matrices transforming 3D turret points by Pan yaw ($\psi$) and Tilt elevation ($\phi$).
          </div>
          <div class="param-item">
            <span class="param-name">D (Focal Distance Offset)</span>
            Camera perspective standoff distance ($D = 420\text{ units}$), providing natural depth foreshortening.
          </div>
        </div>
      </div>
    </section>

    <!-- Section 6: AI/ML Engineering -->
    <section id="ai-ml">
      <h1 class="chapter-heading"><span class="chapter-badge">SEC 06</span> AI/ML Engineering &amp; Optimization</h1>

      <p>
        The vision intelligence utilizes a customized single-stage detector optimized for high-speed aerial micro-targets (balloons and drones). The neural network pairs a cross-stage partial feature extractor with an anchor-free decoupled detection head.
      </p>

      <!-- SVG Neural Network Diagram: Glowing Pink & Yellow Blocks -->
      <div class="diagram-panel">
        <svg viewBox="0 0 880 240" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
          <!-- Input -->
          <rect x="30" y="80" width="90" height="80" rx="6" fill="rgba(255, 42, 133, 0.15)" stroke="#ff2a85" stroke-width="1.8"/>
          <text x="42" y="115" fill="#fff" font-size="11" font-weight="800">INPUT</text>
          <text x="38" y="132" fill="#ff2a85" font-size="10" class="mono">384x384x3</text>

          <path d="M 120 120 L 160 120" stroke="#ff2a85" stroke-width="2"/>

          <!-- Backbone -->
          <rect x="160" y="50" width="160" height="140" rx="6" fill="rgba(255, 42, 133, 0.12)" stroke="#ff2a85" stroke-width="1.8"/>
          <text x="175" y="75" fill="#ff2a85" font-size="11" font-weight="800" class="mono">BACKBONE (C2F)</text>
          <rect x="175" y="90" width="130" height="26" rx="4" fill="rgba(255, 42, 133, 0.25)"/><text x="185" y="107" fill="#fff" font-size="10">Conv Stem (s=2)</text>
          <rect x="175" y="122" width="130" height="26" rx="4" fill="rgba(255, 42, 133, 0.25)"/><text x="185" y="139" fill="#fff" font-size="10">Cross-Stage Blocks</text>
          <rect x="175" y="154" width="130" height="26" rx="4" fill="rgba(255, 42, 133, 0.25)"/><text x="185" y="171" fill="#fff" font-size="10">SPPF Feature Pool</text>

          <path d="M 320 120 L 360 120" stroke="#ffd600" stroke-width="2"/>

          <!-- Neck -->
          <rect x="360" y="50" width="160" height="140" rx="6" fill="rgba(255, 214, 0, 0.12)" stroke="#ffd600" stroke-width="1.8"/>
          <text x="375" y="75" fill="#ffd600" font-size="11" font-weight="800" class="mono">NECK (PANET)</text>
          <rect x="375" y="95" width="130" height="35" rx="4" fill="rgba(255, 214, 0, 0.2)"/><text x="385" y="117" fill="#ffd600" font-size="10">Top-Down Pyramid</text>
          <rect x="375" y="140" width="130" height="35" rx="4" fill="rgba(255, 214, 0, 0.2)"/><text x="385" y="162" fill="#ffd600" font-size="10">Bottom-Up Path</text>

          <path d="M 520 120 L 560 120" stroke="#ff0f3d" stroke-width="2"/>

          <!-- Decoupled Head -->
          <rect x="560" y="50" width="280" height="140" rx="6" fill="rgba(255, 15, 61, 0.15)" stroke="#ff0f3d" stroke-width="1.8"/>
          <text x="575" y="75" fill="#ff0f3d" font-size="11" font-weight="800" class="mono">DECOUPLED ANCHOR-FREE HEAD</text>
          <rect x="575" y="95" width="250" height="35" rx="4" fill="rgba(255, 15, 61, 0.25)"/><text x="590" y="117" fill="#ff2a85" font-size="10">Regression Branch (CIoU + DFL Loss)</text>
          <rect x="575" y="140" width="250" height="35" rx="4" fill="rgba(255, 15, 61, 0.25)"/><text x="590" y="162" fill="#ffd600" font-size="10">Classification Branch (BCE Loss)</text>
        </svg>
        <div class="diagram-caption">Figure 6.0: Single-Stage Anchor-Free YOLO Edge Detection Architecture</div>
      </div>

      <h2 class="section-title">Multi-Task Loss Formulation</h2>
      <p>
        The model trains under a compound objective balancing bounding box overlap, boundary uncertainty regression, and class discrimination confidence:
      </p>

      <!-- Formula Block 6: Multi-Task Loss -->
      <div class="math-block">
        <div class="math-header">Compound Multi-Task Objective Function</div>
        
        <div class="math-display-box">
          $$\mathcal{L}_{\text{total}} = \lambda_{\text{box}} \mathcal{L}_{\text{CIoU}} + \lambda_{\text{dfl}} \mathcal{L}_{\text{DFL}} + \lambda_{\text{cls}} \mathcal{L}_{\text{BCE}}$$
        </div>

        <div class="math-params-grid">
          <div class="param-item">
            <span class="param-name">CIoU Loss (&lambda;_box = 7.5)</span>
            Complete IoU loss penalizing Euclidean distance between box centroids, scale ratio, and aspect ratio divergence.
          </div>
          <div class="param-item">
            <span class="param-name">DFL Loss (&lambda;_dfl = 1.5)</span>
            Distribution Focal Loss modeling bounding box edges as continuous probability distributions over 16 bins.
          </div>
          <div class="param-item">
            <span class="param-name">BCE Loss (&lambda;_cls = 0.5)</span>
            Binary cross-entropy loss driving classification confidence for robust target vs background discrimination.
          </div>
          <div class="param-item">
            <span class="param-name">Quantized CPU Deployment</span>
            Exported to FP16 ONNX runtime graph executed via AVX-512 vector SIMD cores at 45+ FPS.
          </div>
        </div>
      </div>
    </section>

    <!-- Section 7: Hardware & Safety -->
    <section id="safety">
      <h1 class="chapter-heading"><span class="chapter-badge">SEC 07</span> Assembly, Wiring &amp; Safety Protocols</h1>

      <p>
        Operating high-energy electro-optical emitters requires stringent hardware and software fail-safes. The Agesis EYE firmware and ground station enforce a five-stage hardware interlock finite state machine.
      </p>

      <!-- SVG Safety FSM Diagram: Glowing Pink, Yellow & Blood Red -->
      <div class="diagram-panel">
        <svg viewBox="0 0 880 200" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
          <!-- State 1: DISARMED -->
          <rect x="30" y="70" width="150" height="60" rx="6" fill="rgba(100, 116, 139, 0.2)" stroke="#64748b" stroke-width="2"/>
          <text x="50" y="96" fill="#94a3b8" font-size="11" font-weight="800" class="mono">STATE 1: SAFE</text>
          <text x="50" y="114" fill="#fff" font-size="12" font-weight="900">DISARMED</text>

          <path d="M 180 100 L 250 100" stroke="#ffd600" stroke-width="2.5" filter="url(#glow-yellow)"/>

          <!-- State 2: ARMED -->
          <rect x="250" y="70" width="150" height="60" rx="6" fill="rgba(255, 214, 0, 0.18)" stroke="#ffd600" stroke-width="2" filter="url(#glow-yellow)"/>
          <text x="270" y="96" fill="#ffd600" font-size="11" font-weight="800" class="mono">STATE 2: READY</text>
          <text x="270" y="114" fill="#fff" font-size="12" font-weight="900">ARMED</text>

          <path d="M 400 100 L 470 100" stroke="#ff2a85" stroke-width="2.5" filter="url(#glow-pink)"/>

          <!-- State 3: ACQUIRING -->
          <rect x="470" y="70" width="160" height="60" rx="6" fill="rgba(255, 42, 133, 0.18)" stroke="#ff2a85" stroke-width="2" filter="url(#glow-pink)"/>
          <text x="485" y="96" fill="#ff2a85" font-size="11" font-weight="800" class="mono">STATE 3: LOCKING</text>
          <text x="485" y="114" fill="#fff" font-size="12" font-weight="900">&ge; 3 Hits Confirmed</text>

          <path d="M 630 100 L 700 100" stroke="#ff0f3d" stroke-width="2.5" filter="url(#glow-red)"/>

          <!-- State 4: ACTIVE FIRING -->
          <rect x="700" y="70" width="150" height="60" rx="6" fill="rgba(255, 15, 61, 0.3)" stroke="#ff0f3d" stroke-width="2.2" filter="url(#glow-red)"/>
          <text x="720" y="96" fill="#ff2a85" font-size="11" font-weight="800" class="mono">STATE 4: ACTIVE</text>
          <text x="720" y="114" fill="#fff" font-size="12" font-weight="900">FIRING BEAM</text>

          <!-- Cutoff Return Path -->
          <path d="M 775 130 L 775 170 L 325 170 L 325 130" stroke="#ffd600" stroke-width="1.8" stroke-dasharray="5 5" fill="none"/>
          <text x="410" y="185" fill="#ffd600" font-size="10" class="mono">Auto-Cutoff if Target Lost &gt; 300ms OR Max Duration &gt; 1.5s</text>
        </svg>
        <div class="diagram-caption">Figure 7.0: Five-Stage Failsafe Interlock Finite State Machine Architecture</div>
      </div>

      <h2 class="section-title">Safety Operational Checklist</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Protocol Level</th>
              <th>Trigger Condition</th>
              <th>System Action</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Pre-Arm Interlock</strong></td>
              <td>System boot / default state</td>
              <td>Emitter hardware gate held LOW (0V). Software locked.</td>
            </tr>
            <tr>
              <td><strong>Lock Verification</strong></td>
              <td>Detections &lt; 3 consecutive frames</td>
              <td>Beam inhibited. Prevents transient glint discharges.</td>
            </tr>
            <tr>
              <td><strong>Centering Guard</strong></td>
              <td>Boresight error &gt; 16 pixels</td>
              <td>Beam inhibited until turret aligns within target cone.</td>
            </tr>
            <tr>
              <td><strong>Loss-of-Target Cutoff</strong></td>
              <td>Target lost &gt; 300 milliseconds</td>
              <td>Instant sub-millisecond hardware disarm.</td>
            </tr>
            <tr>
              <td><strong>Thermal Duty Cap</strong></td>
              <td>Continuous firing &gt; 1.5 seconds</td>
              <td>Mandatory 2.0-second hardware cooldown lockout enforced.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

  </main>

  <script>
    // Initialize KaTeX with guaranteed DOM readiness
    document.addEventListener("DOMContentLoaded", function() {
      function renderMath() {
        if (typeof renderMathInElement === 'function') {
          renderMathInElement(document.body, {
            delimiters: [
              {left: '$$', right: '$$', display: true},
              {left: '$', right: '$', display: false}
            ],
            throwOnError: false
          });
        } else {
          setTimeout(renderMath, 100);
        }
      }
      renderMath();
    });

    // Highlight active sidebar item on scroll
    window.addEventListener('scroll', () => {
      const headings = document.querySelectorAll('section[id], header[id]');
      let current = '';
      headings.forEach(h => {
        const top = h.getBoundingClientRect().top;
        if (top <= 160) current = h.id;
      });
      document.querySelectorAll('.toc-item a').forEach(link => {
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

def generate():
    print("[*] Generating Black & Bloody Red Glassmorphic Technical Whitepaper...")
    out_html = os.path.join(DOCS_DIR, "index.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"[+] HTML Whitepaper generated: {out_html} ({len(HTML_CONTENT):,} bytes)")

    # Compile PDF in Clean White Background via Edge / Chrome
    pdf_out = os.path.join(DOCS_DIR, "Agesis_EYE_Complete_Manual.pdf")
    browsers = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    browser = next((b for b in browsers if os.path.exists(b)), None)
    if browser:
        print(f"[*] Rendering White-Background PDF Manual via: {browser}")
        file_url = f"file:///{out_html.replace(os.sep, '/')}"
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=3000",
            f"--print-to-pdf={pdf_out}",
            "--no-pdf-header-footer",
            file_url
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
            if os.path.exists(pdf_out) and os.path.getsize(pdf_out) > 5000:
                print(f"[+] Clean White-Background PDF Manual successfully created: {pdf_out} ({os.path.getsize(pdf_out):,} bytes)")
            else:
                print(f"[!] PDF generation failed: {res.stderr.decode()}")
        except Exception as e:
            print(f"[!] Error compiling PDF: {e}")

if __name__ == "__main__":
    generate()
