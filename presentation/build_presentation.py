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

SLIDE_FILES = [
    "00_cover.html",
    "01_speaker1_challenge.html",
    "02_speaker2_pipeline.html",
    "03_speaker3_demo.html",
    "04_speaker4_superpowers.html"
]

def compile_presentation():
    print("=" * 60)
    print("[*] FPGA STUDIO PRESENTATION COMPILER (SPOTIFY DARK & NOTHING EDITION)")
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
            # Update data-slide attribute to global sequential slide number
            sec_updated = re.sub(r'data-slide="\d+"', f'data-slide="{current_global_slide}"', sec)
            
            # Ensure only slide 1 has "active" initially
            if current_global_slide == 1:
                if 'active' not in sec_updated.split('class="')[1].split('"')[0]:
                    sec_updated = sec_updated.replace('class="slide ', 'class="slide active ')
            else:
                sec_updated = sec_updated.replace('active ', '').replace(' active', '')

            # Fix relative image paths: ../assets/ -> assets/
            sec_updated = sec_updated.replace('../assets/', 'assets/')
            
            all_sections.append(sec_updated)

            # Map cues
            if i in local_cues:
                combined_scripts[current_global_slide] = local_cues[i]

            current_global_slide += 1

    total_slides = current_global_slide - 1
    print(f"[OK] Extracted {total_slides} total slides successfully.")

    css_rel = "css/nothing.css"
    js_rel = "js/presentation.js"

    # Build final HTML matching FPGA Studio theme
    html_template = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FPGA STUDIO — KEYNOTE SLIDES</title>
    <!-- Tailwind CSS allowlisted -->
    <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Prompt:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{css_rel}">
</head>
<body class="h-screen w-screen flex flex-col justify-between p-6 relative">

    <!-- Interactive Warping Dot Matrix Canvas -->
    <canvas id="bg-canvas"></canvas>

    <!-- TOP GLYPH BAR / STATUS HEADER -->
    <header class="w-full flex items-center justify-between pb-4 border-b border-[#282828] z-20">
        <div class="flex items-center space-x-3">
            <span class="glyph-green-dot"></span>
            <span class="mono text-xs text-[#EAEAEA]/80 font-semibold tracking-widest uppercase">FPGA STUDIO // KEYNOTE SUITE</span>
            <span class="text-white/20 text-xs">|</span>
            <span class="mono text-xs text-[#1ED760]">v4.3 RELEASE</span>
        </div>

        <!-- Speaker Badge -->
        <div id="speaker-badge" class="px-4 py-1.5 rounded-full border border-[#282828] bg-[#1F1F1F]/90 text-xs font-medium mono tracking-wider flex items-center space-x-2">
            <span class="w-1.5 h-1.5 rounded-full bg-[#1ED760]"></span>
            <span id="speaker-text">SPEAKER 01 // THE VISION</span>
        </div>

        <div class="flex items-center space-x-4">
            <!-- Slide Counter -->
            <div class="mono text-sm font-bold tracking-widest text-[#EAEAEA]">
                <span id="current-slide-num">01</span> <span class="text-white/30">/</span> <span id="total-slide-num">{total_slides:02d}</span>
            </div>
            <!-- Fullscreen Button -->
            <button onclick="toggleFullscreen()" class="p-2 rounded-full border border-[#282828] hover:border-[#484848] hover:bg-[#2A2A2A] transition text-xs mono text-[#B3B3B3]" title="Full Screen (F)">
                ⛶
            </button>
        </div>
    </header>

    <!-- MAIN SLIDE CONTAINER -->
    <main class="flex-1 w-full flex items-center justify-center py-4 relative z-10 overflow-hidden">
{chr(10).join(all_sections)}
    </main>

    <!-- SPEAKER CUES DRAWER -->
    <div id="cues-drawer" class="fixed bottom-20 left-1/2 -translate-x-1/2 max-w-4xl w-[92%] bento-card p-5 border-[#484848] shadow-2xl z-40 hidden transition-all">
        <div class="flex justify-between items-center mb-2 border-b border-[#282828] pb-2">
            <div class="flex items-center space-x-2">
                <span class="glyph-red-dot"></span>
                <span class="mono text-xs text-red-400 font-bold uppercase" id="cue-title">SPEAKER CUE SHEET</span>
            </div>
            <button onclick="toggleCues()" class="text-xs mono text-white/50 hover:text-white">[ ปิด X ]</button>
        </div>
        <p id="cue-content" class="text-xs md:text-sm text-white/90 leading-relaxed whitespace-pre-line font-normal"></p>
    </div>

    <!-- BOTTOM CONTROL BAR -->
    <footer class="w-full flex items-center justify-between pt-4 border-t border-[#282828] z-20">
        <!-- Keyboard shortcuts tip -->
        <div class="mono text-[11px] text-[#727272] hidden md:flex items-center space-x-3">
            <span>[ ← ] PREV</span>
            <span>[ → ] NEXT</span>
            <span>[ SPACE ] ADVANCE</span>
            <span>[ F ] FULLSCREEN</span>
            <span>[ C ] CUES</span>
        </div>

        <!-- Speaker Script Toggle Pill -->
        <button onclick="toggleCues()" class="px-4 py-2 rounded-full border border-[#1ED760]/40 bg-emerald-950/30 hover:bg-emerald-900/40 text-[#1ED760] text-xs mono tracking-wider transition flex items-center space-x-2">
            <span>🎙️</span>
            <span>SPEAKER CUES (สคริปต์พูด)</span>
        </button>

        <!-- Navigation Buttons -->
        <div class="flex items-center space-x-3">
            <button onclick="prevSlide()" class="px-5 py-2 rounded-full border border-[#282828] bg-[#1F1F1F] hover:bg-[#2A2A2A] text-white mono text-xs tracking-wider transition">
                ← PREV
            </button>
            <button onclick="nextSlide()" class="px-5 py-2 rounded-full bg-white text-black hover:bg-neutral-200 mono text-xs font-bold tracking-wider transition shadow-lg">
                NEXT →
            </button>
        </div>
    </footer>

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

    print(f"[OK] Generated full presentation successfully: {OUTPUT_FILE}")

if __name__ == "__main__":
    compile_presentation()
