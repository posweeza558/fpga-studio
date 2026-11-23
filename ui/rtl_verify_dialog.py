# -*- coding: utf-8 -*-
"""
FPGA Studio — 5-Stage Pipeline Hazard Analyzer & RTL Testbench Co-Simulation Dialog
Frameless Spotify Dark modal window providing:
  - Cycle-accurate CPI, RAW Load-Use Stall, Forwarding (EX->EX, MEM->EX), and Branch Flush/Delay metrics
  - Cycle-by-cycle 5-Stage Pipeline Waterfall (IF / ID / EX / MEM / WB)
  - Differential RTL Verification status & 1-click export of Verilog Testbench + VCD Waveform scripts
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config.theme import (
    BG_BLACK,
    BG_ACTIVITY,
    BG_EDITOR,
    BG_ELEVATED,
    BG_PILL_INACT,
    BG_PILL_ACT,
    BORDER_COLOR,
    ACCENT_GREEN,
    ACCENT_AMBER,
    BG_HOVER,
    ACCENT_RED,
    TXT_BRIGHT,
    TXT_PRIMARY,
    TXT_MUTED,
    TXT_ON_WHITE,
    TXT_ON_PILL,
    ACCENT_HOVER,
    FONT_UI,
    FONT_CODE,
    FONT_ICON,
)
from core.rtl_cosim import (
    run_rtl_cosim,
    export_rtl_testbench,
    generate_gtkwave_savefile,
    find_gtkwave_bin,
    detect_verilog_simulator,
)
from ui.installer_wizard import BaseFramelessWizardDialog
from ui import dialog_kit as kit
from ui.widgets import attach_tooltip
from ui.widgets import SpotifyPillButton, SpotifyAutoScrollbar


class RTLVerifyDialog(BaseFramelessWizardDialog):
    """5-Stage Pipeline Hazard Analyzer & RTL Testbench Co-Simulation Dialog."""

    def __init__(self, parent, instructions, arch="mips", cpu_name="OpenMIPS 32-bit",
                 cpu_hdl_path=None, sw_init=0, btn_init=0, mmio_map=None, project_dir=None,
                 on_exported=None):
        self.instructions = instructions or []
        self.arch = arch
        self.cpu_name = cpu_name
        self.cpu_hdl_path = cpu_hdl_path
        self.sw_init = sw_init
        self.btn_init = btn_init
        self.mmio_map = mmio_map or {}
        self.project_dir = project_dir or os.getcwd()
        self.on_exported = on_exported
        self.active_tab = "hazards"
        self.cosim_res = None

        super().__init__(
            parent,
            "วิเคราะห์ Pipeline และทดสอบ RTL",
            940,
            680,
        )
        self._run_analysis()
        self._build_ui()

    def _run_analysis(self):
        self.cosim_res = run_rtl_cosim(
            self.instructions,
            arch=self.arch,
            cpu_hdl_path=self.cpu_hdl_path,
            sim_cycles=500,
            sw_init=self.sw_init,
            btn_init=self.btn_init,
            mmio_map=self.mmio_map,
        )

    def _build_ui(self):
        for w in self.container.winfo_children():
            w.destroy()

        pipe = self.cosim_res["pipeline"]
        pad = 20

        # ---- header: what was analysed
        header = tk.Frame(self.container, bg=BG_BLACK, padx=pad, pady=14)
        header.pack(fill="x")
        tk.Label(header, text=self.cpu_name, font=(FONT_UI, 12, "bold"),
                 bg=BG_BLACK, fg=TXT_BRIGHT, anchor="w").pack(fill="x")
        from core.hdl_analyzer import inspect_cpu_hardware_ports
        caps = inspect_cpu_hardware_ports(self.cpu_hdl_path) if self.cpu_hdl_path else {}
        rtl_topo = caps.get("rtl_topology") or "5-Stage Pipelined RTL"
        tk.Label(
            header,
            text=(f"{self.arch.upper()} · {rtl_topo} · โปรแกรม {len(self.instructions)} คำสั่ง · "
                  f"SW=0x{self.sw_init:04X}  BTN=0x{self.btn_init:02X}"),
            font=(FONT_UI, 9), bg=BG_BLACK, fg=TXT_MUTED, anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # ---- one dense stats line instead of six identical metric cards
        stats = tk.Frame(self.container, bg=BG_BLACK, padx=pad)
        stats.pack(fill="x", pady=(0, 4))
        total_fwds = pipe["ex_forwards"] + pipe["mem_forwards"]
        ctrl_val = pipe["delay_slots"] if self.arch == "mips" else pipe["branch_flushes"]
        ctrl_lbl = "delay slot" if self.arch == "mips" else "branch flush"
        div_stalls = pipe.get("div_stalls", 0)
        items = [
            (f"{pipe['retired_instructions']}", "คำสั่ง", TXT_BRIGHT),
            (f"{pipe['total_cycles']}", "รอบ", TXT_BRIGHT),
            (f"{pipe['cpi']:.2f}", "CPI", ACCENT_AMBER if pipe["cpi"] > 1.35 else TXT_BRIGHT),
            (f"{pipe['load_use_stalls']}", "load-use stall", ACCENT_AMBER if pipe["load_use_stalls"] else TXT_BRIGHT),
            (f"{total_fwds}", "forwarding", TXT_BRIGHT),
            (f"{ctrl_val}", ctrl_lbl, TXT_BRIGHT),
        ]
        if div_stalls:
            items.append((f"{div_stalls}", "divider stall", ACCENT_AMBER))
        items.append((f"{pipe['runtime_25mhz_us']:.1f} µs", "ที่ 25 MHz", TXT_BRIGHT))
        for i, (val, lbl, col) in enumerate(items):
            cell = tk.Frame(stats, bg=BG_BLACK)
            cell.pack(side="left", padx=(0 if i == 0 else 18, 0))
            tk.Label(cell, text=val, font=(FONT_UI, 10, "bold"), bg=BG_BLACK, fg=col).pack(side="left")
            tk.Label(cell, text=lbl, font=(FONT_UI, 9), bg=BG_BLACK, fg=TXT_MUTED).pack(side="left", padx=(5, 0))
            if lbl == "forwarding":
                attach_tooltip(cell, f"EX→EX {pipe['ex_forwards']} ครั้ง, MEM→EX {pipe['mem_forwards']} ครั้ง")

        # ---- MMIO output values (data, so monospace), plus the RTL co-sim verdict if it ran
        rgb_vals = pipe.get("rgb_value", [0, 0])
        rgb_hex = ((rgb_vals[0] & 0xFFF) << 12) | (rgb_vals[1] & 0xFFF) if len(rgb_vals) >= 2 else 0
        out_row = tk.Frame(self.container, bg=BG_BLACK, padx=pad)
        out_row.pack(fill="x", pady=(6, 0))
        tk.Label(out_row, text="เอาต์พุต", font=(FONT_UI, 9), bg=BG_BLACK, fg=TXT_MUTED).pack(side="left")
        tk.Label(
            out_row,
            text=(f"LED 0x{pipe['led_value'] & 0xFFFF:04X}    "
                  f"7-SEG 0x{pipe['seg7_value'] & 0xFFFFFFFF:08X}    RGB 0x{rgb_hex:06X}"),
            font=(FONT_CODE, 9), bg=BG_BLACK, fg=TXT_PRIMARY,
        ).pack(side="left", padx=(12, 0))
        if self.cosim_res.get("ran_rtl"):
            msg_col = ACCENT_GREEN if self.cosim_res.get("passed") else ACCENT_AMBER
            tk.Label(self.container, text=self.cosim_res.get("message", ""), font=(FONT_UI, 9),
                     bg=BG_BLACK, fg=msg_col, anchor="w", padx=pad).pack(fill="x", pady=(4, 0))

        # ---- underlined panel tabs
        tab_strip = tk.Frame(self.container, bg=BG_BLACK, padx=pad)
        tab_strip.pack(fill="x", pady=(14, 0))
        self._tabs = {}
        for key, text in (("hazards", f"Hazards และ Forwarding  {len(pipe['hazard_events'])}"),
                          ("timeline", f"ไทม์ไลน์ Pipeline  {len(pipe['timeline'])} รอบ")):
            cell = tk.Frame(tab_strip, bg=BG_BLACK, cursor="hand2")
            cell.pack(side="left", padx=(0, 22))
            lbl = tk.Label(cell, text=text, font=(FONT_UI, 9, "bold"), bg=BG_BLACK, cursor="hand2")
            lbl.pack(pady=(0, 6))
            bar = tk.Frame(cell, height=2)
            bar.pack(fill="x")
            for w in (cell, lbl):
                w.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self._tabs[key] = (lbl, bar)
        tk.Frame(self.container, bg=BORDER_COLOR, height=1).pack(fill="x", padx=pad)
        self._paint_tabs()

        # ---- footer actions (packed before the table so they are never pushed off)
        footer = tk.Frame(self.container, bg=BG_BLACK, padx=pad, pady=14)
        footer.pack(fill="x", side="bottom")
        kit.button(footer, "ส่งออก RTL Testbench...", self._on_export_testbench).pack(side="left")
        kit.button(footer, "เปิดใน GTKWave", self._on_open_gtkwave).pack(side="left", padx=(8, 0))
        kit.button(footer, "วิเคราะห์ใหม่", self._rerun_and_refresh).pack(side="right")

        # ---- table
        self.body_frame = tk.Frame(self.container, bg=BG_EDITOR, highlightthickness=1,
                                   highlightbackground=BORDER_COLOR)
        self.body_frame.pack(fill="both", expand=True, padx=pad, pady=(10, 0))
        self._populate_active_table()

    def _paint_tabs(self):
        for key, (lbl, bar) in self._tabs.items():
            on = key == self.active_tab
            lbl.config(fg=TXT_BRIGHT if on else TXT_MUTED)
            bar.config(bg=ACCENT_GREEN if on else BG_BLACK)

    def _switch_tab(self, tab_name):
        self.active_tab = tab_name
        self._paint_tabs()
        self._populate_active_table()

    def _populate_active_table(self):
        for w in self.body_frame.winfo_children():
            w.destroy()

        style = ttk.Style(self)
        # proportional font: the description column is Thai prose, not code
        style.configure("Data.Treeview", background=BG_EDITOR, fieldbackground=BG_EDITOR,
                        foreground=TXT_PRIMARY, rowheight=28, font=(FONT_UI, 9), borderwidth=0)
        style.map("Data.Treeview", background=[("selected", BG_HOVER)], foreground=[("selected", TXT_BRIGHT)])

        pipe = self.cosim_res["pipeline"]
        scroll = SpotifyAutoScrollbar(self.body_frame, bg_track=BG_EDITOR)

        if self.active_tab == "hazards":
            cols = ("cycle", "pc", "asm", "type", "detail")
            tree = ttk.Treeview(self.body_frame, columns=cols, show="headings", style="Data.Treeview",
                                yscrollcommand=scroll.set)
            scroll.command = tree.yview
            for c, t in zip(cols, ("รอบ", "PC", "Assembly", "เหตุการณ์", "รายละเอียด")):
                tree.heading(c, text=t, anchor="w")
            tree.column("cycle", width=56, anchor="w", stretch=False)
            tree.column("pc", width=72, anchor="w", stretch=False)
            tree.column("asm", width=170, anchor="w", stretch=False)
            tree.column("type", width=240, anchor="w", stretch=False)
            tree.column("detail", width=320, anchor="w", stretch=True)

            # colour only the rows that cost cycles; forwarding is the normal case
            tree.tag_configure("stall", foreground=ACCENT_AMBER)
            tree.tag_configure("flush", foreground=ACCENT_RED)
            tree.tag_configure("fwd", foreground=TXT_PRIMARY)
            tree.tag_configure("empty", foreground=TXT_MUTED)

            events = pipe["hazard_events"]
            if not events:
                tree.insert("", tk.END, values=("", "", "", "ไม่พบ hazard",
                                                "ไม่มี stall หรือ data hazard ในช่วงคำสั่งที่รัน"), tags=("empty",))
            else:
                for ev in events:
                    tp = ev["type"]
                    tag = "stall" if "Load-Use" in tp else ("flush" if "Flush" in tp else "fwd")
                    tree.insert("", tk.END, values=(ev["cycle"], ev["pc"], ev["asm"], tp, ev["detail"]), tags=(tag,))
        else:
            cols = ("cycle", "if", "id", "ex", "mem", "wb", "note")
            tree = ttk.Treeview(self.body_frame, columns=cols, show="headings", style="Data.Treeview",
                                yscrollcommand=scroll.set)
            scroll.command = tree.yview
            for c, t in zip(cols, ("รอบ", "IF", "ID", "EX", "MEM", "WB", "สัญญาณ")):
                tree.heading(c, text=t, anchor="w")
            tree.column("cycle", width=50, anchor="w", stretch=False)
            for c in ("if", "id", "ex", "mem", "wb"):
                tree.column(c, width=128, anchor="w", stretch=False)
            tree.column("note", width=170, anchor="w", stretch=True)

            tree.tag_configure("stall", foreground=ACCENT_AMBER)
            tree.tag_configure("flush", foreground=ACCENT_RED)
            tree.tag_configure("row", foreground=TXT_PRIMARY)
            for row in pipe["timeline"]:
                note = row["note"]
                tag = "stall" if "STALL" in note else ("flush" if "FLUSH" in note else "row")
                tree.insert("", tk.END,
                            values=(row["cycle"], row["IF"], row["ID"], row["EX"], row["MEM"], row["WB"], note),
                            tags=(tag,))
        scroll.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

    def _rerun_and_refresh(self):
        self._run_analysis()
        self._build_ui()

    def _on_export_testbench(self):
        chosen = filedialog.askdirectory(
            parent=self,
            initialdir=self.project_dir,
            title="เลือกโฟลเดอร์สำหรับส่งออกชุด RTL Testbench (.v + .hex + VCD Waveform)",
        )
        if not chosen:
            return
        if os.path.abspath(chosen).lower() == os.path.abspath(self.project_dir).lower():
            out_dir = os.path.join(chosen, f"rtl_testbench_{self.arch}")
        else:
            out_dir = chosen

        pkg = export_rtl_testbench(
            out_dir,
            self.instructions,
            arch=self.arch,
            cpu_hdl_path=self.cpu_hdl_path,
            sim_cycles=max(1, self.cosim_res["pipeline"]["retired_instructions"]),
            sw_init=self.sw_init,
            btn_init=self.btn_init,
            mmio_map=self.mmio_map,
        )
        if self.on_exported:
            self.on_exported(pkg)
        messagebox.showinfo(
            "ส่งออกชุด RTL Testbench สำเร็จ",
            f"ส่งออกไฟล์ Testbench และโปรแกรมเสร็จสมบูรณ์ที่:\n{pkg['out_dir']}\n\n"
            f"• tb_cpu_cosim.v (พร้อม $dumpfile waveform.vcd)\n"
            f"• program.hex & dmem_init.hex\n"
            f"• rtl_cpu/ ({len(pkg['copied_rtl'])} ไฟล์ RTL)\n"
            f"• run_iverilog_gtkwave.bat & run_vivado_xsim.tcl",
            parent=self,
        )

    def _on_open_gtkwave(self):
        gtkwave_exe = find_gtkwave_bin()
        if not gtkwave_exe:
            messagebox.showwarning("ไม่พบ GTKWave", "ไม่พบโปรแกรม GTKWave ในโฟลเดอร์ toolchain/gtkwave", parent=self)
            return

        out_dir = os.path.join(self.project_dir, f"rtl_testbench_{self.arch}")
        vcd_path = os.path.join(out_dir, "waveform.vcd")

        pkg = export_rtl_testbench(
            out_dir,
            self.instructions,
            arch=self.arch,
            cpu_hdl_path=self.cpu_hdl_path,
            sim_cycles=max(1, self.cosim_res["pipeline"]["retired_instructions"]),
            sw_init=self.sw_init,
            btn_init=self.btn_init,
            mmio_map=self.mmio_map,
        )
        sim_tool = detect_verilog_simulator()
        if sim_tool and sim_tool.get("kind") == "iverilog":
            rtl_files = [
                os.path.join(out_dir, "rtl_cpu", fn)
                for fn in pkg["copied_rtl"]
                if fn.lower().endswith((".v", ".sv"))
            ]
            vvp_out = os.path.join(out_dir, "sim_cosim.vvp")
            subprocess.run(
                [sim_tool["iverilog"], "-g2012", "-I", os.path.join(out_dir, "rtl_cpu"), "-o", vvp_out, pkg["tb_v"]] + rtl_files,
                cwd=out_dir,
                capture_output=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )
            subprocess.run(
                [sim_tool["vvp"], vvp_out],
                cwd=out_dir,
                capture_output=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )

        gtkw_path = generate_gtkwave_savefile(out_dir, arch=self.arch, vcd_path=vcd_path)
        if os.path.exists(vcd_path):
            subprocess.Popen([gtkwave_exe, vcd_path, gtkw_path], cwd=out_dir)
        else:
            subprocess.Popen([gtkwave_exe], cwd=os.path.dirname(gtkwave_exe))
