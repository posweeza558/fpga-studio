# 📱 FPGA Studio Presentation (Nothing Edition) — แผนแยกไฟล์ทีม 4 คน

โฟลเดอร์นี้ออกแบบมาเพื่อให้สมาชิกในกลุ่มทั้ง 4 คน สามารถ**แยกกันแก้โค้ดสไลด์ของตัวเองได้อย่างอิสระ โดยไม่เกิดปัญหา Git Merge Conflict ชนกัน**

---

## 📂 โครงสร้างโฟลเดอร์

```
fpga_studio/presentation/
│
├── 📄 index.html                      <-- หน้าเปิดเลือกว่าจะรันตัวไหน (เปิดตัวนี้หรือตัวรวมก็ได้)
├── 📄 presentation_all.html           <-- สไลด์รวมตัวเต็ม 8 แผ่น (ใช้พรีเซนต์จริงหน้าห้อง)
├── ⚙️ build.bat                       <-- ดับเบิลคลิกเพื่อรวมสไลด์ใหม่ทันทีใน 0.1 วินาที!
├── 🐍 build_presentation.py           <-- สคริปต์คอมไพเลอร์รวมสไลด์
│
├── 📁 slides/                          <-- 【เพื่อนในกลุ่มแยกกันแก้ที่โฟลเดอร์นี้】
│   ├── 00_cover.html                  <-- หน้าปก & ทีมงาน (แก้ไขโดย: ส่วนกลาง / ทุกคน)
│   ├── 01_speaker1_challenge.html     <-- คนที่ 1: วิเคราะห์โพสต์อาจารย์ 13 และ 25 ก.ย.
│   ├── 02_speaker2_pipeline.html      <-- คนที่ 2: Software to Hardware Pipeline & MMIO
│   ├── 03_speaker3_demo.html          <-- คนที่ 3: Live Demo คำนวณจริง & บอร์ดจริง
│   └── 04_speaker4_superpowers.html   <-- คนที่ 4: ขุมพลัง Deep Tech & ส่งมอบงานขอเกรด A
│
├── 📁 css/
│   └── nothing.css                    <-- ธีม Nothing Phone (OLED Black, Glyphs, Bento Cards)
├── 📁 js/
│   └── presentation.js                <-- ระบบควบคุมสไลด์, คีย์บอร์ด, Fullscreen, โพยบทพูด
└── 📁 assets/
    ├── prof_post_sep13.png            <-- ภาพโพสต์อาจารย์ 13 ก.ย.
    └── prof_post_sep25.png            <-- ภาพโพสต์อาจารย์ 25 ก.ย.
```

---

## 👥 การแบ่งงานสำหรับสมาชิก 4 คน (ใครทำไฟล์ไหน)

| ผู้พูด | ไฟล์ที่ต้องแก้ | เนื้อหาหลัก |
| :--- | :--- | :--- |
| **ทุกคน / หน้าปก** | `slides/00_cover.html` | รายชื่อสมาชิกกลุ่ม, เลขกลุ่ม, ชื่อวิชา |
| **คนที่ 1** | `slides/01_speaker1_challenge.html` | ขยี้โพสต์อาจารย์ (3 ตัวเลือก & Computer ที่ต้องการ), ประกาศสร้าง IDE ไม่รอ 3 รุ่น |
| **คนที่ 2** | `slides/02_speaker2_pipeline.html` | ท่อส่งภาษา C สู่ FPGA, GCC, `link.ld`, Stack Pointer, ตาราง Address MMIO |
| **คนที่ 3** | `slides/03_speaker3_demo.html` | ตัวอย่าง Live Demo ($10\text{C}3 = 120$ ออก 7-Seg, UART `printf`, 1-Sec Upload) |
| **คนที่ 4** | `slides/04_speaker4_superpowers.html` | Custom CPU Import, Dual Arch MIPS/RISC-V, Multi-cycle Divider 28.88MHz, ตัวติดตั้ง 599MB, ขอเกรด A |

---

## 🛠️ ขั้นตอนการทำงาน (Workflow)

### 1. ทดสอบสไลด์ตัวเอง
- แต่ละคนสามารถ **ดับเบิลคลิกไฟล์ HTML ของตัวเองในโฟลเดอร์ `slides/`** (เช่น ดับเบิลคลิก `slides/01_speaker1_challenge.html`) เพื่อเปิดดูและแต่งหน้าตาใน Google Chrome หรือ Microsoft Edge ได้ทันที ไม่ต้องรันเซิร์ฟเวอร์
- แก้ไขข้อความ ปรับแต่งการ์ด Bento หรือแก้สคริปต์โพยพูดในตัวแปร `window.speakerScripts` ท้ายไฟล์

### 2. ส่งงานขึ้น GitHub (ปลอดภัย 100% ไม่ชนกัน)
- แต่ละคนแก้เฉพาะไฟล์ของตัวเองใน `slides/` เท่านั้น
- เวลา Commit & Push หรือสร้าง Pull Request จะไม่มีทางทับกับเพื่อน:
  ```bash
  git add slides/01_speaker1_challenge.html
  git commit -m "Update Speaker 1 slides and cue script"
  git push origin main (หรือ push ผ่าน branch ตัวเอง)
  ```

### 3. รวมสไลด์ทั้งหมดก่อนซ้อมพรีเซนต์
- เมื่อทุกคน Merge งานเข้าสู่กิ่งหลัก (`main`) เรียบร้อยแล้ว ให้ Pull โค้ดล่าสุดลงมา:
  ```bash
  git pull
  ```
- **ดับเบิลคลิกไฟล์ `build.bat`** (หรือพิมพ์คำสั่ง `python build_presentation.py`)
- สคริปต์จะดึงสไลด์และโพยพูดของทุกคนมารวมเป็น `presentation_all.html` ให้โดยอัตโนมัติภายใน 0.1 วินาที!

---

## ⌨️ คีย์ลัดตอนนำเสนอ (Keyboard Shortcuts)
- **`→` หรือ `Spacebar`**: ไปสไลด์ถัดไป
- **`←`**: ย้อนกลับสไลด์ก่อนหน้า
- **`F`**: สลับโหมดเต็มจอ (Fullscreen)
- **`C`**: เปิด/ปิด **ถาดโพยบทพูดภาษาไทย (Speaker Cues)**
