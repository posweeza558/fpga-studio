#!/usr/bin/env python3
"""
FPGA Studio Presentation Compiler
Combines individual modular slide files from slides/ into a single standalone presentation_all.html.
This prevents Git merge conflicts when multiple speakers edit their own slide files simultaneously.
"""

import os
import re
import sys

# Configure UTF-8 for console output on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLIDES_DIR = os.path.join(SCRIPT_DIR, "slides")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "presentation_all.html")

# 5 Streamlined Core Slides (รวมหน้าโจทย์อาจารย์และการตีความ)
SLIDE_FILES = [
    "00_cover.html",
    "01_challenge.html",
    "02_features.html",
    "03_c_pipeline.html",
    "04_live_demo.html"
]

def compile_presentation():
    print("=" * 60)
    print("[*] FPGA STUDIO PRESENTATION COMPILER (NOTHING TRAILER CAROUSEL)")
    print("=" * 60)

    all_sections = []
    combined_scripts = {}
    current_global_slide = 1

    for filename in SLIDE_FILES:
        filepath = os.path.join(SLIDES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[!] Warning: {filename} not found, skipping...")
            continue

        print(f"[+] Processing: {filename}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Extract speaker cues dictionary
        script_match = re.search(r"window\.speakerScripts\s*=\s*(\{[\s\S]*?\});", content)
        local_cues = {}
        if script_match:
            try:
                raw_dict = script_match.group(1)
                entries = re.findall(r'(\d+)\s*:\s*("(?:\\.|[^"\\])*")', raw_dict)
                for k, v in entries:
                    local_cues[int(k)] = eval(v)
            except Exception as e:
                print(f"   [!] Could not parse scripts in {filename}: {e}")

        # 2. Extract <section class="slide ..."> blocks
        section_pattern = re.compile(r'<section\s+class="slide[^"]*"[\s\S]*?<\/section>', re.IGNORECASE)
        sections = section_pattern.findall(content)

        for i, sec in enumerate(sections, start=1):
            sec_updated = re.sub(r'data-slide="\d+"', f'data-slide="{current_global_slide}"', sec)
            
            # Safely ensure only slide 1 has the 'active' class on the <section> opening tag
            def fix_section_tag(match):
                tag = match.group(0)
                if current_global_slide == 1:
                    if 'active' not in tag:
                        tag = tag.replace('class="slide ', 'class="slide active ')
                else:
                    tag = re.sub(r'\bactive\b', '', tag)
                    tag = re.sub(r'\s+', ' ', tag)
                return tag

            sec_updated = re.sub(r'<section\s+class="[^"]*"[^>]*>', fix_section_tag, sec_updated, count=1)
            sec_updated = sec_updated.replace('../assets/', 'assets/')
            
            all_sections.append(sec_updated)

            if i in local_cues:
                combined_scripts[current_global_slide] = local_cues[i]
            elif current_global_slide in local_cues:
                combined_scripts[current_global_slide] = local_cues[current_global_slide]

            current_global_slide += 1

    total_slides = current_global_slide - 1
    print(f"[OK] Extracted {total_slides} total slides successfully.")

    css_rel = "css/nothing.css"
    js_rel = "js/presentation.js"

    # Build final HTML with horizontal carousel viewport & track (no buttons, progressive edge arrows)
    html_template = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FPGA STUDIO — KEYNOTE SLIDES</title>
    <!-- Tailwind CSS (Public CDN + Antigravity local fallback) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Doto:wght@400;600;800;900&family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;600;700&family=Prompt:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{css_rel}">
</head>
<body class="h-screen w-screen m-0 p-0 relative overflow-hidden">

    <!-- FLOATING TOP HUD BAR (TRANSPARENT OVER FULLSCREEN SPACE STAGE) -->
    <header class="fx-hud flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <span class="glyph-green-dot"></span>
            <span class="mono text-xs text-[#EAEAEA] font-bold tracking-widest uppercase">FPGA STUDIO</span>
            <span class="text-white/20 text-xs">|</span>
            <span class="mono text-xs text-[#1ED760]">v4.4 ORBIT LAUNCH</span>
        </div>

        <div class="flex items-center space-x-4">
            <!-- Fullscreen Button -->
            <button onclick="toggleFullscreen()" class="p-2 rounded-full bg-black/40 border border-white/15 hover:border-[#1ED760]/60 hover:bg-black/70 transition text-xs mono text-[#EAEAEA]" title="Full Screen (F)">
                ⛶
            </button>
        </div>
    </header>

    <!-- FULLSCREEN SLIDE VIEWPORT & TRACK -->
    <main class="w-screen h-screen m-0 p-0 relative z-10 overflow-hidden">
        <div id="carousel-viewport">
            <div id="carousel-track">
{chr(10).join(all_sections)}
            </div>
        </div>
    </main>

    <!-- SPEAKER CUES DRAWER (กดปุ่ม C เพื่อเปิด/ปิด) -->
    <div id="cues-drawer" class="fixed bottom-10 left-1/2 -translate-x-1/2 max-w-4xl w-[92%] bento-card p-5 border-[#484848] shadow-2xl z-50 hidden transition-all">
        <div class="flex justify-between items-center mb-2 border-b border-[#282828] pb-2">
            <div class="flex items-center space-x-2">
                <span class="glyph-red-dot"></span>
                <span class="mono text-xs text-red-400 font-bold uppercase" id="cue-title">CUE SHEET (กดปุ่ม C)</span>
            </div>
            <button onclick="toggleCues()" class="text-xs mono text-white/50 hover:text-white">[ ปิด X ]</button>
        </div>
        <p id="cue-content" class="text-xs md:text-sm text-white/90 leading-relaxed whitespace-pre-line font-normal"></p>
    </div>

    <!-- GENERATED SCRIPTS -->
    <script>
        window.speakerScripts = {repr(combined_scripts)};
    </script>
    <script src="{js_rel}"></script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)

    index_file = os.path.join(os.path.dirname(OUTPUT_FILE), "index.html")
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"[OK] Generated full presentation successfully: {OUTPUT_FILE} & {index_file}")

if __name__ == "__main__":
    compile_presentation()
