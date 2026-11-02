/**
 * FPGA Studio - Keynote Presentation Engine (Nothing Phone Trailer & Carousel Edition)
 * - Seamless Horizontal Track Carousel (เลื่อนแนวนอนแบบเทรลเลอร์ Nothing Phone ไม่มีป็อปอัพเด้ง)
 * - Click anywhere to navigate (คลิกฝั่งซ้าย = ถอยหลัง / คลิกฝั่งขวา = เดินหน้า ไม่ต้องมีปุ่ม)
 * - Progressive Ambient Edge Arrows (เมาส์เข้าใกล้ขอบฝั่งไหน ลูกศรจะค่อยๆ สว่างชัดขึ้นเรื่อยๆ)
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
    setupEdgeArrows();

    const slides = document.querySelectorAll('.slide');
    totalSlides = slides.length;
    
    const totalElem = document.getElementById('total-slide-num');
    if (totalElem && totalSlides > 1) {
        totalElem.innerText = String(totalSlides).padStart(2, '0');
    }

    updateSlide();
    initDotMatrixCanvas();
    initOrbitStarfields();
    initPupilTracker();
    initGlobalClickNavigation();
}

// 2D Spatial Coordinates for Slides:
// Slide 1 (0,0) -> Slide 2 (1,0) -> Slide 3 (2,0) -> Slide 4 Video is ABOVE Slide 3 in space (2,-1) -> Slide 5 (3,-1)
function getSlideGridPos(indexZeroBased, total) {
    if (total <= 1) return { x: 0, y: 0 };
    const map = [
        { x: 0, y: 0 },  // Slide 1: Cover
        { x: 1, y: 0 },  // Slide 2: Origin Quest (3D Globe)
        { x: 2, y: 0 },  // Slide 3: Features (Planet Horizon)
        { x: 2, y: -1 }, // Slide 4: Pipeline Video (Camera ascends UP above the world!)
        { x: 3, y: -1 }  // Slide 5: Live Demo & GitHub (Deep Space Orbit)
    ];
    return map[indexZeroBased] || { x: indexZeroBased, y: 0 };
}

function setupCarouselDOM() {
    const main = document.querySelector('main');
    if (!main) return;

    let viewport = document.getElementById('carousel-viewport');
    let track = document.getElementById('carousel-track');
    if (!track) {
        if (!viewport) {
            viewport = document.createElement('div');
            viewport.id = 'carousel-viewport';
            main.appendChild(viewport);
        }

        track = document.createElement('div');
        track.id = 'carousel-track';
        viewport.appendChild(track);

        const slides = Array.from(main.querySelectorAll('.slide'));
        slides.forEach(s => track.appendChild(s));
    }

    if (viewport && !document.getElementById('global-space-stage')) {
        const spaceStage = document.createElement('div');
        spaceStage.id = 'global-space-stage';
        spaceStage.innerHTML = '<div class="fx-nebula"></div><div class="fx-grid"></div>';
        viewport.insertBefore(spaceStage, viewport.firstChild);
    }

    const slides = Array.from(track.querySelectorAll('.slide'));
    if (slides.length > 1) {
        track.classList.add('track-2d');
        slides.forEach((s, idx) => {
            const pos = getSlideGridPos(idx, slides.length);
            s.style.left = `${pos.x * 100}vw`;
            s.style.top  = `${pos.y * 100}vh`;
        });
    }
    carouselTrack = track;
}

function setupEdgeArrows() {
    if (document.getElementById('edge-arrow-left')) return;

    // Create Left Edge Arrow
    const leftArrow = document.createElement('div');
    leftArrow.id = 'edge-arrow-left';
    leftArrow.className = 'edge-arrow edge-arrow-left';
    leftArrow.innerHTML = `
        <svg viewBox="0 0 64 140" fill="none" stroke="currentColor">
            <path d="M48 20 L16 70 L48 120" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `;

    // Create Right Edge Arrow
    const rightArrow = document.createElement('div');
    rightArrow.id = 'edge-arrow-right';
    rightArrow.className = 'edge-arrow edge-arrow-right';
    rightArrow.innerHTML = `
        <svg viewBox="0 0 64 140" fill="none" stroke="currentColor">
            <path d="M16 20 L48 70 L16 120" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `;

    document.body.appendChild(leftArrow);
    document.body.appendChild(rightArrow);
}

let lastSlideIndex = 0;

function isOriginQuestSlide(el) {
    return Boolean(el && (el.id === 'origin-quest-slide' || el.getAttribute('data-slide') === '2'));
}

function updateSlide() {
    const slides = document.querySelectorAll('.slide');
    if (!slides.length) return;

    const prevIdx = lastSlideIndex;
    lastSlideIndex = currentSlide;

    if (carouselTrack) {
        if ( slides.length > 1 ) {
            const pos = getSlideGridPos(currentSlide - 1, slides.length);
            const tx = -pos.x * 100;
            const ty = -pos.y * 100;
            carouselTrack.style.transform = `translate3d(${tx}vw, ${ty}vh, 0)`;
        } else {
            const offsetPercent = (currentSlide - 1) * 100;
            carouselTrack.style.transform = `translate3d(-${offsetPercent}%, 0, 0)`;
        }
    }

    slides.forEach((s, idx) => {
        if (idx === currentSlide - 1) {
            s.classList.add('active');
        } else {
            s.classList.remove('active');
        }
    });

    const activeSlide = slides[currentSlide - 1] || document.querySelector(`.slide[data-slide="${currentSlide}"]`);
    const slideKey = totalSlides > 1 ? currentSlide : (Number(activeSlide?.getAttribute('data-slide')) || currentSlide);

    // Show Top HUD Bar ONLY on Slide 1
    const hud = document.querySelector('.fx-hud');
    if (hud) {
        if (slideKey === 1) {
            hud.classList.remove('hud-hidden');
        } else {
            hud.classList.add('hud-hidden');
        }
    }

    const curElem = document.getElementById('current-slide-num');
    if (curElem && totalSlides > 1) {
        curElem.innerText = String(currentSlide).padStart(2, '0');
    }

    const speakerName = activeSlide ? activeSlide.getAttribute('data-speaker') || "PRESENTATION" : "PRESENTATION";
    
    const cueTitle = document.getElementById('cue-title');
    const cueContent = document.getElementById('cue-content');
    if (cueTitle) cueTitle.innerText = `${speakerName} // CUE SHEET`;
    if (cueContent) {
        const scripts = window.speakerScripts || {};
        cueContent.innerText = scripts[slideKey] || scripts[currentSlide] || "ไม่มีสคริปต์ในสไลด์นี้";
    }

    // Hook: Sync Origin Quest 3D Globe across Slide 1 <-> Slide 2 <-> Slide 3 (forward & backward)
    if (typeof window.syncOriginQuestSlide === 'function') {
        window.syncOriginQuestSlide(slideKey, prevIdx);
    } else if (isOriginQuestSlide(activeSlide) && typeof window.enterOriginQuest === 'function') {
        const dir = (prevIdx > currentSlide) ? 'backward' : 'forward';
        window.enterOriginQuest(dir);
    }

    // Hook: If arriving on slide 3 (Arc Carousel Slide), initialize/update arc positions immediately
    if (currentSlide === 3) {
        if (typeof window.initArcCarousel === 'function') {
            window.initArcCarousel();
        } else if (typeof window.updateArcPositions === 'function') {
            window.updateArcPositions();
        }
    }

    // Hook: Auto-play / pause Pipeline Video on Slide 4
    const pipeVid = document.getElementById('pipeline-video');
    if (pipeVid) {
        if (slideKey === 4) {
            pipeVid.play().catch(() => {
                pipeVid.muted = true;
                pipeVid.play().catch(() => {});
            });
        } else {
            pipeVid.pause();
        }
    }

    // Trigger Nothing dot-matrix scramble on active slide's [data-scramble] elements
    if (activeSlide) {
        triggerSlideScramble(activeSlide);
    }

    // Refresh arrows immediately on slide change
    updateEdgeArrows(mouse.x);
}

function nextSlide() {
    const slides = document.querySelectorAll('.slide');
    const activeSlide = slides[currentSlide - 1];
    if (isOriginQuestSlide(activeSlide) && typeof window.stepOriginQuest === 'function') {
        if (window.stepOriginQuest(1)) {
            updateEdgeArrows(mouse.x);
            return;
        }
    }

    if (currentSlide < totalSlides) {
        currentSlide++;
        updateSlide();
    } else if (window.nextSectionUrl) {
        window.location.href = window.nextSectionUrl;
    }
}

function prevSlide() {
    const slides = document.querySelectorAll('.slide');
    const activeSlide = slides[currentSlide - 1];
    if (isOriginQuestSlide(activeSlide) && typeof window.stepOriginQuest === 'function') {
        if (window.stepOriginQuest(-1)) {
            updateEdgeArrows(mouse.x);
            return;
        }
    }

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
// 2. DYNAMIC AMBIENT EDGE ARROWS & CLICK NAVIGATION
// ==============================================================================

function updateEdgeArrows(mouseX) {
    const leftArrow = document.getElementById('edge-arrow-left');
    const rightArrow = document.getElementById('edge-arrow-right');
    if (!leftArrow || !rightArrow) return;

    if (mouseX < 0) {
        leftArrow.style.opacity = '0';
        rightArrow.style.opacity = '0';
        return;
    }

    const width = window.innerWidth;
    const activationZone = width * 0.38; // 38% from edge starts fading in

    // Left Arrow: increases intensity as cursor gets closer to the left edge
    const canGoPrev = currentSlide > 1 || window.prevSectionUrl;
    if (canGoPrev && mouseX < activationZone) {
        const ratio = 1 - (mouseX / activationZone);
        const opacity = Math.min(Math.pow(ratio, 1.2), 0.95);
        leftArrow.style.opacity = opacity;
        leftArrow.style.transform = `translateY(-50%) translateX(${-12 * (1 - ratio)}px)`;
    } else {
        leftArrow.style.opacity = '0';
    }

    // Right Arrow: increases intensity as cursor gets closer to the right edge
    const canGoNext = currentSlide < totalSlides || window.nextSectionUrl;
    const distFromRight = width - mouseX;
    if (canGoNext && distFromRight < activationZone) {
        const ratio = 1 - (distFromRight / activationZone);
        const opacity = Math.min(Math.pow(ratio, 1.2), 0.95);
        rightArrow.style.opacity = opacity;
        rightArrow.style.transform = `translateY(-50%) translateX(${12 * (1 - ratio)}px)`;
    } else {
        rightArrow.style.opacity = '0';
    }
}

function initGlobalClickNavigation() {
    window.addEventListener('click', (e) => {
        if (e.target.closest('button, a, input, select, textarea, #cues-drawer, [data-no-nav]')) {
            return;
        }

        const selection = window.getSelection();
        if (selection && selection.toString().length > 0) {
            return;
        }

        const screenWidth = window.innerWidth;
        const clickX = e.clientX;

        // Click Left 44% = Previous, Click Right 56% = Next
        if (clickX < screenWidth * 0.44) {
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
        updateEdgeArrows(e.clientX);
    });

    window.addEventListener('mouseleave', () => {
        mouse.targetX = -9999;
        mouse.targetY = -9999;
        mouse.active = false;
        updateEdgeArrows(-9999);
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

    // Micro movement limit: strictly max 3.2px (ฟีลลูกตา ขยับนิดเดียวในวงกลาง)
    const maxRadius = 3.2;
    const angle = Math.atan2(dy, dx);

    const strength = Math.min(dist / 350, 1) * maxRadius;

    const targetX = Math.cos(angle) * strength;
    const targetY = Math.sin(angle) * strength;

    pupilX += (targetX - pupilX) * 0.12;
    pupilY += (targetY - pupilY) * 0.12;

    tracker.style.transform = `translate3d(${pupilX.toFixed(2)}px, ${pupilY.toFixed(2)}px, 0)`;
}

// ==============================================================================
// 5. ORBIT LAUNCH STARFIELD & DOT-MATRIX HEADLINE SCRAMBLE
// ==============================================================================

function scrambleTextElement(el, finalText) {
    if (!el || !finalText) return;
    if (window.location.search.includes('settle=1') || window.location.search.includes('side=2')) {
        el.textContent = finalText;
        return;
    }
    const glyphs = '01#%&*+<>/=?ABCDEFXYZ';
    const len = finalText.length;
    let frame = 0;
    const totalFrames = 20;
    if (el._raf) cancelAnimationFrame(el._raf);
    const tick = () => {
        let out = '';
        for (let i = 0; i < len; i++) {
            const ch = finalText[i];
            const revealAt = (i / len) * totalFrames * 0.8;
            if (ch === ' ' || frame >= revealAt + 5) out += ch;
            else out += glyphs[Math.floor(Math.random() * glyphs.length)];
        }
        el.textContent = out;
        frame++;
        if (frame <= totalFrames + 5) {
            el._raf = requestAnimationFrame(tick);
        } else {
            el.textContent = finalText;
        }
    };
    tick();
}

function triggerSlideScramble(slideEl) {
    const items = slideEl.querySelectorAll('[data-scramble]');
    items.forEach((el) => {
        const target = el.getAttribute('data-scramble') || el.textContent;
        scrambleTextElement(el, target);
    });
}

function initOrbitStarfields() {
    const canvases = Array.from(document.querySelectorAll('canvas.fx-stars:not(#fx-stars)'));
    if (!canvases.length) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let mx = 0, my = 0;
    window.addEventListener('mousemove', (e) => {
        mx = (e.clientX / window.innerWidth - 0.5);
        my = (e.clientY / window.innerHeight - 0.5);
    });

    const states = canvases.map((canvas) => ({
        canvas,
        ctx: canvas.getContext('2d'),
        W: 0,
        H: 0,
        stars: [],
        shooting: null,
        slide: canvas.closest('.slide')
    }));

    function resizeState(st) {
        const r = st.canvas.getBoundingClientRect();
        const w = r.width || window.innerWidth - 48;
        const h = r.height || window.innerHeight - 100;
        if (!w || !h) return;
        st.W = w;
        st.H = h;
        st.canvas.width = w * dpr;
        st.canvas.height = h * dpr;
        st.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        const count = Math.round((w * h) / 5200);
        st.stars = Array.from({ length: count }, () => ({
            x: Math.random() * w,
            y: Math.random() * h,
            z: Math.random() * 0.9 + 0.1,
            p: Math.random() * Math.PI * 2,
            tw: 0.6 + Math.random() * 1.8,
            g: Math.random() < 0.14
        }));
    }

    states.forEach(resizeState);
    window.addEventListener('resize', () => states.forEach(resizeState));

    function frame(t) {
        requestAnimationFrame(frame);
        const time = t / 1000;
        for (const st of states) {
            if (st.slide && !st.slide.classList.contains('active')) continue;
            if (!st.W) { resizeState(st); if (!st.W) continue; }
            const { ctx, W, H, stars } = st;
            ctx.clearRect(0, 0, W, H);
            for (const s of stars) {
                s.x -= s.z * 0.06;
                if (s.x < -4) s.x = W + 4;
                const a = (0.35 + 0.65 * (0.5 + 0.5 * Math.sin(time * s.tw + s.p))) * s.z;
                const x = s.x - mx * 22 * s.z;
                const y = s.y - my * 14 * s.z;
                const size = s.z * 1.4;
                ctx.fillStyle = s.g ? `rgba(120,255,170,${a})` : `rgba(255,255,255,${a})`;
                ctx.fillRect(x, y, size, size);
            }
            if (!st.shooting && Math.random() < 0.004) {
                st.shooting = { x: Math.random() * W * 0.7 + W * 0.2, y: Math.random() * H * 0.35, l: 0 };
            }
            if (st.shooting) {
                st.shooting.l += 14;
                const sx = st.shooting.x - st.shooting.l;
                const sy = st.shooting.y + st.shooting.l * 0.35;
                const grad = ctx.createLinearGradient(sx, sy, sx + 120, sy - 42);
                grad.addColorStop(0, 'rgba(190,255,215,0.9)');
                grad.addColorStop(1, 'rgba(190,255,215,0)');
                ctx.strokeStyle = grad;
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(sx + 120, sy - 42);
                ctx.stroke();
                if (st.shooting.l > W * 0.5) st.shooting = null;
            }
        }
    }
    requestAnimationFrame(frame);
}

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', initPresentation);
