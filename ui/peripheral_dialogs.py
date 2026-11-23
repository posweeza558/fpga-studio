# -*- coding: utf-8 -*-
"""
Interactive Peripheral Simulation Windows for Nexys A7:
1. VGADisplayWindow: Frameless 640x480 @ 60Hz 12-bit RGB VGA Monitor screen.
   Connects directly to FPGA video output (VRAM 0xFF000000) with custom dark titlebar,
   built like the main window (one frame, no nested double borders).
2. UARTTerminalWindow: Frameless USB-UART Serial Terminal (115200 8-N-1) with live RX log,
   TX interactive sending, custom dark titlebar, and unified frameless window style.
"""

import ctypes
import tkinter as tk
from tkinter import ttk
from config.theme import (
    BG_BLACK,
    BG_PANEL,
    BG_ELEVATED,
    BG_HOVER,
    BG_PILL_INACT,
    BG_PILL_ACT,
    BORDER_COLOR,
    BORDER_HOVER,
    ACCENT_GREEN,
    ACCENT_AMBER,
    ACCENT_RED,
    TXT_BRIGHT,
    TXT_PRIMARY,
    TXT_MUTED,
    TXT_DIM,
    TXT_ON_WHITE,
    FONT_UI,
    FONT_CODE,
)
from ui.widgets import SpotifyAutoScrollbar
from ui import dialog_kit as kit


def apply_main_window_style(win):
    """
    Enables frameless mode with Windows 11 DWM native rounded corners and taskbar integration,
    matching the main application window architecture exactly (no nested double borders).
    """
    win.overrideredirect(True)
    win._click_to_raise = True
    try:
        win.update()
        hwnd = win.winfo_id()
        p_hwnd = ctypes.windll.user32.GetParent(hwnd) or hwnd
        for h in (hwnd, p_hwnd):
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            ex_style = ctypes.windll.user32.GetWindowLongW(h, GWL_EXSTYLE)
            ex_style = (ex_style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(h, GWL_EXSTYLE, ex_style)

            # Apply Windows 11 native DWM smooth rounded corners (DWMWCP_ROUND = 2)
            pref = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(h, 33, ctypes.byref(pref), ctypes.sizeof(pref))
    except Exception:
        pass


def center_on_parent(win, parent, w, h):
    """Center child window within parent window bounds."""
    try:
        parent.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = max(px + (pw - w) // 2, 40)
        y = max(py + (ph - h) // 2, 40)
    except Exception:
        x, y = 200, 120
    win.geometry(f"{w}x{h}+{x}+{y}")


def attach_window_drag(win, handle_widgets):
    """Attach mouse drag-to-move handlers to specified handle widgets."""
    def _start_drag(e):
        try:
            if getattr(win, "master", None) is not None:
                win.master.winfo_toplevel()._active_raised_window = win
            win.lift()
        except Exception:
            pass
        win._drag_start_x = e.x_root
        win._drag_start_y = e.y_root
        win._win_x = win.winfo_x()
        win._win_y = win.winfo_y()

    def _on_drag(e):
        dx = e.x_root - win._drag_start_x
        dy = e.y_root - win._drag_start_y
        win.geometry(f"+{win._win_x + dx}+{win._win_y + dy}")

    for w in handle_widgets:
        w.bind("<Button-1>", _start_drag)
        w.bind("<B1-Motion>", _on_drag)


class VGADisplayWindow(tk.Toplevel):
    """Frameless 640x480 @ 60Hz VGA Monitor Simulation Window matching Main Application styling."""

    def __init__(self, parent, sim_engine):
        super().__init__(parent)
        self.sim_engine = sim_engine
        center_on_parent(self, parent, 670, 560)
        self.minsize(640, 500)
        self.configure(bg="#121212")
        apply_main_window_style(self)

        self._build_ui()
        self.redraw()
        self.deiconify()
        try:
            if parent is not None:
                parent.winfo_toplevel()._active_raised_window = self
        except Exception:
            pass
        self.lift()
        self.focus_force()

    def _build_ui(self):
        # 1. Custom dark title bar, placed directly in the root window (no nested borders)
        tb = tk.Frame(self, bg="#181818", height=38, padx=12)
        tb.pack(side=tk.TOP, fill=tk.X)
        tb.pack_propagate(False)

        title_lbl = tk.Label(
            tb, text="จอ VGA",
            bg="#181818", fg=TXT_MUTED, font=(FONT_UI, 9)
        )
        title_lbl.pack(side=tk.LEFT)

        btn_close = tk.Button(
            tb, text="✕", bg="#181818", fg=TXT_MUTED,
            activebackground=ACCENT_RED, activeforeground=TXT_ON_WHITE,
            bd=0, highlightthickness=0, width=4, pady=6, cursor="hand2",
            font=(FONT_UI, 9, "bold"), command=self.destroy
        )
        btn_close.pack(side=tk.RIGHT)
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg=TXT_ON_WHITE))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg="#181818", fg=TXT_MUTED))

        res_lbl = tk.Label(
            tb, text="640×480, 60 Hz · framebuffer 0xFF000000",
            bg="#181818", fg=TXT_DIM, font=(FONT_UI, 8), padx=10
        )
        res_lbl.pack(side=tk.RIGHT)

        attach_window_drag(self, [tb, title_lbl, res_lbl])

        self.sync_lbl = res_lbl

        # 3. VGA Screen Canvas (Directly packed in window - No nested bezel/border frames!)
        self.canvas = tk.Canvas(self, bg="#000000", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Redraw on every resize so the picture always fills the window
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def redraw(self):
        w = max(self.canvas.winfo_width(), 640)
        h = max(self.canvas.winfo_height(), 440)
        self.canvas.delete("all")

        # If CPU/FPGA has written pixel data to VRAM framebuffer, render it directly!
        if self.sim_engine.vga_buffer:
            self.canvas.create_rectangle(0, 0, w, h, fill="#000000", outline="")
            cw = w / 80.0
            ch = h / 60.0
            for addr, color_val in list(self.sim_engine.vga_buffer.items())[:4800]:
                offset = (addr - 0xFF000000) // 4
                gx = offset % 80
                gy = offset // 80
                if 0 <= gx < 80 and 0 <= gy < 60:
                    px0 = int(gx * cw)
                    py0 = int(gy * ch)
                    px1 = int((gx + 1) * cw) + 1
                    py1 = int((gy + 1) * ch) + 1
                    hex_col = f"#{color_val & 0xFFFFFF:06X}"
                    self.canvas.create_rectangle(px0, py0, px1, py1, fill=hex_col, outline="")
        else:
            # Empty state: a black screen (what a real monitor shows) plus what to do
            self.canvas.create_rectangle(0, 0, w, h, fill="#000000", outline="")
            self.canvas.create_text(w // 2, h // 2 - 12, text="ยังไม่มีภาพ",
                                    fill=TXT_MUTED, font=(FONT_UI, 11))
            self.canvas.create_text(w // 2, h // 2 + 14,
                                    text="เขียนพิกเซลที่แอดเดรส 0xFF000000 แล้วภาพจะแสดงที่นี่",
                                    fill=TXT_DIM, font=(FONT_UI, 9))


class UARTTerminalWindow(tk.Toplevel):
    """Frameless USB-UART Serial Terminal Window (COM Port Simulation) matching Main Application styling."""

    def __init__(self, parent, sim_engine, on_send_callback=None):
        super().__init__(parent)
        self.sim_engine = sim_engine
        self.on_send_callback = on_send_callback
        center_on_parent(self, parent, 670, 520)
        self.minsize(600, 420)
        self.configure(bg="#121212")
        apply_main_window_style(self)

        self._build_ui()
        self._refresh_content()
        self.deiconify()
        try:
            if parent is not None:
                parent.winfo_toplevel()._active_raised_window = self
        except Exception:
            pass
        self.lift()
        self.focus_force()

    def _build_ui(self):
        # 1. Custom dark title bar, placed directly in the root window (no nested borders)
        tb = tk.Frame(self, bg="#181818", height=38, padx=12)
        tb.pack(side=tk.TOP, fill=tk.X)
        tb.pack_propagate(False)

        title_lbl = tk.Label(
            tb, text="Serial monitor (USB-UART)",
            bg="#181818", fg=TXT_MUTED, font=(FONT_UI, 9)
        )
        title_lbl.pack(side=tk.LEFT)

        btn_close = tk.Button(
            tb, text="✕", bg="#181818", fg=TXT_MUTED,
            activebackground=ACCENT_RED, activeforeground=TXT_ON_WHITE,
            bd=0, highlightthickness=0, width=4, pady=6, cursor="hand2",
            font=(FONT_UI, 9, "bold"), command=self.destroy
        )
        btn_close.pack(side=tk.RIGHT)
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg=TXT_ON_WHITE))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg="#181818", fg=TXT_MUTED))

        baud_lbl = tk.Label(
            tb, text="115200 8-N-1 · 0xF0000010",
            bg="#181818", fg=TXT_DIM, font=(FONT_UI, 8), padx=10
        )
        baud_lbl.pack(side=tk.RIGHT)

        attach_window_drag(self, [tb, title_lbl, baud_lbl])

        # 3. Transmission / Input Bar (Packed above status bar)
        send_bar = tk.Frame(self, bg=BG_PANEL, padx=12, pady=8)
        send_bar.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            send_bar, text="ส่งเข้า CPU", bg=BG_PANEL, fg=TXT_MUTED, font=(FONT_UI, 9)
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            send_bar, textvariable=self.input_var, bg=BG_ELEVATED, fg=TXT_BRIGHT,
            insertbackground=TXT_BRIGHT, bd=0, highlightthickness=1,
            highlightbackground=BORDER_COLOR, highlightcolor=BORDER_HOVER, font=(FONT_CODE, 9)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=3)
        self.input_entry.bind("<Return>", lambda e: self.send_text())

        kit.button(send_bar, "ส่ง", self.send_text, kind="primary", pady=4).pack(side=tk.RIGHT)
        kit.button(send_bar, "ล้าง", self.clear_log, kind="link").pack(side=tk.RIGHT, padx=(0, 6))

        # 4. Terminal Screen (Scrollable Text Area directly in window)
        term_frame = tk.Frame(self, bg="#121212")
        term_frame.pack(fill=tk.BOTH, expand=True)

        self.scroll = SpotifyAutoScrollbar(term_frame, bg_track="#121212")
        self.text_area = tk.Text(
            term_frame, bg="#121212", fg=TXT_PRIMARY, insertbackground=TXT_BRIGHT,
            selectbackground=BG_HOVER, font=(FONT_CODE, 10), wrap=tk.WORD,
            bd=0, highlightthickness=0, yscrollcommand=self.scroll.set, padx=12, pady=10
        )
        self.scroll.command = self.text_area.yview
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_area.tag_configure("hint", foreground=TXT_DIM, font=(FONT_UI, 9))
        self.text_area.tag_configure("rx", foreground=TXT_MUTED)

    def _refresh_content(self):
        self.text_area.delete("1.0", tk.END)
        buf = self.sim_engine.uart_buffer
        if not buf:
            self._show_empty_hint()
        else:
            self.text_area.insert(tk.END, buf)
        self.text_area.see(tk.END)

    def append_text(self, text):
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

    def send_text(self):
        val = self.input_var.get()
        if not val:
            return
        self.send_raw(val + "\n")
        self.input_var.set("")

    def send_raw(self, text):
        self.sim_engine.send_uart_input(text)
        self.text_area.insert(tk.END, f"> {text}", ("rx",))
        self.text_area.see(tk.END)
        if self.on_send_callback:
            self.on_send_callback()

    def clear_log(self):
        self.sim_engine.uart_buffer = ""
        self.text_area.delete("1.0", tk.END)
        self._show_empty_hint()

    def _show_empty_hint(self):
        self.text_area.insert(tk.END, "ยังไม่มีข้อมูล โปรแกรมที่เขียนไปที่ 0xF0000010 จะแสดงที่นี่\n", ("hint",))
