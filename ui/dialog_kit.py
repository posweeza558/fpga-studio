# -*- coding: utf-8 -*-
"""
Shared building blocks for the tool dialogs (flasher, RTL verify, synthesis,
wizards, monitors), so every dialog uses the same button vocabulary:

- primary:   the one action the dialog exists for (green fill, dark text)
- secondary: any other action (neutral fill, 1px border)
- link:      low-weight actions such as "Close" or "Locate..." (text only)

Keep at most one primary button per dialog.
"""

import tkinter as tk
from tkinter import ttk

from config.theme import (
    ACCENT_GREEN,
    ACCENT_HOVER,
    BG_BLACK,
    BG_EDITOR,
    BG_ELEVATED,
    BG_HOVER,
    BG_PILL_INACT,
    BORDER_COLOR,
    BORDER_HOVER,
    FONT_UI,
    TXT_BRIGHT,
    TXT_DIM,
    TXT_MUTED,
    TXT_ON_WHITE,
)

_STYLES = {
    #            bg              fg            hover bg      border          font weight
    "primary":   (ACCENT_GREEN,  TXT_ON_WHITE, ACCENT_HOVER, ACCENT_GREEN,  "bold"),
    "secondary": (BG_PILL_INACT, TXT_BRIGHT,   BG_HOVER,     BORDER_COLOR,  "bold"),
    "link":      (None,          TXT_MUTED,    None,         None,          "normal"),
}


def button(parent, text, command, kind="secondary", size=9, padx=None, pady=None):
    """A flat button in one of the three shared styles."""
    bg, fg, hover, border, weight = _STYLES[kind]
    parent_bg = parent.cget("bg")
    if kind == "link":
        bg = hover = border = parent_bg
    b = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=hover,
        activeforeground=TXT_ON_WHITE if kind == "primary" else TXT_BRIGHT,
        disabledforeground=TXT_DIM,
        bd=0, relief="flat", highlightthickness=0 if kind == "link" else 1,
        highlightbackground=border, highlightcolor=border,
        padx=padx if padx is not None else (16 if kind == "primary" else 12),
        pady=pady if pady is not None else (7 if kind == "primary" else 5),
        cursor="hand2", font=(FONT_UI, size, weight), takefocus=1,
    )

    def _enter(_):
        if str(b.cget("state")) == "disabled":
            return
        if kind == "link":
            b.config(fg=TXT_BRIGHT)
        else:
            b.config(bg=hover, highlightbackground=BORDER_HOVER if kind == "secondary" else hover)

    def _leave(_):
        if kind == "link":
            b.config(fg=fg)
        else:
            b.config(bg=b._kit_bg, highlightbackground=border)

    b._kit_bg = bg
    b.bind("<Enter>", _enter)
    b.bind("<Leave>", _leave)
    return b


def set_primary_busy(btn, busy, idle_text, busy_text):
    """Grey out a primary button while its job runs."""
    if busy:
        btn._kit_bg = BG_PILL_INACT
        btn.config(text=busy_text, state=tk.DISABLED, bg=BG_PILL_INACT, fg=TXT_MUTED,
                   highlightbackground=BORDER_COLOR)
    else:
        btn._kit_bg = ACCENT_GREEN
        btn.config(text=idle_text, state=tk.NORMAL, bg=ACCENT_GREEN, fg=TXT_ON_WHITE,
                   highlightbackground=ACCENT_GREEN)


def section_label(parent, text):
    """Small muted label above a block (log, table...)."""
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=TXT_MUTED,
                    font=(FONT_UI, 9, "bold"), anchor="w")


def apply_dark_ttk(root):
    """Dark Combobox / Checkbutton styling so native controls match the theme."""
    style = ttk.Style(root)
    style.configure(
        "TCombobox",
        fieldbackground=BG_EDITOR, background=BG_ELEVATED, foreground=TXT_BRIGHT,
        arrowcolor=TXT_MUTED, bordercolor=BORDER_COLOR, lightcolor=BORDER_COLOR,
        darkcolor=BORDER_COLOR, insertcolor=TXT_BRIGHT, padding=(6, 4),
        selectbackground=BG_EDITOR, selectforeground=TXT_BRIGHT,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BG_EDITOR), ("disabled", BG_BLACK)],
        foreground=[("readonly", TXT_BRIGHT), ("disabled", TXT_DIM)],
        background=[("active", BG_HOVER), ("readonly", BG_ELEVATED)],
        bordercolor=[("focus", BORDER_HOVER), ("hover", BORDER_HOVER)],
        arrowcolor=[("hover", TXT_BRIGHT)],
        selectbackground=[("readonly", BG_EDITOR)],
        selectforeground=[("readonly", TXT_BRIGHT)],
    )
    # drop-down list
    root.option_add("*TCombobox*Listbox.background", BG_ELEVATED)
    root.option_add("*TCombobox*Listbox.foreground", TXT_BRIGHT)
    root.option_add("*TCombobox*Listbox.selectBackground", BG_HOVER)
    root.option_add("*TCombobox*Listbox.selectForeground", TXT_BRIGHT)
    root.option_add("*TCombobox*Listbox.borderWidth", 0)
    root.option_add("*TCombobox*Listbox.font", (FONT_UI, 9))
