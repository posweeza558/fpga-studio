/**
 * FPGA Studio - Keynote Presentation Engine (Nothing Phone Trailer / Carousel Edition)
 * - Seamless Horizontal Track Carousel (เลื่อนแนวนอนแบบเทรลเลอร์ Nothing Phone ไม่มีป็อปอัพเด้ง)
 * - Click anywhere to navigate (คลิกฝั่งซ้าย = ถอยหลัง / คลิกฝั่งขวา = เดินหน้า ไม่ต้องมีปุ่ม)
 * - Micro Pupil Eye Tracking (จุดแดงขยับนิดเดียวฟีลลูกตามองตามเมาส์)
 * - Interactive Elastic Dot-Matrix Canvas Background
 */

let currentSlide = 1;
let totalSlides = 1;
let carouselTrack = null;

// Mouse coordinates
const mouse = {
    x: -9999,
    y: -9999,
    targetX: -9999,
    targetY: -9999,
    radius: 145,
    strength: 30,
    active: false
};

// Micro pupil tracking
let pupilX = 0;
let pupilY = 0;

// ==============================================================================
// 1. CAROUSEL ENGINE (NOTHING PHONE TRAILER HORIZONTAL SWEEP)
// ==============================================================================

function initPresentation() {
    setupCarouselDOM();

    const slides = document.querySelectorAll('.slide');
    totalSlides = slides.length;
    
    const totalElem = document.getElementById('total-slide-num');
    if (totalElem) {
        totalElem.innerText = String(totalSlides).padStart(2, '0');
    }

    updateSlide();
    initDotMatrixCanvas();
    initPupilTracker();
    initGlobalClickNavigation();
}

function setupCarouselDOM() {
    const main = document.querySelector('main');
    if (!main) return;

    let track = document.getElementById('carousel-track');
    if (!track) {
        // Create viewport wrapper if missing
        let viewport = document.getElementById('carousel-viewport');
        if (!viewport) {
            viewport = document.createElement('div');
            viewport.id = 'carousel-viewport';
            main.appendChild(viewport);
        }

        track = document.createElement('div');
        track.id = 'carousel-track';
        viewport.appendChild(track);

        // Move all slide sections into the carousel track
        const slides = Array.from(main.querySelectorAll('.slide'));
        slides.forEach(s => track.appendChild(s));
    }
    carouselTrack = track;
}

function updateSlide() {
    const slides = document.querySelectorAll('.slide');
    if (!slides.length) return;

    // Cinematic horizontal track translation (Nothing Phone trailer sweep)
    if (carouselTrack) {
        const offsetPercent = (currentSlide - 1) * 100;
        carouselTrack.style.transform = `translate3d(-${offsetPercent}%, 0, 0)`;
    }

    slides.forEach((s, idx) => {
        if (idx === currentSlide - 1) {
            s.classList.add('active');
        } else {
            s.classList.remove('active');
        }
    });

    // Update Counter
    const curElem = document.getElementById('current-slide-num');
    if (curElem) {
        curElem.innerText = String(currentSlide).padStart(2, '0');
    }

    // Update Speaker Cue Drawer
    const activeSlide = document.querySelector(`.slide[data-slide="${currentSlide}"]`);
    const speakerName = activeSlide ? activeSlide.getAttribute('data-speaker') || "PRESENTATION" : "PRESENTATION";
    
    const cueTitle = document.getElementById('cue-title');
    const cueContent = document.getElementById('cue-content');
    if (cueTitle) cueTitle.innerText = `${speakerName} // CUE SHEET`;
    if (cueContent) {
        const scripts = window.speakerScripts || {};
        cueContent.innerText = scripts[currentSlide] || "ไม่มีสคริปต์ในสไลด์นี้";
    }
}

function nextSlide() {
    if (currentSlide < totalSlides) {
        currentSlide++;
        updateSlide();
    } else if (window.nextSectionUrl) {
        window.location.href = window.nextSectionUrl;
    }
}

function prevSlide() {
    if (currentSlide > 1) {
        currentSlide--;
        updateSlide();
    } else if (window.prevSectionUrl) {
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

// ==============================================================================
// 2. CLICK ANYWHERE NAVIGATION (คลิกฝั่งซ้าย = ย้อนกลับ, คลิกฝั่งขวา = เดินหน้า)
// ==============================================================================

function initGlobalClickNavigation() {
    window.addEventListener('click', (e) => {
        // Ignore clicks on buttons, links, inputs, cues drawer, or if text is selected
        if (e.target.closest('button, a, input, select, textarea, #cues-drawer, [data-no-nav]')) {
            return;
        }

        const selection = window.getSelection();
        if (selection && selection.toString().length > 0) {
            return;
        }

        const screenWidth = window.innerWidth;
        const clickX = e.clientX;

        // Left 42% = Previous Slide | Right 58% = Next Slide
        if (clickX < screenWidth * 0.42) {
            prevSlide();
        } else {
            nextSlide();
        }
    });
}

// Global Keyboard Navigation
window.addEventListener('keydown', (e) => {
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


// ==============================================================================
// 3. INTERACTIVE ELASTIC DOT MATRIX CANVAS (จุดๆ พื้นหลังยวบยาบ)
// ==============================================================================

class Dot {
    constructor(x, y) {
        this.originX = x;
        this.originY = y;
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.radius = 1.35;
        this.baseAlpha = 0.16;
        this.alpha = this.baseAlpha;
    }

    update(mouseX, mouseY, radius, strength) {
        const dx = mouseX - this.originX;
        const dy = mouseY - this.originY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        let targetX = this.originX;
        let targetY = this.originY;
        let targetAlpha = this.baseAlpha;

        if (dist < radius && dist > 0) {
            const force = Math.pow(1 - dist / radius, 1.8);
            const angle = Math.atan2(dy, dx);
            
            targetX = this.originX - Math.cos(angle) * force * strength;
            targetY = this.originY - Math.sin(angle) * force * strength;
            
            targetAlpha = this.baseAlpha + force * 0.45;
        }

        const spring = 0.07;
        const friction = 0.82;

        const ax = (targetX - this.x) * spring;
        const ay = (targetY - this.y) * spring;

        this.vx = (this.vx + ax) * friction;
        this.vy = (this.vy + ay) * friction;

        this.x += this.vx;
        this.y += this.vy;

        this.alpha += (targetAlpha - this.alpha) * 0.15;
    }

    draw(ctx) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        
        if (this.alpha > 0.28) {
            ctx.fillStyle = `rgba(30, 215, 96, ${this.alpha * 0.75})`;
        } else {
            ctx.fillStyle = `rgba(235, 235, 235, ${this.alpha})`;
        }
        ctx.fill();
    }
}

function initDotMatrixCanvas() {
    let canvas = document.getElementById('bg-canvas');
    if (!canvas) {
        canvas = document.createElement('canvas');
        canvas.id = 'bg-canvas';
        document.body.prepend(canvas);
    }

    const ctx = canvas.getContext('2d', { alpha: true });
    let dots = [];
    const spacing = 28;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        buildGrid();
    }

    function buildGrid() {
        dots = [];
        const cols = Math.ceil(canvas.width / spacing) + 1;
        const rows = Math.ceil(canvas.height / spacing) + 1;

        const offsetX = (canvas.width - (cols - 1) * spacing) / 2;
        const offsetY = (canvas.height - (rows - 1) * spacing) / 2;

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const x = offsetX + c * spacing;
                const y = offsetY + r * spacing;
                dots.push(new Dot(x, y));
            }
        }
    }

    window.addEventListener('resize', resize);
    resize();

    window.addEventListener('mousemove', (e) => {
        mouse.targetX = e.clientX;
        mouse.targetY = e.clientY;
        mouse.active = true;
    });

    window.addEventListener('mouseleave', () => {
        mouse.targetX = -9999;
        mouse.targetY = -9999;
        mouse.active = false;
    });

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        mouse.x += (mouse.targetX - mouse.x) * 0.15;
        mouse.y += (mouse.targetY - mouse.y) * 0.15;

        for (let i = 0; i < dots.length; i++) {
            dots[i].update(mouse.x, mouse.y, mouse.radius, mouse.strength);
            dots[i].draw(ctx);
        }

        updatePupil();

        requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
}


// ==============================================================================
// 4. MICRO PUPIL EYE TRACKING (จุดแดงขยับนิดเดียวฟีลลูกตามองตามเมาส์)
// ==============================================================================

function initPupilTracker() {
    const pupil = document.getElementById('eye-pupil');
    if (pupil && !document.getElementById('eye-pupil-tracker')) {
        const parent = pupil.parentElement;
        const wrapper = document.createElement('div');
        wrapper.id = 'eye-pupil-tracker';
        wrapper.style.display = 'flex';
        wrapper.style.alignItems = 'center';
        wrapper.style.justifyContent = 'center';
        wrapper.style.position = 'relative';
        wrapper.style.width = '100%';
        wrapper.style.height = '100%';
        wrapper.style.pointerEvents = 'none';

        parent.insertBefore(wrapper, pupil);
        wrapper.appendChild(pupil);
    }
}

function updatePupil() {
    const tracker = document.getElementById('eye-pupil-tracker');
    const outerCircle = document.getElementById('eye-outer');

    if (!tracker || !outerCircle) return;

    const rect = outerCircle.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const dx = (mouse.targetX !== -9999 ? mouse.targetX : centerX) - centerX;
    const dy = (mouse.targetY !== -9999 ? mouse.targetY : centerY) - centerY;
    const dist = Math.sqrt(dx * dx + dy * dy);

    // Subtle micro-pupil movement: strictly max 5.5px
    const maxRadius = 5.5;
    const angle = Math.atan2(dy, dx);

    const strength = Math.min(dist / 350, 1) * maxRadius;

    const targetX = Math.cos(angle) * strength;
    const targetY = Math.sin(angle) * strength;

    pupilX += (targetX - pupilX) * 0.12;
    pupilY += (targetY - pupilY) * 0.12;

    tracker.style.transform = `translate3d(${pupilX.toFixed(2)}px, ${pupilY.toFixed(2)}px, 0)`;
}

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', initPresentation);
