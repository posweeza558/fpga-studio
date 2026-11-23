# -*- coding: utf-8 -*-
"""
FPGA Studio — Hardware Pin & Address Configuration Dialog (Pin & MMIO Planner):
Frameless Spotify/NVIDIA Dark Modal Dialog styled identically to the Import Wizard.
Allows users to visually inspect and customize:
  1. Hardware HDL port pin bindings (Clock, Reset, Address Bus, Data In/Out, WE).
  2. MMIO Base Addresses for peripherals (LEDs, Switches, 7-Segment, UART, VGA Framebuffer).
Saves configuration to cpu_manifest.json and updates the Nexys A7 simulator in real time.
"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox

from config.theme import (
    BG_BLACK,
    BG_TITLEBAR,
    BG_ACTIVITY,
    BG_SIDEBAR,
    BG_EDITOR,
    BG_POPUP,
    BG_ELEVATED,
    BORDER_COLOR,
    ACCENT_GREEN,
    ACCENT_AMBER,
    ACCENT_RED,
    TXT_BRIGHT,
    TXT_PRIMARY,
    TXT_MUTED,
    FONT_UI,
    FONT_CODE,
    FONT_ICON,
)
from core.hdl_analyzer import extract_cpu_ports, inspect_cpu_hardware_ports, invalidate_hdl_cache
from ui.installer_wizard import BaseFramelessWizardDialog
from ui import dialog_kit as kit
from ui.widgets import SpotifyPillButton


class PinAssignmentDialog(BaseFramelessWizardDialog):
    """
    Hardware Pin & MMIO Address Configuration Dialog.
    Styled identically to the Setup & Import Wizard (Frameless, DWM rounded, Spotify/NVIDIA dark theme).
    """

    def __init__(self, parent, target_file_path=None, cpu_info=None, on_save=None):
        self.cpu_info = cpu_info or {}
        if target_file_path:
            self.target_file_path = os.path.abspath(target_file_path)
        else:
            self.target_file_path = self.cpu_info.get("path", "")

        self.on_save = on_save
        self.pkg_dir = os.path.dirname(self.target_file_path) if self.target_file_path else os.getcwd()
        self.cpu_name = self.cpu_info.get("name") or (os.path.splitext(os.path.basename(self.target_file_path))[0] if self.target_file_path else "Standard CPU")

        # 1. Extract physical ports from HDL file (if file exists)
        if self.target_file_path and os.path.exists(self.target_file_path):
            self.port_data = extract_cpu_ports(self.target_file_path)
            self.all_ports = self.port_data.get("ports", [])
            self.detailed = self.port_data.get("detailed_ports", [])
            self.roles = self.port_data.get("detected_roles", {})
        else:
            self.port_data = {"ports": [], "detailed_ports": [], "detected_roles": {}}
            self.all_ports = ["clk", "rst", "ram_addr_o", "ram_data_o", "ram_data_i", "ram_we_o"]
            self.detailed = []
            self.roles = {
                "clock": "clk", "reset": "rst",
                "mem_addr": "ram_addr_o", "mem_wdata": "ram_data_o",
                "mem_rdata": "ram_data_i", "mem_we": "ram_we_o"
            }

        # 2. Load existing manifest mapping if present
        self.manifest_path = os.path.join(self.pkg_dir, "cpu_manifest.json")
        self.existing_manifest_raw = {}
        self.existing_mapping = {}
        self.existing_mmio = {}
        self.existing_is_alu = False

        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as jf:
                    mdata = json.load(jf)
                    self.existing_manifest_raw = dict(mdata)
                    self.existing_mapping = mdata.get("port_mapping", {})
                    self.existing_mmio = mdata.get("mmio_mapping", {})
                    self.existing_is_alu = mdata.get("is_standalone_alu", False)
            except Exception:
                pass

        # 3. Form Variables — Pin Mapping
        self.clk_var = tk.StringVar(value=self.existing_mapping.get("clk") or self.roles.get("clock") or "")
        self.rst_var = tk.StringVar(value=self.existing_mapping.get("rst") or self.roles.get("reset") or "")
        self.addr_var = tk.StringVar(value=self.existing_mapping.get("mem_addr") or self.roles.get("mem_addr") or "")
        self.wdata_var = tk.StringVar(value=self.existing_mapping.get("mem_wdata") or self.roles.get("mem_wdata") or "")
        self.rdata_var = tk.StringVar(value=self.existing_mapping.get("mem_rdata") or self.roles.get("mem_rdata") or "")
        self.we_var = tk.StringVar(value=self.existing_mapping.get("mem_we") or self.roles.get("mem_we") or "")

        # Has Memory Bus capability
        has_bus_detect = bool(self.addr_var.get() or self.roles.get("mem_addr"))

        # Default GPIO & UART (Clear, compact labels that fit neatly in dropdowns)
        default_gpio = self.existing_mapping.get("led")
        if not default_gpio or "Memory Bus" in default_gpio or default_gpio.startswith("("):
            default_gpio = "MMIO 0xF0000000 (Nexys A7 Bus)" if has_bus_detect else "(ไม่ระบุ / Unmapped)"
        self.gpio_var = tk.StringVar(value=default_gpio)

        default_uart = self.existing_mapping.get("uart_tx")
        if not default_uart or "Memory Bus" in default_uart or default_uart.startswith("("):
            default_uart = "MMIO 0xF0000010 (Nexys A7 Bus)" if has_bus_detect else "(ไม่ระบุ / Unmapped)"
        self.uart_var = tk.StringVar(value=default_uart)

        # Standalone ALU flag
        init_alu = self.existing_is_alu or ("alu_only" in self.cpu_name.lower()) or (not has_bus_detect and len(self.all_ports) > 0)
        self.is_alu_var = tk.BooleanVar(value=init_alu)

        # 4. Form Variables — Unified MMIO Addresses (supports both individual and legacy keys)
        self.mmio_led_var = tk.StringVar(value=self.existing_mmio.get("led") or self.existing_mmio.get("led_seg") or "0xF0000000")
        self.mmio_sw_var = tk.StringVar(value=self.existing_mmio.get("sw") or "0xF0000004")
        self.mmio_seg7_var = tk.StringVar(value=self.existing_mmio.get("seg7") or "0xF0000008")
        self.mmio_btn_var = tk.StringVar(value=self.existing_mmio.get("btn") or self.existing_mmio.get("btn_rgb") or "0xF000000C")
        self.mmio_uart_var = tk.StringVar(value=self.existing_mmio.get("uart_tx") or "0xF0000010")
        self.mmio_rgb_var = tk.StringVar(value=self.existing_mmio.get("rgb") or "0xF0000018")
        self.mmio_vga_var = tk.StringVar(value=self.existing_mmio.get("vga") or "0xFF000000")

        # Active tab state: 'pins' | 'addresses'
        self.active_tab = "pins"

        super().__init__(parent, "กำหนดขาพอร์ตและแอดเดรส", 820, 740)
        self._build_ui()

    def _build_ui(self):
        for w in self.container.winfo_children():
            w.destroy()
        pad = 20

        # ---- which module is being configured
        info = tk.Frame(self.container, bg=BG_BLACK, padx=pad, pady=14)
        info.pack(fill="x")
        fname = os.path.basename(self.target_file_path) if self.target_file_path else "Built-in Core"
        top = tk.Frame(info, bg=BG_BLACK)
        top.pack(fill="x")
        tk.Label(top, text=f"{self.cpu_name.upper()}  ({fname})", font=(FONT_UI, 12, "bold"),
                 bg=BG_BLACK, fg=TXT_BRIGHT).pack(side="left")
        if self.is_alu_var.get():
            badge_txt, badge_fg = "ALU เดี่ยว ไม่ต่อ bus", ACCENT_AMBER
        elif len(self.all_ports) == 0:
            badge_txt, badge_fg = "testbench แบบปิด", TXT_MUTED
        else:
            badge_txt, badge_fg = "ต่อ bus ผ่าน MMIO", ACCENT_GREEN
        tk.Label(top, text=badge_txt, font=(FONT_UI, 9), bg=BG_BLACK, fg=badge_fg).pack(side="right")

        if self.detailed:
            sample_p = [f"{p['name']}({'in' if p['dir']=='input' else 'out'}:{p['width']})" for p in self.detailed[:8]]
            ports_desc = f"{len(self.all_ports)} พอร์ต: {', '.join(sample_p)}{'...' if len(self.detailed) > 8 else ''}"
        elif self.all_ports:
            ports_desc = f"{len(self.all_ports)} พอร์ต: {', '.join(self.all_ports[:10])}{'...' if len(self.all_ports) > 10 else ''}"
        else:
            ports_desc = "ไม่มีพอร์ตภายนอก (วงจรจำลองแบบปิด)"
        tk.Label(info, text=ports_desc, font=(FONT_CODE, 8), bg=BG_BLACK, fg=TXT_MUTED,
                 wraplength=760, justify="left").pack(anchor="w", pady=(4, 0))

        # ---- underlined tabs
        tab_bar = tk.Frame(self.container, bg=BG_BLACK, padx=pad)
        tab_bar.pack(fill="x")
        for key, text in (("pins", "การจับคู่ขาพอร์ต"), ("addresses", "แอดเดรส MMIO")):
            on = key == self.active_tab
            cell = tk.Frame(tab_bar, bg=BG_BLACK, cursor="hand2")
            cell.pack(side="left", padx=(0, 22))
            lbl = tk.Label(cell, text=text, font=(FONT_UI, 9, "bold"), bg=BG_BLACK,
                           fg=TXT_BRIGHT if on else TXT_MUTED, cursor="hand2")
            lbl.pack(pady=(0, 6))
            tk.Frame(cell, height=2, bg=ACCENT_GREEN if on else BG_BLACK).pack(fill="x")
            for w in (cell, lbl):
                w.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
        tk.Frame(self.container, bg=BORDER_COLOR, height=1).pack(fill="x", padx=pad)

        # ---- footer (packed first so it is never pushed off)
        bbar = tk.Frame(self.container, bg=BG_BLACK, padx=pad, pady=14)
        bbar.pack(fill="x", side="bottom")
        kit.button(bbar, "บันทึก", self._save_all, kind="primary").pack(side="left")
        kit.button(bbar, "ยกเลิก", self.destroy, kind="link").pack(side="right")

        self.content_frame = tk.Frame(self.container, bg=BG_BLACK)
        self.content_frame.pack(fill="both", expand=True, padx=pad, pady=(12, 0))
        if self.active_tab == "pins":
            self._render_pins_tab()
        else:
            self._render_mmio_tab()

    def _switch_tab(self, tab):
        self.active_tab = tab
        self._build_ui()

    def _render_pins_tab(self):
        tk.Checkbutton(
            self.content_frame,
            text="ใช้เป็น ALU เดี่ยว (ไม่มี memory bus และไม่ต่อ I/O ของบอร์ด)",
            variable=self.is_alu_var, command=self._on_alu_toggle,
            font=(FONT_UI, 9), bg=BG_BLACK, fg=TXT_PRIMARY, selectcolor=BG_EDITOR,
            activebackground=BG_BLACK, activeforeground=TXT_BRIGHT, bd=0, highlightthickness=0,
        ).pack(anchor="w", pady=(0, 8))

        port_options = ["(ไม่ระบุ / Unmapped)"] + self.all_ports
        gpio_options = ["MMIO 0xF0000000 (Nexys A7 Bus)", "(ไม่ระบุ / Unmapped)"] + self.all_ports
        uart_options = ["MMIO 0xF0000010 (Nexys A7 Bus)", "(ไม่ระบุ / Unmapped)"] + self.all_ports
        rows = [
            ("Address bus", self.addr_var, port_options, "แอดเดรสจาก CPU ไป RAM/MMIO เช่น ram_addr_o"),
            ("Write enable", self.we_var, port_options, "สัญญาณสั่งเขียน เช่น ram_we_o"),
            ("Write data", self.wdata_var, port_options, "ข้อมูลจาก CPU ไป RAM เช่น ram_data_o"),
            ("Read data", self.rdata_var, port_options, "ข้อมูลจาก RAM กลับเข้า CPU เช่น ram_data_i"),
            ("Clock", self.clk_var, port_options, "เช่น clk"),
            ("Reset", self.rst_var, port_options, "active high หรือ low เช่น rst, rst_n"),
            ("GPIO LED/สวิตช์", self.gpio_var, gpio_options, "ปกติต่อผ่าน MMIO เลือกพอร์ตเฉพาะเมื่อ CPU ต่อขาตรง"),
            ("UART TX", self.uart_var, uart_options, "ปกติต่อผ่าน MMIO เลือกพอร์ตเฉพาะเมื่อ CPU ต่อขาตรง"),
        ]
        grid = tk.Frame(self.content_frame, bg=BG_BLACK)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        self.combos = []
        for i, (label_text, var, options, tip) in enumerate(rows):
            lab = tk.Frame(grid, bg=BG_BLACK)
            lab.grid(row=i, column=0, sticky="w", padx=(0, 20), pady=3)
            tk.Label(lab, text=label_text, font=(FONT_UI, 9), bg=BG_BLACK, fg=TXT_PRIMARY, anchor="w").pack(anchor="w")
            tk.Label(lab, text=tip, font=(FONT_UI, 8), bg=BG_BLACK, fg=TXT_MUTED, anchor="w").pack(anchor="w")
            combo = ttk.Combobox(grid, textvariable=var, values=options, state="readonly", font=(FONT_CODE, 9))
            combo.grid(row=i, column=1, sticky="ew", pady=3)
            self.combos.append(combo)
        self._on_alu_toggle()

    def _render_mmio_tab(self):
        tk.Label(self.content_frame,
                 text="CPU ที่มี memory bus จะอ่าน/เขียนอุปกรณ์บนบอร์ดผ่านแอดเดรสเหล่านี้",
                 font=(FONT_UI, 9), bg=BG_BLACK, fg=TXT_MUTED, anchor="w").pack(fill="x", pady=(0, 8))
        mmio_items = [
            ("LED 16 ดวง (LD0-LD15)", self.mmio_led_var, "0xF0000000", "เขียน 16 บิต"),
            ("สวิตช์ 16 ตัว (SW0-SW15)", self.mmio_sw_var, "0xF0000004", "อ่าน 16 บิต"),
            ("7-Segment 8 หลัก", self.mmio_seg7_var, "0xF0000008", "เขียน 32 บิต แสดงเลขฐาน 16"),
            ("ปุ่มกด (BTNC/U/L/R/D)", self.mmio_btn_var, "0xF000000C", "อ่าน 6 บิต รวมปุ่มรีเซ็ต"),
            ("USB-UART", self.mmio_uart_var, "0xF0000010", "115200 8-N-1, status อยู่ที่ base + 4"),
            ("RGB LED 2 ดวง (LD16, LD17)", self.mmio_rgb_var, "0xF0000018", "เขียน 24 บิต: [23:12]=LD16, [11:0]=LD17"),
            ("VGA framebuffer", self.mmio_vga_var, "0xFF000000", "640x480 @ 60Hz"),
        ]
        grid = tk.Frame(self.content_frame, bg=BG_BLACK)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        for i, (title, var, default_hex, desc) in enumerate(mmio_items):
            lab = tk.Frame(grid, bg=BG_BLACK)
            lab.grid(row=i, column=0, sticky="w", pady=4)
            tk.Label(lab, text=title, font=(FONT_UI, 9), bg=BG_BLACK, fg=TXT_PRIMARY, anchor="w").pack(anchor="w")
            tk.Label(lab, text=desc, font=(FONT_UI, 8), bg=BG_BLACK, fg=TXT_MUTED, anchor="w").pack(anchor="w")
            tk.Entry(grid, textvariable=var, font=(FONT_CODE, 9), bg=BG_EDITOR, fg=TXT_BRIGHT,
                     insertbackground=TXT_BRIGHT, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR,
                     width=13).grid(row=i, column=1, padx=(12, 0), ipady=4)
            kit.button(grid, "ค่าเริ่มต้น", (lambda v=var, d=default_hex: v.set(d)), kind="link",
                       size=8).grid(row=i, column=2, padx=(8, 0))

    def _on_alu_toggle(self):
        if not hasattr(self, "combos") or not self.combos:
            return
        is_alu = self.is_alu_var.get()
        if is_alu:
            for c in self.combos[:4]:
                c.config(state="disabled")
        else:
            for c in self.combos[:4]:
                c.config(state="readonly")

    def _save_all(self):
        is_alu = self.is_alu_var.get()

        def clean_val(v):
            val = v.get().strip()
            if "MMIO" in val or "Unmapped" in val or val.startswith("("):
                return ""
            return val

        def clean_hex(v, fallback):
            val = v.get().strip().upper()
            if not val.startswith("0X"):
                val = "0X" + val
            if re.match(r"^0X[0-9A-F]{1,8}$", val):
                return "0x" + val[2:]
            return fallback

        port_mapping = {
            "clk": clean_val(self.clk_var),
            "rst": clean_val(self.rst_var),
            "mem_addr": "" if is_alu else clean_val(self.addr_var),
            "mem_we": "" if is_alu else clean_val(self.we_var),
            "mem_wdata": "" if is_alu else clean_val(self.wdata_var),
            "mem_rdata": "" if is_alu else clean_val(self.rdata_var),
            "led": "" if is_alu else clean_val(self.gpio_var),
            "uart_tx": "" if is_alu else clean_val(self.uart_var),
        }

        led_hex = clean_hex(self.mmio_led_var, "0xF0000000")
        sw_hex = clean_hex(self.mmio_sw_var, "0xF0000004")
        seg7_hex = clean_hex(self.mmio_seg7_var, "0xF0000008")
        btn_hex = clean_hex(self.mmio_btn_var, "0xF000000C")
        uart_hex = clean_hex(self.mmio_uart_var, "0xF0000010")
        uart_stat_int = (int(uart_hex, 16) + 4) & 0xFFFFFFFF
        rgb_hex = clean_hex(self.mmio_rgb_var, "0xF0000018")
        vga_hex = clean_hex(self.mmio_vga_var, "0xFF000000")

        mmio_mapping = {
            "led": led_hex,
            "sw": sw_hex,
            "seg7": seg7_hex,
            "btn": btn_hex,
            "uart_tx": uart_hex,
            "uart_rx": uart_hex,
            "uart_stat": f"0x{uart_stat_int:08X}",
            "rgb": rgb_hex,
            "vga": vga_hex,
        }

        manifest_data = dict(self.existing_manifest_raw)
        manifest_data.update({
            "cpu_name": self.cpu_name,
            "target_file": os.path.basename(self.target_file_path) if self.target_file_path else "",
            "is_standalone_alu": is_alu,
            "port_mapping": port_mapping,
            "mmio_mapping": mmio_mapping,
        })

        # Save to cpu_manifest.json if directory exists
        if self.pkg_dir and os.path.isdir(self.pkg_dir):
            try:
                with open(self.manifest_path, "w", encoding="utf-8") as jf:
                    json.dump(manifest_data, jf, indent=2, ensure_ascii=False)
                invalidate_hdl_cache(self.target_file_path)
            except Exception as e:
                messagebox.showerror("Error", f"ไม่สามารถบันทึก cpu_manifest.json ได้: {e}", parent=self)
                return

        if self.on_save:
            self.on_save(manifest_data)

        messagebox.showinfo("บันทึกสำเร็จ",
                            "บันทึกการกำหนดขาพอร์ตและแอดเดรสฮาร์ดแวร์เรียบร้อยแล้ว!\nระบบได้ปรับปรุงสถานะการเชื่อมต่อกับบอร์ดเสมือน Nexys A7 ทันที",
                            parent=self)
        self.destroy()
