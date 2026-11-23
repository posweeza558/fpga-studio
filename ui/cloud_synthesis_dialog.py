# -*- coding: utf-8 -*-
"""
FPGA Studio — Cloud Synthesis Dialog (GitHub Actions CI/CD)
Provides an intuitive GUI for 1-Click Zero-Vivado Bitstream Generation.
"""

import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from config.theme import (
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_WARN,
    BG_BLACK,
    BG_CARD,
    BG_DARK,
    BG_EDITOR,
    BG_ELEVATED,
    BG_PILL_INACT,
    BORDER_COLOR,
    BORDER_HOVER,
    FONT_CODE,
    FONT_UI,
    TXT_BRIGHT,
    TXT_DIM,
    TXT_MUTED,
    TXT_PRIMARY,
)
from core.cloud_synthesis import (
    check_github_repo_workflow,
    download_synthesized_bitstream_from_url,
    export_cloud_bundle_zip,
    get_latest_workflow_run,
    get_run_artifacts,
    trigger_cloud_synthesis_workflow,
)
from ui.installer_wizard import BaseFramelessWizardDialog
from ui import dialog_kit as kit
from ui.widgets import SpotifyAutoScrollbar, SpotifyPillButton

ACCENT_PURPLE = "#A78BFA"


class CloudSynthesisDialog(BaseFramelessWizardDialog):
    """Dialog for automated Cloud Bitstream Synthesis via GitHub Actions."""

    def __init__(
        self,
        parent,
        cpu_name: str = "openmips",
        cpu_arch: str = "mips",
        cpu_hdl_path: Optional[str] = None,
        board_name: str = "nexys_a7_100",
        project_dir: Optional[str] = None,
        on_bitstream_ready: Optional[Callable[[str], None]] = None,
    ):
        self.cpu_name = cpu_name
        self.cpu_arch = cpu_arch
        self.cpu_hdl_path = cpu_hdl_path
        self.board_name = board_name
        self.project_dir = project_dir or os.getcwd()
        self.on_bitstream_ready = on_bitstream_ready
        self.is_running = False

        super().__init__(
            parent,
            "สังเคราะห์ Bitstream บน GitHub Actions",
            820,
            620,
        )

        self._build_ui()

    DISPATCH_IDLE = "เริ่มสังเคราะห์บน GitHub Actions"
    DISPATCH_BUSY = "กำลังสังเคราะห์บน Cloud..."

    def _build_ui(self):
        body = tk.Frame(self.container, bg=BG_BLACK)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        form = tk.Frame(body, bg=BG_BLACK)
        form.pack(fill=tk.X)
        form.columnconfigure(1, weight=1)

        def label(row, text):
            tk.Label(form, text=text, bg=BG_BLACK, fg=TXT_MUTED, font=(FONT_UI, 9),
                     anchor="w").grid(row=row, column=0, sticky="w", padx=(0, 16), pady=5)

        def entry(row, var, **kw):
            e = tk.Entry(form, textvariable=var, bg=BG_EDITOR, fg=TXT_BRIGHT, insertbackground=TXT_BRIGHT,
                         bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR,
                         highlightcolor=BORDER_HOVER, font=(FONT_CODE, 9), **kw)
            e.grid(row=row, column=1, sticky="ew", pady=5, ipady=4)
            return e

        label(0, "เป้าหมาย")
        tk.Label(form, text=f"{self.cpu_name} ({self.cpu_arch.upper()}) บน {self.board_name}",
                 bg=BG_BLACK, fg=TXT_BRIGHT, font=(FONT_UI, 9), anchor="w").grid(
                     row=0, column=1, columnspan=2, sticky="w", pady=5)

        label(1, "GitHub repo")
        self.repo_var = tk.StringVar(value="posweeza558/fpga-studio-cloud")
        entry(1, self.repo_var)

        label(2, "GitHub token")
        # Auto-detect a token embedded in the local git remote URL
        detected_token = ""
        try:
            import subprocess, re
            r_out = subprocess.check_output(["git", "config", "remote.origin.url"], text=True,
                                            stderr=subprocess.DEVNULL).strip()
            m = re.search(r"(ghp_[A-Za-z0-9]+)", r_out)
            if m:
                detected_token = m.group(1)
        except Exception:
            pass
        self.token_var = tk.StringVar(value=detected_token)
        entry(2, self.token_var, show="*")
        kit.button(form, "ตรวจสอบ repo", self._test_repo_connection).grid(row=2, column=2, sticky="e", padx=(8, 0))

        tk.Label(body, text="GitHub Actions จะรัน openXC7 (Yosys, nextpnr) ใน container แล้วส่งไฟล์ .bit กลับมา",
                 bg=BG_BLACK, fg=TXT_MUTED, font=(FONT_UI, 9), anchor="w").pack(fill=tk.X, pady=(8, 0))

        footer = tk.Frame(body, bg=BG_BLACK)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(14, 0))
        self.btn_dispatch = kit.button(footer, self.DISPATCH_IDLE, self._start_cloud_synthesis_thread, kind="primary")
        self.btn_dispatch.pack(side=tk.LEFT)
        kit.button(footer, "ส่งออก .zip เพื่อ push เอง", self._export_bundle_zip, pady=7).pack(side=tk.LEFT, padx=(8, 0))
        kit.button(footer, "ปิด", self.destroy, kind="link").pack(side=tk.RIGHT)

        kit.section_label(body, "บันทึก").pack(fill=tk.X, pady=(16, 6))
        con_frame = tk.Frame(body, bg=BG_EDITOR, highlightthickness=1, highlightbackground=BORDER_COLOR)
        con_frame.pack(fill=tk.BOTH, expand=True)
        self.txt_log = tk.Text(con_frame, bg=BG_EDITOR, fg=TXT_PRIMARY, font=(FONT_CODE, 9), wrap="char",
                               bd=0, padx=10, pady=8, insertbackground=TXT_BRIGHT)
        sb = SpotifyAutoScrollbar(con_frame, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._log("ใส่ GitHub repo และ token แล้วกด 'เริ่มสังเคราะห์บน GitHub Actions'")

    def _log(self, text: str):
        def _append():
            self.txt_log.insert(tk.END, text + "\n")
            self.txt_log.see(tk.END)

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self.after(0, _append)

    def _test_repo_connection(self):
        repo = self.repo_var.get().strip()
        token = self.token_var.get().strip() or None
        if not repo or "/" not in repo:
            messagebox.showwarning("รูปแบบคลังไม่ถูกต้อง", "กรุณาระบุคลังในรูปแบบ 'owner/repository'", parent=self)
            return

        self._log(f"\nกำลังตรวจสอบการเชื่อมต่อไปยังคลัง: {repo}...")
        ok, msg = check_github_repo_workflow(repo, token)
        if ok:
            self._log(f"✓ {msg}")
            messagebox.showinfo("เชื่อมต่อสำเร็จ", msg, parent=self)
        else:
            self._log(f"✗ {msg}")
            messagebox.showerror("เชื่อมต่อไม่สำเร็จ", msg, parent=self)

    def _export_bundle_zip(self):
        ok, msg, z_path = export_cloud_bundle_zip(
            project_dir=self.project_dir,
            cpu_name=self.cpu_name,
            cpu_arch=self.cpu_arch,
            cpu_hdl_path=self.cpu_hdl_path,
            on_log=self._log,
        )
        if ok and z_path:
            messagebox.showinfo(
                "สร้างแพ็กเกจสำเร็จ",
                f"สร้างแพ็กเกจ Cloud ZIP เรียบร้อยแล้วที่:\n\n{z_path}\n\nคุณสามารถนำไฟล์นี้ไปแตกและ Push ขึ้น GitHub เพื่อรัน Cloud Actions ได้ทันที!",
                parent=self,
            )

    def _start_cloud_synthesis_thread(self):
        if self.is_running:
            return

        repo = self.repo_var.get().strip()
        token = self.token_var.get().strip()
        if not repo or "/" not in repo:
            messagebox.showwarning("กรุณาระบุคลัง", "กรุณาระบุชื่อ GitHub Repo ให้ถูกต้อง เช่น 'username/project'", parent=self)
            return
        if not token:
            messagebox.showwarning("ต้องใช้ GitHub Token", "การสั่งรัน GitHub Actions ผ่านโปรแกรมจำเป็นต้องใช้ Personal Access Token (PAT)\n\nหรือหากไม่มี Token สามารถใช้ปุ่ม 'รวมไฟล์แพ็กเกจ .ZIP เพื่อ Push เอง' ได้ครับ", parent=self)
            return

        self.is_running = True
        kit.set_primary_busy(self.btn_dispatch, True, self.DISPATCH_IDLE, self.DISPATCH_BUSY)

        def worker():
            self._log("\n" + "=" * 60)
            self._log(f"[1/2] เตรียมแพ็กเกจ SoC Auto-Wrapper สำหรับ '{self.cpu_name}'...")
            try:
                from core.cloud_synthesis import prepare_cloud_synthesis_package
                prepare_cloud_synthesis_package(self.project_dir, self.cpu_name, arch=self.cpu_arch, cpu_hdl_path=self.cpu_hdl_path)
                self._log("✓ สร้างโค้ด SoC Top และ Constraints เรียบร้อย")
            except Exception as e:
                self._log(f"เตรียมแพ็กเกจล้มเหลว: {e}")

            self._log(f"[2/2] เริ่มส่งคำสั่ง Cloud Synthesis ไปยัง GitHub Actions ({repo})...")

            ok, msg = trigger_cloud_synthesis_workflow(
                repo_slug=repo,
                github_token=token,
                cpu_name=self.cpu_name,
                board_target=self.board_name,
            )
            if not ok:
                self._log(f"✗ {msg}")
                self.after(0, lambda: self._on_finish(False, msg))
                return

            self._log(f"✓ {msg}")
            self._log("กำลังรอเวิร์กโฟลว์เริ่มทำงานบน GitHub Runners (ตรวจสอบทุก 6 วินาที)...")

            # Polling loop
            start_time = time.time()
            active_run_id = None
            max_wait_seconds = 1800  # 30 mins

            while time.time() - start_time < max_wait_seconds:
                time.sleep(6)
                s_ok, run_data, r_msg = get_latest_workflow_run(repo, token)
                if not s_ok or not run_data:
                    continue

                active_run_id = run_data.get("id")
                status = run_data.get("status")
                conclusion = run_data.get("conclusion")
                html_url = run_data.get("html_url", "")

                self._log(f"   [Cloud Status] Run #{active_run_id}: {status} (ข้อสรุป: {conclusion or 'กำลังรัน...'})")

                if status == "completed":
                    if conclusion == "success":
                        self._log("เวิร์กโฟลว์บน GitHub Actions สังเคราะห์ Bitstream สำเร็จ")
                        # Download artifact
                        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        dest_bit = os.path.join(app_root, "bitstreams", f"nexys_a7_{self.cpu_name}.bit")

                        a_ok, artifacts, a_msg = get_run_artifacts(repo, active_run_id, token)
                        if a_ok and artifacts:
                            down_url = artifacts[0].get("archive_download_url")
                            d_ok, d_msg = download_synthesized_bitstream_from_url(down_url, dest_bit, token, on_log=self._log)
                            if d_ok:
                                self.after(0, lambda: self._on_bitstream_downloaded(dest_bit))
                                return
                            else:
                                self.after(0, lambda m=d_msg: self._on_finish(False, m))
                                return
                        self.after(0, lambda: self._on_finish(False, f"สังเคราะห์เสร็จแต่ไม่พบ Artifacts สำหรับดาวน์โหลด ({html_url})"))
                        return
                    else:
                        err_str = f"การสังเคราะห์บน Cloud ล้มเหลว (ผลลัพธ์: {conclusion})\nดูรายละเอียดได้ที่: {html_url}"
                        self._log(f"✗ {err_str}")
                        self.after(0, lambda: self._on_finish(False, err_str))
                        return

            self.after(0, lambda: self._on_finish(False, "หมดเวลารอคอยผลลัพธ์จาก Cloud (Timeout)"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_bitstream_downloaded(self, bit_path: str):
        self.is_running = False
        kit.set_primary_busy(self.btn_dispatch, False, self.DISPATCH_IDLE, self.DISPATCH_BUSY)
        self._log(f"\n✓ ได้รับไฟล์ Bitstream สำเร็จรูป: {bit_path}")
        if self.on_bitstream_ready:
            self.on_bitstream_ready(bit_path)
        messagebox.showinfo(
            "Cloud Synthesis สำเร็จ!",
            f"ดาวน์โหลดไฟล์ Bitstream เรียบร้อยแล้ว!\n\nไฟล์: {os.path.basename(bit_path)}\n\nพร้อมสำหรับการแฟลชลงบอร์ด FPGA ผ่านสาย USB ทันที!",
            parent=self,
        )
        self.destroy()

    def _on_finish(self, ok: bool, msg: str):
        self.is_running = False
        kit.set_primary_busy(self.btn_dispatch, False, self.DISPATCH_IDLE, self.DISPATCH_BUSY)
        self._log(f"\n[{'เสร็จสมบูรณ์' if ok else 'แจ้งเตือน'}] {msg}")
        if not ok:
            messagebox.showerror("สถานะ Cloud Synthesis", msg, parent=self)
