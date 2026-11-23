# -*- coding: utf-8 -*-
"""
FPGA Studio — WSL Local Hardware Synthesis Dialog
Enables running open-source hardware synthesis (openXC7, Yosys, nextpnr)
directly on the user's PC via Windows Subsystem for Linux (WSL).
"""

import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from config.theme import (
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_PURPLE,
    ACCENT_WARN,
    BG_BLACK,
    BG_CARD,
    BG_DARK,
    BG_EDITOR,
    BG_ELEVATED,
    BG_PILL_ACT,
    BG_PILL_INACT,
    BORDER_COLOR,
    FONT_CODE,
    FONT_UI,
    TXT_BRIGHT,
    TXT_DIM,
    TXT_PRIMARY,
    TXT_MUTED,
)
from core.wsl_synthesis import (
    check_wsl_status,
    launch_wsl_install,
    run_wsl_synthesis,
)
from ui.installer_wizard import BaseFramelessWizardDialog
from ui import dialog_kit as kit
from ui.widgets import SpotifyAutoScrollbar


class WSLSynthesisDialog(BaseFramelessWizardDialog):
    """
    WSL Local Synthesis Wizard Dialog.
    Detects WSL status, offers 1-click install if missing, and runs local synthesis.
    """

    def __init__(
        self,
        parent,
        cpu_name: str = "openmips",
        cpu_arch: str = "mips",
        cpu_hdl_path: Optional[str] = None,
        board_name: str = "Digilent Nexys A7-100T (Artix-7)",
        project_dir: Optional[str] = None,
        on_bitstream_ready: Optional[Callable[[str], None]] = None,
    ):
        self.cpu_name = cpu_name
        self.cpu_arch = cpu_arch
        self.cpu_hdl_path = cpu_hdl_path
        self.board_name = board_name
        self.project_dir = project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.on_bitstream_ready = on_bitstream_ready
        self.is_running = False

        super().__init__(
            parent,
            f"สังเคราะห์ Bitstream ผ่าน WSL ({cpu_name})",
            840,
            660,
        )

        self._build_ui()
        self._refresh_wsl_status()

    START_IDLE = "เริ่มสังเคราะห์"
    START_BUSY = "กำลังสังเคราะห์..."

    def _build_ui(self):
        body = tk.Frame(self.container, bg=BG_BLACK)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # ---- WSL status: one line of state, one line of detail, actions on the right
        status = tk.Frame(body, bg=BG_BLACK)
        status.pack(fill=tk.X)
        act_box = tk.Frame(status, bg=BG_BLACK)
        act_box.pack(side=tk.RIGHT)
        self.btn_refresh = kit.button(act_box, "ตรวจสอบใหม่", self._refresh_wsl_status, kind="link")
        self.btn_refresh.pack(side=tk.RIGHT)
        self.btn_install_wsl = kit.button(act_box, "ติดตั้ง WSL (Ubuntu)", self._install_wsl_clicked)
        stat_info = tk.Frame(status, bg=BG_BLACK)
        stat_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_status_title = tk.Label(stat_info, text="กำลังตรวจสอบ WSL...", bg=BG_BLACK,
                                         fg=TXT_BRIGHT, font=(FONT_UI, 10, "bold"), anchor="w")
        self.lbl_status_title.pack(fill=tk.X)
        self.lbl_status_desc = tk.Label(stat_info, text="", bg=BG_BLACK, fg=TXT_MUTED,
                                        font=(FONT_UI, 9), anchor="w")
        self.lbl_status_desc.pack(fill=tk.X, pady=(2, 0))
        self.lbl_status_icon = tk.Label(stat_info)     # kept for older call sites; not shown

        # ---- target
        cfg = tk.Frame(body, bg=BG_BLACK)
        cfg.pack(fill=tk.X, pady=(14, 0))
        for i, (k, v) in enumerate((("CPU", f"{self.cpu_name} ({self.cpu_arch.upper()})"),
                                    ("บอร์ด", self.board_name))):
            tk.Label(cfg, text=k, bg=BG_BLACK, fg=TXT_MUTED, font=(FONT_UI, 9)).pack(
                side=tk.LEFT, padx=(0 if i == 0 else 24, 8))
            tk.Label(cfg, text=v, bg=BG_BLACK, fg=TXT_BRIGHT, font=(FONT_UI, 9)).pack(side=tk.LEFT)

        # ---- footer (packed before the log so it stays visible)
        footer = tk.Frame(body, bg=BG_BLACK)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(14, 0))
        self.btn_start = kit.button(footer, self.START_IDLE, self._start_wsl_synthesis_thread, kind="primary")
        self.btn_start.pack(side=tk.LEFT)
        kit.button(footer, "ปิด", self.destroy, kind="link").pack(side=tk.RIGHT)

        # ---- log
        kit.section_label(body, "บันทึก").pack(fill=tk.X, pady=(16, 6))
        con_frame = tk.Frame(body, bg=BG_EDITOR, highlightthickness=1, highlightbackground=BORDER_COLOR)
        con_frame.pack(fill=tk.BOTH, expand=True)
        self.txt_log = tk.Text(con_frame, bg=BG_EDITOR, fg=TXT_PRIMARY, font=(FONT_CODE, 9), wrap="char",
                               bd=0, padx=10, pady=8, insertbackground=TXT_BRIGHT)
        sb = SpotifyAutoScrollbar(con_frame, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._log(f"เป้าหมาย: CPU '{self.cpu_name}', บอร์ด '{self.board_name}'")

    def _log(self, text: str):
        def _append():
            self.txt_log.insert(tk.END, text + "\n")
            self.txt_log.see(tk.END)

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self.after(0, _append)

    def _refresh_wsl_status(self):
        self.lbl_status_title.config(text="กำลังตรวจสอบ WSL...", fg=TXT_BRIGHT)
        self.lbl_status_desc.config(text="")
        self.btn_install_wsl.pack_forget()

        def worker():
            status = check_wsl_status()

            def update():
                if not self.winfo_exists():     # dialog closed while the check ran
                    return
                if status["installed"] and status["distros"]:
                    distro = status.get("default_distro") or "Linux"
                    self.lbl_status_icon.config(text="")
                    self.lbl_status_title.config(text=f"WSL พร้อมใช้งาน ({distro})", fg=TXT_BRIGHT)
                    tool_desc = []
                    if status["tools"].get("yosys"):
                        tool_desc.append("Yosys")
                    if status["tools"].get("docker"):
                        tool_desc.append("Docker")
                    desc = f"เครื่องมือที่พบ: {', '.join(tool_desc)}" if tool_desc else "ยังไม่มี Yosys/Docker ใน WSL สคริปต์จะติดตั้งให้ตอนเริ่มสังเคราะห์"
                    self.lbl_status_desc.config(text=desc)
                    self.btn_start.config(state=tk.NORMAL)
                    self._log(f"✓ ตรวจพบ WSL Linux: {distro}")
                elif status["installed"]:
                    self.lbl_status_icon.config(text="⏳")
                    self.lbl_status_title.config(text="WSL ติดตั้งแล้ว แต่ยังไม่มี Ubuntu", fg=ACCENT_WARN)
                    self.lbl_status_desc.config(text="รอหน้าต่าง cmd.exe ติดตั้ง Ubuntu ให้เสร็จ แล้วกด 'ตรวจสอบใหม่'")
                    self.btn_install_wsl.config(text="ติดตั้ง Ubuntu")
                    self.btn_install_wsl.pack(side=tk.RIGHT, padx=(0, 12))
                    self.btn_start.config(state=tk.DISABLED)
                    self._log("WSL ติดตั้งแล้ว กำลังรอติดตั้ง Ubuntu ในหน้าต่าง cmd.exe")
                else:
                    self.lbl_status_icon.config(text="")
                    self.lbl_status_title.config(text="ยังไม่ได้ติดตั้ง WSL", fg=ACCENT_WARN)
                    self.lbl_status_desc.config(text="การสังเคราะห์ใช้ Linux ผ่าน WSL กด 'ติดตั้ง WSL (Ubuntu)' เพื่อติดตั้ง")
                    self.btn_install_wsl.config(text="ติดตั้ง WSL (Ubuntu)")
                    self.btn_install_wsl.pack(side=tk.RIGHT, padx=(0, 12))
                    self.btn_start.config(state=tk.DISABLED)
                    self._log("ยังไม่ได้ติดตั้ง WSL กด 'ติดตั้ง WSL (Ubuntu)' เพื่อติดตั้ง")

            self.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def _install_wsl_clicked(self):
        ans = messagebox.askyesno(
            "ติดตั้ง WSL (Windows Subsystem for Linux)",
            "ระบบจะเปิดหน้าต่าง Command Prompt (สิทธิ์ Administrator) เพื่อรันคำสั่ง:\n\n"
            "wsl --install\n\n"
            "• เป็นฟีเจอร์มาตรฐานของ Windows\n"
            "• จะติดตั้ง Linux (Ubuntu) ลงในเครื่องโดยอัตโนมัติ\n"
            "• หลังจากติดตั้งเสร็จ อาจต้อง Restart เครื่อง 1 ครั้ง\n\n"
            "ต้องการเริ่มติดตั้งทันทีหรือไม่?",
            parent=self,
        )
        if ans:
            self._log("กำลังเรียกตัวติดตั้ง 'wsl --install' ผ่าน Administrator Shell...")
            launch_wsl_install()
            messagebox.showinfo(
                "กำลังติดตั้ง WSL",
                "เปิดหน้าต่างติดตั้ง WSL แล้ว\n\nกด 'Yes' ที่หน้าต่าง UAC ของ Windows แล้วรอให้ดาวน์โหลดในหน้าต่าง cmd.exe เสร็จ",
                parent=self,
            )

    def _start_wsl_synthesis_thread(self):
        if self.is_running:
            return

        self.is_running = True
        kit.set_primary_busy(self.btn_start, True, self.START_IDLE, self.START_BUSY)

        def worker():
            self._log("\n" + "=" * 60)
            self._log(f"เริ่มสังเคราะห์ CPU '{self.cpu_name}' ผ่าน WSL")
            
            ok, msg, out_bit = run_wsl_synthesis(
                project_dir=self.project_dir,
                cpu_name=self.cpu_name,
                cpu_arch=self.cpu_arch,
                cpu_hdl_path=self.cpu_hdl_path,
                on_log=self._log,
            )

            def done():
                self.is_running = False
                kit.set_primary_busy(self.btn_start, False, self.START_IDLE, self.START_BUSY)
                if ok and out_bit and os.path.isfile(out_bit):
                    self._log(f"\n✓ {msg}")
                    if self.on_bitstream_ready:
                        self.on_bitstream_ready(out_bit)
                    messagebox.showinfo(
                        "สังเคราะห์สำเร็จ",
                        f"สร้าง Bitstream แล้ว: {os.path.basename(out_bit)}\n\nแฟลชลงบอร์ดได้จากหน้าต่างแฟลช",
                        parent=self,
                    )
                    self.destroy()
                elif ok:
                    self._log(f"\n{msg}")
                    messagebox.showinfo("การสังเคราะห์ใน WSL", msg, parent=self)
                else:
                    self._log(f"\n✗ ข้อผิดพลาด: {msg}")
                    messagebox.showerror("การสังเคราะห์ใน WSL ไม่สำเร็จ", msg, parent=self)

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()
