# 📱 FPGA Studio Presentation (Nothing Edition) — 5 Core Keynote Slides

สไลด์พรีเซนเทชัน 5 หน้ากระชับ ตรงเป้า พร้อมระบบ **Horizontal Carousel สไตล์เทรลเลอร์ Nothing Phone** ไร้ปุ่มกด และมี **ลูกศรแอมเบียนต์เรืองแสงตามระยะเมาส์**

---

## 📂 โครงสร้าง 5 สไลด์หลัก

```
fpga_studio/presentation/
│
├── 📄 index.html                      <-- เมนูเปิดสไลด์
├── 📄 presentation_all.html           <-- สไลด์รวม 5 แผ่นตัวเต็ม (ใช้พรีเซนต์จริง)
├── ⚙️ build.bat                       <-- ดับเบิลคลิกเพื่อรวมสไลด์ใหม่ทันที
├── 🐍 build_presentation.py           <-- สคริปต์คอมไพเลอร์
│
├── 📁 slides/
│   ├── 00_cover.html                  <-- [สไลด์ 1] หน้าปก: Glyph Motif & ลูกตามองตามเมาส์
│   ├── 01_challenge.html              <-- [สไลด์ 2] โจทย์อาจารย์: โพสต์ 13 ก.ย. & 25 ก.ย. พร้อมการตีความโจทย์
│   ├── 02_features.html               <-- [สไลด์ 3] ฟีเจอร์ 7 ข้อเต็ม: สถาปัตยกรรม & ขุมพลังทั้งระบบ
│   ├── 03_c_pipeline.html             <-- [สไลด์ 4] ท่อ C: C-TO-SILICON PIPELINE (Compile -> Pipeline -> MMIO)
│   └── 04_live_demo.html              <-- [สไลด์ 5] เดโม่จริง: Live Nexys A7 + GitHub QR Code สแกนลองในห้อง
│
├── 📁 css/nothing.css                 <-- สไตล์ Nothing Phone & Carousel Track
├── 📁 js/presentation.js              <-- Carousel Engine, Ambient Arrows, Micro Eye Tracking
└── 📁 assets/                         <-- ภาพโพสต์อาจารย์ & รูป QR Code ของ GitHub
```

---

## 🎯 เนื้อหา 5 สไลด์ & ผู้บรรยาย

| สไลด์ | ชื่อหัวข้อ | ผู้พูด | ไฮไลต์เนื้อหา |
| :---: | :--- | :---: | :--- |
| **01** | **COVER** | ทุกคน | เปิดตัว FPGA Studio, สถาปัตยกรรม Dual 32-bit RISC, สมาชิกกลุ่ม |
| **02** | **THE ORIGIN CHALLENGE & INTERPRETATION** | คนที่ 1 | โพสต์อาจารย์ 13 และ 25 ก.ย. ("ไม่ต้องรอ 3 รุ่น ใครทำได้ให้ A") พร้อม **การตีความโจทย์**: รวบทำทั้ง 3 ทางเลือก, ทำตัวหารฮาร์ดแวร์ 32 ไซเคิล, และสร้าง All-in-One EDA Studio |
| **03** | **7 CORE SYSTEM FEATURES** | คนที่ 2 | ขุมพลัง 7 ข้อเต็ม: 5-Stage Dual-Core, Custom CPU Engine (HDL AST Parser + MMIO), Virtual Nexys A7 Board, Debugger (32 Regs + GTKWave), C Runtime (start.S + link.ld), 1-Sec Fast Flash + WSL Yosys, และ Export ครบ 6 ฟอร์แมต |
| **04** | **C-TO-SILICON PIPELINE** | คนที่ 3 | เส้นทางภาษา C สู่สัญญาณฮาร์ดแวร์: `main.c` $\rightarrow$ GCC $\rightarrow$ `link.ld` $\rightarrow$ `start.S` $\rightarrow$ BRAM $\rightarrow$ 5-Stage Pipeline พร้อมตาราง Address สั่งงานฮาร์ดแวร์จริง (`0xF0000000` LEDs, `0xF0000004` SW, `0xF0000008` 7-Seg, `0xF0000010` UART `printf`, `0xFF000000` VGA) |
| **05** | **LIVE DEMO & GITHUB HANDOVER** | คนที่ 4 | รัน $10\text{C}3 = 120$ ออก 7-Segment สดๆ, สับสวิตช์/ไฟ LED, อัปโหลด USB 1 วินาที **พร้อมรูป QR Code บานใหญ่คมชัด** ให้ทุกคนในห้องสแกนดาวน์โหลด Setup.exe 599MB หรือดูโค้ดบน GitHub |

---

## 🕹️ การควบคุมขณะพรีเซนต์
- **คลิกซีกขวาของจอ (หรือกด `→` / `Spacebar`):** เลื่อนไปสไลด์ถัดไป (เลื่อนแนวนอนแบบเทรลเลอร์)
- **คลิกซีกซ้ายของจอ (หรือกด `←`):** เลื่อนย้อนกลับ
- **เลื่อนเมาส์เข้าใกล้ขอบจอ:** ลูกศรแอมเบียนต์กว้างๆ จะ **ค่อยๆ สว่างชัดขึ้นเรื่อยๆ** ตามระยะที่เมาส์เข้าใกล้
- **กดปุ่ม `F`:** เข้าโหมดเต็มจอ Fullscreen
- **กดปุ่ม `C`:** เปิด/ปิด ถาดโพยบทพูดภาษาไทย (Speaker Cues)
