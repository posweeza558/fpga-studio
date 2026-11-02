/**
 * FPGA Studio - Nothing Phone Keynote Presentation Engine
 * Handles slide transitions, speaker cues, fullscreen, and keyboard shortcuts.
 */

let currentSlide = 1;
let totalSlides = 1;

function initPresentation() {
    const slides = document.querySelectorAll('.slide');
    totalSlides = slides.length;
    
    // Set total slide counter in header
    const totalElem = document.getElementById('total-slide-num');
    if (totalElem) {
        totalElem.innerText = String(totalSlides).padStart(2, '0');
    }

    updateSlide();
}

function updateSlide() {
    const slides = document.querySelectorAll('.slide');
    slides.forEach(s => s.classList.remove('active'));

    const activeSlide = document.querySelector(`.slide[data-slide="${currentSlide}"]`);
    if (activeSlide) {
        activeSlide.classList.add('active');

        // Update Counter
        const curElem = document.getElementById('current-slide-num');
        if (curElem) {
            curElem.innerText = String(currentSlide).padStart(2, '0');
        }

        // Update Speaker Header
        const speakerName = activeSlide.getAttribute('data-speaker') || "PRESENTATION";
        const speakerElem = document.getElementById('speaker-text');
        if (speakerElem) {
            speakerElem.innerText = speakerName;
        }

        // Update Speaker Cue Drawer
        const cueTitle = document.getElementById('cue-title');
        const cueContent = document.getElementById('cue-content');
        if (cueTitle) cueTitle.innerText = `${speakerName} // CUE SHEET`;
        if (cueContent) {
            const scripts = window.speakerScripts || {};
            cueContent.innerText = scripts[currentSlide] || "ไม่มีสคริปต์ในสไลด์นี้";
        }
    }
}

function nextSlide() {
    if (currentSlide < totalSlides) {
        currentSlide++;
        updateSlide();
    } else if (window.nextSectionUrl) {
        // Jump to next topic file if configured
        window.location.href = window.nextSectionUrl;
    }
}

function prevSlide() {
    if (currentSlide > 1) {
        currentSlide--;
        updateSlide();
    } else if (window.prevSectionUrl) {
        // Jump to previous topic file if configured
        window.location.href = window.prevSectionUrl;
    }
}

function toggleCues() {
    const drawer = document.getElementById('cues-drawer');
    if (drawer) {
        drawer.classList.toggle('hidden');
    }
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.warn(`Fullscreen error: ${err.message}`);
        });
    } else {
        document.exitFullscreen();
    }
}

// Global Keyboard Shortcuts
window.addEventListener('keydown', (e) => {
    // Avoid hijacking when typing in an input/textarea if any
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
        e.preventDefault();
        nextSlide();
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        prevSlide();
    } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        toggleFullscreen();
    } else if (e.key === 'c' || e.key === 'C') {
        e.preventDefault();
        toggleCues();
    }
});

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', initPresentation);
