# 📱 FPGA Studio Presentation (Nothing Edition) — 4 Core Keynote Slides

สไลด์พรีเซนเทชัน 4 หน้ากระชับ ตรงเป้า พร้อมระบบ **Horizontal Carousel สไตล์เทรลเลอร์ Nothing Phone** ไร้ปุ่มกด และมี **ลูกศรแอมเบียนต์เรืองแสงตามระยะเมาส์**

---

## 📂 โครงสร้าง 4 สไลด์หลัก

```
fpga_studio/presentation/
│
├── 📄 index.html                      <-- เมนูเปิดสไลด์
├── 📄 presentation_all.html           <-- สไลด์รวม 4 แผ่นตัวเต็ม (ใช้พรีเซนต์จริง)
├── ⚙️ build.bat                       <-- ดับเบิลคลิกเพื่อรวมสไลด์ใหม่ทันที
├── 🐍 build_presentation.py           <-- สคริปต์คอมไพเลอร์
│
├── 📁 slides/
│   ├── 00_cover.html                  <-- [สไลด์ 1] หน้าปก: Glyph Motif & ลูกตามองตามเมาส์
│   ├── 01_features.html               <-- [สไลด์ 2] ฟีเจอร์: ตอบโจทย์อาจารย์ & ขุมพลัง IDE ทั้งระบบ
│   ├── 02_c_pipeline.html             <-- [สไลด์ 3] ท่อ C: C-TO-SILICON PIPELINE (Compile -> Pipeline -> MMIO)
│   └── 03_live_demo.html              <-- [สไลด์ 4] เดโม่จริง: Live Nexys A7 + GitHub QR Code สแกนลองในห้อง
│
├── 📁 css/nothing.css                 <-- สไตล์ Nothing Phone & Carousel Track
├── 📁 js/presentation.js              <-- Carousel Engine, Ambient Arrows, Micro Eye Tracking
└── 📁 assets/                         <-- ภาพโพสต์อาจารย์ & รูป QR Code ของ GitHub
```

---

## 🎯 เนื้อหา 4 สไลด์ & ผู้บรรยาย

| สไลด์ | ชื่อหัวข้อ | ผู้พูด | ไฮไลต์เนื้อหา |
| :---: | :--- | :---: | :--- |
| **01** | **COVER** | ทุกคน | เปิดตัว FPGA Studio, สถาปัตยกรรม Dual 32-bit RISC, สมาชิก 4 คน |
| **02** | **CORE FEATURES & THE CHALLENGE** | คนที่ 1 & 2 | ขยี้โพสต์อาจารย์ 13 และ 25 ก.ย. ("ไม่ต้องรอ 3 รุ่น ใครทำได้ให้ A -> วันนี้ทำเสร็จแล้ว!"), รวมฟีเจอร์เด็ด GCC Toolchain, Virtual Board, Custom CPU Import, วงจรหาร 28.88MHz, WSL Synthesis |
| **03** | **C-TO-SILICON PIPELINE** | คนที่ 2 & 3 | เส้นทางภาษา C สู่สัญญาณฮาร์ดแวร์: `main.c` $\rightarrow$ GCC $\rightarrow$ `link.ld` $\rightarrow$ `start.S` $\rightarrow$ BRAM $\rightarrow$ 5-Stage Pipeline พร้อมตาราง Address สั่งงานฮาร์ดแวร์จริง (LEDs, Switches, 7-Segment, UART `printf`, VGA) |
| **04** | **LIVE DEMO & GITHUB HANDOVER** | คนที่ 3 & 4 | รัน $10\text{C}3 = 120$ ออก 7-Segment สดๆ, สับสวิตช์/ไฟ LED, อัปโหลด USB 1 วินาที **พร้อมรูป QR Code บานใหญ่คมชัด** ให้ทุกคนในห้องสแกนดาวน์โหลด Setup.exe 599MB หรือดูโค้ดบน GitHub |

---

## 🕹️ การควบคุมขณะพรีเซนต์
- **คลิกซีกขวาของจอ (หรือกด `→` / `Spacebar`):** เลื่อนไปสไลด์ถัดไป (เลื่อนแนวนอนแบบเทรลเลอร์)
- **คลิกซีกซ้ายของจอ (หรือกด `←`):** เลื่อนย้อนกลับ
- **เลื่อนเมาส์เข้าใกล้ขอบจอ:** ลูกศรแอมเบียนต์กว้างๆ จะ **ค่อยๆ สว่างชัดขึ้นเรื่อยๆ** ตามระยะที่เมาส์เข้าใกล้
- **กดปุ่ม `F`:** เข้าโหมดเต็มจอ Fullscreen
- **กดปุ่ม `C`:** เปิด/ปิด ถาดโพยบทพูดภาษาไทย (Speaker Cues)
