# -*- coding: utf-8 -*-
"""
FPGA Studio — Direct In-App FPGA Hardware Programmer & Bitstream Flasher Dialog
Frameless Spotify Dark Modal Window allowing 1-click flashing of synthesizable CPU bitstreams
(.bit) directly onto the connected FPGA board (Digilent Nexys A7-100T, Virtex-6, Basys 3, etc.)
without opening external Vivado windows.

Supports:
  - Built-in OpenMIPS 32-bit CPU
  - Built-in RISC-V RV32I 32-bit CPU
  - All User Custom CPUs (imported Verilog / VHDL modules)
  - 1-Click SoC Vivado synthesis wrapper generation
"""

import glob
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from config.theme import (
    ACCENT_AMBER,
    ACCENT_GREEN,
    ACCENT_RED,
    BG_ACTIVITY,
    BG_BLACK,
    BG_EDITOR,
    BG_ELEVATED,
    BG_HOVER,
    BG_PANEL,
    BG_PILL_ACT,
    BG_PILL_INACT,
    BG_SIDEBAR,
    BORDER_COLOR,
    BORDER_HOVER,
    FONT_CODE,
    FONT_UI,
    TXT_BRIGHT,
    TXT_DIM,
    TXT_MUTED,
    TXT_PRIMARY,
)
from core.fpga_programmer import (
    detect_all_fpga_programmers,
    find_djtgcfg_binary,
    find_openfpgaloader_binary,
    find_vivado_binary,
    program_fpga_with_djtgcfg,
    program_fpga_with_openfpgaloader,
    program_fpga_with_vivado,
)
from ui.installer_wizard import BaseFramelessWizardDialog
from ui.widgets import SpotifyAutoScrollbar, SpotifyPillButton
from ui import dialog_kit as kit

ACCENT_CYAN = "#38BDF8"  # Sky blue accent for Open-Source Toolchain


class FPGAProgrammerDialog(BaseFramelessWizardDialog):
    """Direct In-App FPGA Hardware Flasher & JTAG Bitstream Loader Dialog."""

    def __init__(
        self,
        parent,
        current_arch: str = "openmips",
        active_arch_val: str = "",
        custom_cpus: Optional[List[dict]] = None,
        project_dir: Optional[str] = None,
        compiled_ins: Optional[list] = None,
        on_success_callback=None,
    ):
        self.current_arch = current_arch or "openmips"
        self.active_arch_val = active_arch_val or ""
        self.custom_cpus = custom_cpus or []
        self.project_dir = project_dir or os.getcwd()
        self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.compiled_ins = compiled_ins or []
        self.on_success_callback = on_success_callback
        self.is_flashing = False

        # Scan for available programmer backends (check app toolchain dir first)
        toolchain_path = os.path.join(self.app_dir, "toolchain")
        if not os.path.exists(toolchain_path):
            toolchain_path = os.path.join(self.project_dir, "toolchain")
        self.programmers = detect_all_fpga_programmers(toolchain_dir=toolchain_path)

        super().__init__(
            parent,
            "แฟลช CPU ลงบอร์ด FPGA",
            900,
            660,
        )
        self._build_ui()
        self._on_cpu_selection_changed()

    FLASH_IDLE = "แฟลชลงบอร์ด"
    FLASH_BUSY = "กำลังแฟลช..."

    def _build_ui(self):
        body = tk.Frame(self.container, bg=BG_BLACK, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        # ---- form: label column + control column, aligned on one grid
        form = tk.Frame(body, bg=BG_BLACK)
        form.pack(fill=tk.X)
        form.columnconfigure(1, weight=1)

        def label(row, text):
            tk.Label(form, text=text, bg=BG_BLACK, fg=TXT_MUTED, font=(FONT_UI, 9),
                     anchor="w").grid(row=row, column=0, sticky="w", padx=(0, 16), pady=5)

        label(0, "บอร์ด")
        self.board_var = tk.StringVar(value="Digilent Nexys A7-100T (Artix-7)")
        cb_board = ttk.Combobox(
            form, textvariable=self.board_var, state="readonly", font=(FONT_UI, 9),
            values=[
                "Digilent Nexys A7-100T (Artix-7)",
                "Digilent Nexys A7-50T (Artix-7)",
                "Digilent Basys 3 (Artix-7)",
                "AMD Virtex-6 Connectivity Kit (XC6VLX240T)",
                "บอร์ด FPGA ทั่วไป (Generic JTAG)",
            ],
        )
        cb_board.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

        label(1, "CPU")
        self.cpu_map = {}
        mips_label = "OpenMIPS 32-bit (MDU, 7-Segment)"
        self.cpu_map[mips_label] = {"kind": "builtin", "arch": "mips", "name": "openmips", "path": None}
        riscv_label = "RISC-V RV32I 32-bit (MDU, 7-Segment)"
        self.cpu_map[riscv_label] = {"kind": "builtin", "arch": "riscv", "name": "riscv", "path": None}
        demo_label = "Nexys A7 Factory Demo (ทดสอบบอร์ด)"
        self.cpu_map[demo_label] = {"kind": "demo", "arch": "demo", "name": "factory_demo", "path": None}
        gpio_label = "Nexys A7 Switch-to-LED (สวิตช์ 16 ตัว แสดงที่ LED และ 7-Segment)"
        self.cpu_map[gpio_label] = {"kind": "demo", "arch": "demo", "name": "gpio_demo", "path": None}
        for c in self.custom_cpus:
            c_name = c.get("name", "Custom CPU")
            c_arch = c.get("arch", "Generic")
            lbl = f"{c_name} (Custom, {c_arch})"
            self.cpu_map[lbl] = {"kind": "custom", "arch": c_arch, "name": c_name, "path": c.get("path")}

        default_lbl = mips_label
        if self.active_arch_val.startswith("custom:"):
            c_path = self.active_arch_val.split("custom:", 1)[1]
            for lbl, info in self.cpu_map.items():
                if info.get("path") == c_path or info.get("name") == os.path.basename(c_path):
                    default_lbl = lbl
                    break
        elif "riscv" in self.current_arch.lower():
            default_lbl = riscv_label

        self.cpu_core_var = tk.StringVar(value=default_lbl)
        cb_cpu = ttk.Combobox(form, textvariable=self.cpu_core_var, values=list(self.cpu_map.keys()),
                              state="readonly", font=(FONT_UI, 9))
        cb_cpu.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        cb_cpu.bind("<<ComboboxSelected>>", lambda e: self._on_cpu_selection_changed())

        label(2, "Bitstream")
        self.bit_path_var = tk.StringVar(value="")
        e_bit = tk.Entry(form, textvariable=self.bit_path_var, bg=BG_EDITOR, fg=TXT_BRIGHT,
                         insertbackground=TXT_BRIGHT, bd=0, highlightthickness=1,
                         highlightbackground=BORDER_COLOR, highlightcolor=BORDER_HOVER, font=(FONT_CODE, 9))
        e_bit.grid(row=2, column=1, sticky="ew", pady=5, ipady=4)
        kit.button(form, "เลือกไฟล์...", self._browse_bitstream).grid(row=2, column=2, sticky="e", padx=(8, 0))

        # building a bitstream gets its own row (these used to crowd the CPU row and clip)
        label(3, "สร้าง Bitstream")
        build_row = tk.Frame(form, bg=BG_BLACK)
        build_row.grid(row=3, column=1, columnspan=2, sticky="w", pady=5)
        kit.button(build_row, "สร้างแพ็กเกจ Vivado SoC", self._start_synthesis_thread).pack(side=tk.LEFT)
        kit.button(build_row, "สังเคราะห์ผ่าน WSL", self._open_wsl_synthesis_dialog).pack(side=tk.LEFT, padx=(8, 0))
        from core.open_synthesizer import detect_synthesis_engines
        if not detect_synthesis_engines().get("yosys"):
            kit.button(build_row, "ติดตั้ง OSS CAD Suite",
                       lambda: self._start_install_oss_cad_suite(auto_synthesize_after=False)
                       ).pack(side=tk.LEFT, padx=(8, 0))

        label(4, "เครื่องมือแฟลช")
        eng_row = tk.Frame(form, bg=BG_BLACK)
        eng_row.grid(row=4, column=1, columnspan=2, sticky="ew", pady=5)
        eng_text, eng_color = self._get_engine_status_summary()
        self.lbl_eng_status = tk.Label(eng_row, text=eng_text, bg=BG_BLACK, fg=eng_color, font=(FONT_UI, 9))
        self.lbl_eng_status.pack(side=tk.LEFT)
        kit.button(eng_row, "ระบุตำแหน่ง Vivado...", self._browse_vivado, kind="link").pack(side=tk.RIGHT)
        kit.button(eng_row, "ติดตั้งไดรเวอร์ USB (Zadig)", self._open_zadig, kind="link").pack(side=tk.RIGHT, padx=(0, 4))

        # ---- action bar (packed before the log so it is never pushed off-screen)
        act_bar = tk.Frame(body, bg=BG_BLACK)
        act_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(14, 0))
        self.btn_flash = kit.button(act_bar, self.FLASH_IDLE, self._start_flashing_thread, kind="primary")
        self.btn_flash.pack(side=tk.LEFT)
        kit.button(act_bar, "อัปโหลดโปรแกรมผ่าน USB-UART", self._call_parent_uart_upload,
                   pady=7).pack(side=tk.LEFT, padx=(8, 0))
        kit.button(act_bar, "ปิด", self.destroy, kind="link").pack(side=tk.RIGHT)

        # ---- log
        kit.section_label(body, "บันทึกการแฟลช").pack(fill=tk.X, pady=(16, 6))
        card_log = tk.Frame(body, bg=BG_EDITOR, padx=10, pady=8, highlightthickness=1,
                            highlightbackground=BORDER_COLOR)
        card_log.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(
            card_log, bg=BG_EDITOR, fg=TXT_PRIMARY, bd=0, highlightthickness=0,
            font=(FONT_CODE, 9), wrap=tk.WORD, spacing1=2, spacing3=2,
            selectbackground=BG_HOVER, insertbackground=TXT_BRIGHT,
        )
        log_scroll = SpotifyAutoScrollbar(card_log, command=self.log_text.yview, bg_track=BG_EDITOR)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._log("เลือก CPU และต่อสาย USB ของบอร์ด แล้วกด 'แฟลชลงบอร์ด'")

    def _on_cpu_selection_changed(self):
        sel = self.cpu_core_var.get()
        info = self.cpu_map.get(sel, {})
        core_name = info.get("name", "openmips")
        c_path = info.get("path")

        # Auto-detect bitstream with priority to pre-bundled bitstreams
        cands = [
            os.path.join(self.app_dir, "bitstreams", f"nexys_a7_{core_name}.bit"),
            os.path.join(self.project_dir, "bitstreams", f"nexys_a7_{core_name}.bit"),
            os.path.join(self.project_dir, f"vivado_nexys_a7_{core_name}", "vivado_proj", "fpga_studio_nexys_a7.runs", "impl_1", "nexys_a7_soc_top.bit"),
            os.path.join(self.project_dir, f"top_{core_name}.bit"),
            os.path.join(self.project_dir, f"{core_name}.bit"),
            os.path.join(self.project_dir, "top.bit"),
        ]
        if c_path and os.path.exists(c_path):
            c_dir = os.path.dirname(c_path)
            cands.extend(glob.glob(os.path.join(c_dir, "*.bit")))
            cands.extend(glob.glob(os.path.join(c_dir, "**", "*.bit"), recursive=True))

        found = None
        for c in cands:
            if os.path.isfile(c):
                found = c
                break

        if found:
            self.bit_path_var.set(found)
            self._log(f"✓ โหลด Bitstream สำเร็จรูปสำหรับ '{core_name}': {os.path.basename(found)}")
        else:
            self.bit_path_var.set("")
            if info.get("kind") == "custom":
                self._log(f"CPU ที่ผู้ใช้เพิ่มเอง '{core_name}': เลือกไฟล์ .bit หรือกด 'สร้างแพ็กเกจ Vivado สำหรับ CPU นี้'")
            else:
                self._log(f"ยังไม่พบไฟล์ .bit สำหรับ '{core_name}' — สามารถกดเลือกไฟล์ .bit หรือสร้างแพ็กเกจ Vivado")

    def _open_wsl_synthesis_dialog(self):
        """Open WSL Local Hardware Synthesis modal dialog."""
        sel = self.cpu_core_var.get()
        info = self.cpu_map.get(sel, {})
        core_name = info.get("name", "openmips")
        core_arch = "mips" if "mips" in info.get("arch", "").lower() or "openmips" in core_name.lower() else "riscv"
        c_path = info.get("path")

        from ui.wsl_synthesis_dialog import WSLSynthesisDialog

        def on_ready(bit_path):
            self.bit_path_var.set(bit_path)
            self._log(f"✓ เลือกไฟล์ Bitstream จาก WSL อัตโนมัติ: {os.path.basename(bit_path)}")

        WSLSynthesisDialog(
            parent=self,
            cpu_name=core_name,
            cpu_arch=core_arch,
            cpu_hdl_path=c_path,
            board_name=self.board_var.get(),
            project_dir=self.project_dir,
            on_bitstream_ready=on_ready,
        )

    def _open_cloud_synthesis_dialog(self):
        """Open Cloud Synthesis modal dialog (GitHub Actions)."""
        sel = self.cpu_core_var.get()
        info = self.cpu_map.get(sel, {})
        core_name = info.get("name", "openmips")
        core_arch = "mips" if "mips" in info.get("arch", "").lower() or "openmips" in core_name.lower() else "riscv"
        c_path = info.get("path")

        from ui.cloud_synthesis_dialog import CloudSynthesisDialog

        def on_ready(bit_path):
            self.bit_path_var.set(bit_path)
            self._log(f"✓ เลือกไฟล์ Bitstream จาก Cloud อัตโนมัติ: {os.path.basename(bit_path)}")

        CloudSynthesisDialog(
            parent=self,
            cpu_name=core_name,
            cpu_arch=core_arch,
            cpu_hdl_path=c_path,
            board_name=self.board_var.get(),
            project_dir=self.project_dir,
            on_bitstream_ready=on_ready,
        )

    def _start_synthesis_thread(self):
        """Run In-App Synthesis Pipeline in background thread."""
        sel = self.cpu_core_var.get()
        info = self.cpu_map.get(sel, {})
        core_name = info.get("name", "openmips")
        core_arch = "mips" if "mips" in info.get("arch", "").lower() or "openmips" in core_name.lower() else "riscv"
        c_path = info.get("path")

        from core.open_synthesizer import synthesize_soc_bitstream

        def worker():
            ok, msg, out_bit = synthesize_soc_bitstream(
                project_dir=self.project_dir,
                cpu_name=core_name,
                cpu_arch=core_arch,
                cpu_hdl_path=c_path,
                board_name=self.board_var.get(),
                on_log=self._log,
            )

            def done():
                if ok and out_bit and os.path.isfile(out_bit):
                    self.bit_path_var.set(out_bit)
                    self._log(f"\n✓ {msg}")
                    ans = messagebox.askyesno(
                        "สังเคราะห์สำเร็จ",
                        f"สังเคราะห์ Bitstream สำหรับ '{core_name}' สำเร็จเรียบร้อย!\n\n"
                        f"ไฟล์: {os.path.basename(out_bit)}\n\n"
                        "คุณต้องการเริ่มแฟลชลงบอร์ด FPGA ผ่านสาย USB ทันทีเลยหรือไม่?",
                        parent=self,
                    )
                    if ans:
                        self._start_flashing_thread()
                elif ok:
                    self._log(f"\n📁 {msg}")
                    ans = messagebox.askyesno(
                        "สร้างแพ็กเกจ SoC สำเร็จ (ต้องการติดตั้ง OSS Toolchain?)",
                        f"ระบบสร้างแพ็กเกจ SoC Auto-Wrapper สำหรับ '{core_name}' เสร็จสมบูรณ์แล้ว!\n\n"
                        f"สถานะ: {msg}\n\n"
                        "แต่ในเครื่องของคุณยังไม่มีตัวสังเคราะห์เพื่อแปลงเป็นไฟล์ Bitstream (.bit)\n\n"
                        "คุณต้องการให้ FPGA Studio ดาวน์โหลดและติดตั้ง Open-Source Toolchain (OSS CAD Suite ~600MB)\n"
                        "ลงในตัวแอปอัตโนมัติหรือไม่?\n\n"
                        "✓ ฟรี 100% ไม่ต้องติดตั้ง Vivado (50-80GB) ให้หนักเครื่อง\n"
                        "✓ รองรับการสังเคราะห์เป็น .bit ในโปรแกรมโดยตรง",
                        parent=self,
                    )
                    if ans:
                        self._start_install_oss_cad_suite(auto_synthesize_after=True)
                else:
                    self._log(f"\n✗ ข้อผิดพลาด: {msg}")
                    messagebox.showerror("การสังเคราะห์ล้มเหลว", msg, parent=self)

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _start_install_oss_cad_suite(self, auto_synthesize_after: bool = False):
        """Download and install OSS CAD Suite in background thread."""
        from core.open_synthesizer import install_oss_cad_suite

        def worker():
            self._log("\n" + "=" * 65)
            self._log("เริ่มดาวน์โหลดและติดตั้ง OSS CAD Suite (Yosys + NextPNR)...")
            self._log("=" * 65)
            ok, msg = install_oss_cad_suite(on_log=self._log)

            def done():
                if ok:
                    self._log(f"\n✓ {msg}")
                    messagebox.showinfo("ติดตั้งสำเร็จ", msg, parent=self)
                    if auto_synthesize_after:
                        self._start_synthesis_thread()
                else:
                    self._log(f"\n✗ {msg}")
                    messagebox.showerror("การติดตั้งล้มเหลว", msg, parent=self)

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _generate_soc_package_for_selected_cpu(self):
        """Generate ready-to-synthesize Vivado package for the selected CPU."""
        self._start_synthesis_thread()

    def _get_engine_status_summary(self):
        if self.programmers.get("openfpgaloader"):
            return "openFPGALoader (มากับโปรแกรม)", ACCENT_GREEN
        if self.programmers.get("vivado"):
            p = self.programmers["vivado"]
            base = os.path.basename(os.path.dirname(os.path.dirname(p)))
            return f"Xilinx Vivado CLI ({base})", ACCENT_GREEN
        if self.programmers.get("djtgcfg"):
            return "Digilent Adept CLI (djtgcfg)", ACCENT_GREEN
        return "ไม่พบเครื่องมือแฟลช JTAG", ACCENT_AMBER

    def _browse_bitstream(self):
        f = filedialog.askopenfilename(
            parent=self,
            title="เลือกไฟล์ FPGA Bitstream (.bit)",
            filetypes=[("FPGA Bitstream", "*.bit"), ("All files", "*.*")],
            initialdir=os.path.join(self.app_dir, "bitstreams"),
        )
        if f:
            self.bit_path_var.set(f)
            self._log(f"เลือกไฟล์ Bitstream: {f}")

    def _open_zadig(self):
        """Launch bundled Zadig tool to switch Interface 0 to WinUSB."""
        cands = [
            os.path.join(self.app_dir, "toolchain", "zadig.exe"),
            os.path.join(self.project_dir, "toolchain", "zadig.exe"),
            os.path.join(self.app_dir, "_internal", "toolchain", "zadig.exe"),
        ]
        found = None
        for c in cands:
            if os.path.isfile(c):
                found = c
                break
        if found:
            self._log("กำลังเปิดโปรแกรม Zadig ด้วยสิทธิ์ Administrator (UAC)...")
            try:
                if os.name == "nt":
                    import ctypes
                    # ShellExecuteW with 'runas' prompts Windows UAC cleanly without WinError 740
                    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", found, None, None, 1)
                    if ret <= 32:
                        os.startfile(found)
                else:
                    import subprocess
                    subprocess.Popen([found])
                self._log("✓ ส่งคำขอเปิด Zadig เรียบร้อย (โปรดกดยืนยัน 'Yes' ในหน้าต่าง UAC):")
                self._log("   1. ใน Zadig คลิกเมนู 'Options' -> ติ๊ก 'List All Devices'")
                self._log("   2. ช่องบนเลือก 'USB Serial Converter A' หรือ 'Digilent USB Device (Interface 0)'")
                self._log("   3. ช่องขวาเลือก 'WinUSB' แล้วกดปุ่ม 'Replace Driver'")
            except Exception as e:
                self._log(f"✗ ไม่สามารถเปิด Zadig อัตโนมัติ: {e}")
                self._log(f"คลิกขวาที่ไฟล์นี้แล้วกด 'Run as administrator' ได้โดยตรง:")
                self._log(f"   {found}")
        else:
            import webbrowser
            self._log("กำลังเปิดหน้าดาวน์โหลด Zadig (https://zadig.akeo.ie/)...")
            webbrowser.open("https://zadig.akeo.ie/")

    def _browse_vivado(self):
        f = filedialog.askopenfilename(
            parent=self,
            title="ระบุตำแหน่งไฟล์ vivado.bat หรือ vivado_lab.bat",
            filetypes=[("Vivado Executable", "*.bat;*.exe"), ("All files", "*.*")],
            initialdir=r"C:\Xilinx",
        )
        if f and os.path.isfile(f):
            self.programmers["vivado"] = f
            txt, col = self._get_engine_status_summary()
            self.lbl_eng_status.config(text=txt, fg=col)
            self._log(f"ตั้งค่าเส้นทาง Vivado สำเร็จ: {f}")

    def _log(self, text: str):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _call_parent_uart_upload(self):
        if hasattr(self.master, "upload_to_board"):
            self.destroy()
            self.master.upload_to_board()

    def _start_flashing_thread(self):
        if self.is_flashing:
            return

        bit_path = self.bit_path_var.get().strip()
        if not bit_path or not os.path.isfile(bit_path):
            messagebox.showwarning(
                "ไม่พบไฟล์ Bitstream",
                "กรุณาระบุไฟล์ .bit ของ CPU ก่อนเริ่มแฟลช\n\n"
                "คุณสามารถกดปุ่ม 'เลือกไฟล์ .bit...' เพื่อเลือก Bitstream สำเร็จรูป\n"
                "หรือกด '⬆ อัปโหลดโค้ด MIPS / C (USB UART)' เพื่อรันโค้ดบนบอร์ดทันที",
                parent=self,
            )
            return

        prog_type = None
        prog_bin = None
        # Prioritize bundled lightweight openFPGALoader so users never need 50GB Vivado!
        if self.programmers.get("openfpgaloader"):
            prog_type = "openfpgaloader"
            prog_bin = self.programmers["openfpgaloader"]
        elif self.programmers.get("vivado"):
            prog_type = "vivado"
            prog_bin = self.programmers["vivado"]
        elif self.programmers.get("djtgcfg"):
            prog_type = "djtgcfg"
            prog_bin = self.programmers["djtgcfg"]

        if not prog_bin:
            messagebox.showinfo(
                "ต้องการเครื่องมือแฟลช JTAG",
                "ไม่พบเครื่องมือแฟลชบอร์ด FPGA ในระบบ\n\n"
                "โปรดตรวจสอบว่าโฟลเดอร์ toolchain/openFPGALoader อยู่ในโปรแกรม\n"
                "หรือกดปุ่ม 'ระบุตำแหน่ง Vivado...' เพื่อเลือกไฟล์ vivado.bat\n"
                "หรือหากบอร์ดได้แฟลช CPU ไว้อยู่แล้ว ให้ใช้ปุ่ม 'อัปโหลดโค้ด MIPS / C (USB UART)'",
                parent=self,
            )
            return

        self.is_flashing = True
        kit.set_primary_busy(self.btn_flash, True, self.FLASH_IDLE, self.FLASH_BUSY)
        sel_cpu = self.cpu_core_var.get()
        self._log("\n" + "=" * 65)
        self._log(f"เริ่มแฟลช CPU: {sel_cpu}")
        self._log(f"เป้าหมาย: บอร์ด {self.board_var.get()}")
        self._log(f"ไฟล์ Bitstream: {bit_path}")
        self._log(f"เครื่องมือแฟลช: {prog_type} ({os.path.basename(prog_bin)})")
        self._log("=" * 65)

        def worker():
            ok = False
            msg = ""
            device_hint = "xc7a100t"
            if "50t" in self.board_var.get().lower():
                device_hint = "xc7a50t"
            elif "basys" in self.board_var.get().lower():
                device_hint = "xc7a35t"
            elif "virtex" in self.board_var.get().lower():
                device_hint = "xc6v"

            try:
                if prog_type == "openfpgaloader":
                    ok, msg = program_fpga_with_openfpgaloader(prog_bin, bit_path, board=self.board_var.get(), on_log=self._log)
                elif prog_type == "vivado":
                    ok, msg = program_fpga_with_vivado(prog_bin, bit_path, device_hint=device_hint, on_log=self._log)
                elif prog_type == "djtgcfg":
                    ok, msg = program_fpga_with_djtgcfg(prog_bin, bit_path, on_log=self._log)
            except Exception as ex:
                ok = False
                msg = str(ex)

            def done():
                self.is_flashing = False
                kit.set_primary_busy(self.btn_flash, False, self.FLASH_IDLE, self.FLASH_BUSY)
                if ok:
                    self._log(f"\n✓ {msg}")
                    messagebox.showinfo("แฟลชสำเร็จ", msg, parent=self)
                    if self.on_success_callback:
                        self.on_success_callback()
                else:
                    self._log(f"\n✗ ข้อผิดพลาด: {msg}")
                    if "unable to open ftdi" in msg.lower() or "usb_open" in msg.lower():
                        self._log("\n" + "=" * 65)
                        self._log("พบบอร์ด แต่ Windows ยังไม่ให้สิทธิ์ WinUSB:")
                        self._log("1. ในหน้าต่าง Zadig ที่กำลังเปิด ให้ไปที่ Options -> ติ๊ก 'List All Devices'")
                        self._log("2. ช่อง Dropdown เลือก 'USB Serial Converter A' หรือ 'Digilent USB Device (Interface 0)'")
                        self._log("3. ฝั่งขวา (Target Driver) เลือกเป็น 'WinUSB' แล้วกดปุ่ม 'Replace Driver'")
                        self._log("4. รอ 5 วินาที แล้วกลับมากด 'แฟลชลงบอร์ด' อีกครั้ง")
                        self._log("=" * 65)
                        ans = messagebox.askyesno(
                            "ต้องเปิดสิทธิ์ไดรเวอร์ JTAG (ทำครั้งเดียว)",
                            "ตรวจพบบอร์ด FPGA เสียบสาย USB อยู่แล้ว แต่ระบบ Windows กำหนดไดรเวอร์เดิม (FTDIBUS) ล็อกพอร์ต JTAG ไว้\n\n"
                            "วิธีแก้ไขง่ายมากใน 1 นาที (ทำครั้งเดียวตลอดชีพ ไม่ต้องลง Vivado):\n"
                            "1. เปิด Zadig (กด 'Yes' ด้านล่างเพื่อเปิดทันที)\n"
                            "2. ไปที่เมนู Options -> ติ๊ก 'List All Devices'\n"
                            "3. ในช่อง Dropdown เลือก 'USB Serial Converter A' (หรือ Interface 0)\n"
                            "4. ทางขวาเลือก 'WinUSB' แล้วกดปุ่ม 'Replace Driver'\n\n"
                            "คุณต้องการเปิดโปรแกรม Zadig เพื่อสลับไดรเวอร์ตอนนี้หรือไม่?",
                            parent=self,
                        )
                        if ans:
                            self._open_zadig()
                    else:
                        messagebox.showerror("การแฟลชล้มเหลว", msg, parent=self)

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()
