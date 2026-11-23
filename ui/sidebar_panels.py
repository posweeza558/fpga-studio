# -*- coding: utf-8 -*-
"""
Left Sidebar Panels Mixin:
- Explorer View (Multi-folder collapsible tree, inline file/folder creation & rename)
- Search View (Project-wide code & 32-bit opcode search + Quick ISA Reference)
- Extensions View (Marketplace cards for C++, Python, Rust, Verilog HDL)
"""

import os
import re
import json
import shutil
import tkinter as tk
from tkinter import filedialog
from config.theme import (
    BG_SIDEBAR,
    BG_ELEVATED,
    BG_PILL_INACT,
    BG_HOVER,
    BORDER_COLOR,
    BORDER_HOVER,
    ACCENT_GREEN,
    ACCENT_YELLOW,
    ACCENT_RED,
    TXT_BRIGHT,
    TXT_PRIMARY,
    TXT_MUTED,
    TXT_DIM,
    TXT_ON_WHITE,
    FONT_UI,
    FONT_CODE,
)
from config.catalog import (
    DEFAULT_PROJECT_DIR,
    EXTENSIONS_STATE_FILE,
    DEFAULT_FILES,
    BADGE_STYLES,
    EXTENSIONS_CATALOG,
    EXT_TO_CATALOG,
    ISA_REFERENCE,
)
from ui.graphics import truncate_to_pixel_width, add_hover_border, get_antialiased_pill_photo
from ui.widgets import SpotifyPillButton, SpotifyPopupMenu, SpotifyAutoScrollbar, attach_tooltip


class SidebarPanelsMixin:
    """Provides Explorer, Search, and Extensions Marketplace sidebar views and workspace file operations."""

    # ==========================================================================
    # REAL DISK WORKSPACE & EXTENSIONS PERSISTENCE
    # ==========================================================================
    def _init_workspace_on_disk(self):
        os.makedirs(DEFAULT_PROJECT_DIR, exist_ok=True)
        existing = [
            f for f in os.listdir(DEFAULT_PROJECT_DIR)
            if os.path.isfile(os.path.join(DEFAULT_PROJECT_DIR, f))
        ]
        if not existing:
            for fname, content in DEFAULT_FILES.items():
                fpath = os.path.join(DEFAULT_PROJECT_DIR, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)

    def _load_extensions_state(self):
        # All extensions (C++, Python, Rust, Verilog) are enabled 100% out-of-the-box
        return {item["id"] for item in EXTENSIONS_CATALOG}

    def _save_extensions_state(self):
        pass

    def _is_file_missing_extension(self, filepath):
        # All extensions are built-in and active by default; never prompt
        return None

    def _list_workspace_folders(self):
        if not os.path.isdir(self.workspace_root):
            return []
        folders = []
        for entry in sorted(os.listdir(self.workspace_root)):
            full = os.path.join(self.workspace_root, entry)
            if os.path.isdir(full) and not entry.startswith("."):
                folders.append(full)
        if not folders and os.path.isdir(self.project_dir):
            folders.append(self.project_dir)
        return folders

    def _list_files_in_dir(self, folder_path):
        if not os.path.isdir(folder_path):
            return []
        items = []
        for fn in sorted(os.listdir(folder_path)):
            full = os.path.join(folder_path, fn)
            if os.path.isfile(full) and not fn.startswith("."):
                items.append(fn)
        return items

    # ==========================================================================
    # VIEW 1: MULTI-FOLDER COLLAPSIBLE EXPLORER
    # ==========================================================================
    def _build_explorer_view(self):
        hdr = tk.Frame(self.view_explorer, bg=BG_SIDEBAR, padx=14, pady=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Explorer", bg=BG_SIDEBAR, fg=TXT_MUTED,
                 font=(FONT_UI, 11, "bold")).pack(side=tk.LEFT)

        # Compact icon actions (they no longer clip when the sidebar narrows)
        icon_font = getattr(self, "icon_font_name", "Segoe MDL2 Assets")
        for glyph, tip, btn_cmd in reversed([
            ("", "ไฟล์ใหม่ (Ctrl+N)",  self.start_inline_new_file),
            ("", "โฟลเดอร์ใหม่",       self.start_inline_new_project),
            ("", "เปิดโฟลเดอร์...",    self.open_folder_dialog),
        ]):
            b = tk.Button(
                hdr, text=glyph, bd=0, highlightthickness=0, width=3, pady=2,
                bg=BG_SIDEBAR, fg=TXT_MUTED, activebackground=BG_HOVER, activeforeground=ACCENT_GREEN,
                cursor="hand2", font=(icon_font, 10), command=btn_cmd
            )
            b.pack(side=tk.RIGHT, padx=1)
            b.bind("<Enter>", lambda e, w=b: w.config(bg=BG_HOVER, fg=TXT_BRIGHT))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=BG_SIDEBAR, fg=TXT_MUTED))
            attach_tooltip(b, tip)

        tree_area = tk.Frame(self.view_explorer, bg=BG_SIDEBAR)
        tree_area.pack(fill=tk.BOTH, expand=True, pady=(6, 2))

        self.exp_scroll = SpotifyAutoScrollbar(tree_area, bg_track=BG_SIDEBAR)
        self.exp_canvas = tk.Canvas(
            tree_area, bg=BG_SIDEBAR, bd=0, highlightthickness=0,
            yscrollcommand=self.exp_scroll.set
        )
        self.exp_scroll.command = self.exp_canvas.yview
        self.exp_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.file_list_frame = tk.Frame(self.exp_canvas, bg=BG_SIDEBAR)
        self._exp_canvas_win = self.exp_canvas.create_window((0, 0), window=self.file_list_frame, anchor="nw")

        self.file_list_frame.bind(
            "<Configure>",
            lambda e: self.exp_canvas.configure(scrollregion=self.exp_canvas.bbox("all"))
        )
        self.exp_canvas.bind(
            "<Configure>",
            lambda e: self.exp_canvas.itemconfig(self._exp_canvas_win, width=e.width)
        )

        def _on_exp_wheel(event):
            first, last = self.exp_canvas.yview()
            if first <= 0.0 and last >= 1.0:
                return
            self.exp_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.exp_canvas.bind("<Enter>", lambda e: self.exp_canvas.bind_all("<MouseWheel>", _on_exp_wheel))
        self.exp_canvas.bind("<Leave>", lambda e: self.exp_canvas.unbind_all("<MouseWheel>"))

        self.file_buttons = {}
        self.folder_frames = {}

        # (Vivado/VHDL/COE export buttons used to be repeated here; they now
        #  live once under File > ส่งออก (Export).)

    def _clear_inline_entry(self):
        if self._inline_entry_row and self._inline_entry_row.winfo_exists():
            self._inline_entry_row.destroy()
        self._inline_entry_row = None

    def toggle_folder_expand(self, folder_path):
        abs_p = os.path.abspath(folder_path)
        self.project_dir = abs_p
        if abs_p in self.expanded_folders:
            self.expanded_folders.remove(abs_p)
        else:
            self.expanded_folders.add(abs_p)
        self.refresh_project_explorer()

    # ==========================================================================
    # FILE TREE (icon rows, real sub-folders + virtual type folders)
    # ==========================================================================
    # Virtual folders only change how the tree looks: files stay where they
    # are on disk, so the compiler, #include and saved paths are unaffected.
    TREE_GROUPS = [
        ("C / C++ Source", {".c", ".cpp", ".cc", ".cxx"}),
        ("Assembly",       {".s", ".asm"}),
        ("Verilog / HDL",  {".v", ".sv", ".vhd", ".vhdl"}),
        ("Headers",        {".h", ".hpp"}),
        ("Python / Rust",  {".py", ".rs"}),
        ("Docs & Config",  None),               # everything else
    ]
    TREE_FILE_ICONS = {
        ".c": ("c", ACCENT_GREEN), ".cpp": ("c++", "#569CD6"), ".cc": ("c++", "#569CD6"),
        ".s": ("asm", "#FFA657"), ".asm": ("asm", "#FFA657"),
        ".h": ("h", "#79C0FF"), ".hpp": ("h", "#79C0FF"),
        ".v": ("v", "#C586C0"), ".sv": ("sv", "#C586C0"), ".vhd": ("vhd", "#C586C0"), ".vhdl": ("vhd", "#C586C0"),
        ".py": ("py", "#FFD43B"), ".rs": ("rs", "#DEA584"),
        ".md": ("md", "#8B949E"), ".json": ("{ }", "#8B949E"), ".txt": ("txt", "#8B949E"),
    }
    TREE_ROW_BG = BG_SIDEBAR
    TREE_HOVER_BG = "#1F1F1F"
    TREE_ACTIVE_BG = "#232323"
    TREE_INDENT = 16

    @staticmethod
    def _natural_key(name):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]

    def _tree_group_files(self, files):
        groups = []
        claimed = set()
        for gname, exts in self.TREE_GROUPS:
            if exts is None:
                members = [f for f in files if f not in claimed]
            else:
                members = [f for f in files if os.path.splitext(f)[1].lower() in exts]
            claimed.update(members)
            if members:
                groups.append((gname, sorted(members, key=self._natural_key)))
        return groups

    def _list_subdirs(self, folder_path):
        try:
            return sorted(
                (os.path.join(folder_path, d) for d in os.listdir(folder_path)
                 if os.path.isdir(os.path.join(folder_path, d)) and not d.startswith(".")),
                key=lambda d: self._natural_key(os.path.basename(d)))
        except OSError:
            return []

    def _draw_file_pill(self, canvas, bg):
        label, col = canvas._pill_spec
        photo = get_antialiased_pill_photo(30, 16, bg, col, radius=5)
        canvas.config(bg=bg)
        canvas.delete("all")
        canvas.create_image(0, 0, image=photo, anchor="nw")
        canvas.create_text(15, 8, text=label, fill="#000000", font=(FONT_CODE, 7, "bold"))
        canvas._photo = photo

    def _tree_row(self, parent, depth, chevron, make_icon, text, fg, bold=False, count=None):
        """One flat tree row: [indent][chevron][icon][name ......][count]."""
        bg = self.TREE_ROW_BG
        row = tk.Frame(parent, bg=bg, height=28, cursor="hand2")
        row.pack(fill=tk.X, padx=(6, 6))
        row.pack_propagate(False)
        tk.Frame(row, bg=bg, width=8 + depth * self.TREE_INDENT).pack(side=tk.LEFT)
        chev = tk.Label(row, text=chevron, bg=bg, fg=TXT_MUTED, width=2, font=(FONT_UI, 10))
        chev.pack(side=tk.LEFT)
        icon = make_icon(row)
        icon.pack(side=tk.LEFT, padx=(0, 8))
        name = tk.Label(row, text=text, bg=bg, fg=fg, anchor="w",
                        font=(FONT_UI, 9, "bold" if bold else "normal"))
        name.pack(side=tk.LEFT, fill=tk.X, expand=True)
        parts = [row, chev, icon, name]
        if count is not None:
            cnt = tk.Label(row, text=str(count), bg=bg, fg=TXT_DIM, font=(FONT_UI, 8))
            cnt.pack(side=tk.RIGHT, padx=(4, 6))
            parts.append(cnt)
        return row, name, parts

    def _set_row_bg(self, parts, bg):
        for w in parts:
            if getattr(w, "_pill_spec", None):
                self._draw_file_pill(w, bg)
            else:
                w.config(bg=bg)
            for child in w.winfo_children() if w is parts[0] else ():
                if not getattr(child, "_pill_spec", None):
                    child.config(bg=bg)

    def _bind_row(self, parts, on_click, on_ctx=None, is_active=lambda: False):
        def _enter(e):
            self._set_row_bg(parts, self.TREE_HOVER_BG)

        def _leave(e):
            self._set_row_bg(parts, self.TREE_ACTIVE_BG if is_active() else self.TREE_ROW_BG)

        for w in parts:
            w.bind("<Button-1>", lambda e: on_click())
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
            if on_ctx:
                w.bind("<Button-3>", on_ctx)

    def _folder_icon(self, parent, is_open, color=TXT_BRIGHT):
        icon_font = getattr(self, "icon_font_name", "Segoe MDL2 Assets")
        return tk.Label(parent, text="" if is_open else "", bg=self.TREE_ROW_BG,
                        fg=color, font=(icon_font, 11))

    def _toggle_tree_key(self, key):
        exp = self._tree_expanded()
        if key in exp:
            exp.remove(key)
        else:
            exp.add(key)
        self.refresh_project_explorer()

    def _tree_expanded(self):
        if not hasattr(self, "_tree_open_keys"):
            # start tidy: only the C/C++ source folder of each project is open
            self._tree_open_keys = {f"{os.path.abspath(f)}|C / C++ Source"
                                    for f in self._list_workspace_folders()}
        return self._tree_open_keys

    def _render_file_row(self, parent, depth, full_p, folder_for_ctx):
        fname = os.path.basename(full_p)
        ext = os.path.splitext(fname)[1].lower()
        label, col = self.TREE_FILE_ICONS.get(ext, ("•", "#8B949E"))
        def make_pill(row):
            c = tk.Canvas(row, width=30, height=16, bd=0, highlightthickness=0, bg=self.TREE_ROW_BG)
            c._pill_spec = (label, col)
            self._draw_file_pill(c, self.TREE_ROW_BG)
            return c

        missing_ext = self._is_file_missing_extension(full_p) is not None
        has_err = (full_p in self.file_errors) and not missing_ext
        display = truncate_to_pixel_width(fname, (FONT_UI, 9), max_px=180)
        row, name, parts = self._tree_row(parent, depth, "", make_pill, display, TXT_PRIMARY)
        pill = parts[2]
        err_dot = tk.Label(row, text="●" if (has_err or missing_ext) else "", bg=self.TREE_ROW_BG,
                           fg=ACCENT_YELLOW if missing_ext else ACCENT_RED, font=(FONT_UI, 8, "bold"))
        err_dot.pack(side=tk.RIGHT, padx=(2, 6))
        parts.append(err_dot)

        def _ctx(event, fp=full_p, fn=fname, r=row, p=folder_for_ctx):
            m = SpotifyPopupMenu(self)
            m.add_command(f"เปลี่ยนชื่อไฟล์ ({fn})", command=lambda: self.start_inline_rename_file(fp, r))
            m.add_command(f"ลบไฟล์ ({fn})", command=lambda: self.delete_file_direct(fp))
            m.add_separator()
            m.add_command("เปิดโฟลเดอร์จริงใน Windows Explorer", command=lambda: os.startfile(p))
            m.show(event.x_root, event.y_root)

        is_act = lambda fp=full_p: bool(self.current_file_path) and fp == os.path.abspath(self.current_file_path)
        self._bind_row(parts, lambda fp=full_p: self.load_file_path(fp), _ctx, is_act)
        self.file_buttons[full_p] = (row, pill, name, err_dot, parts)

    def _render_subdir(self, parent, depth, dir_path):
        """Real folder on disk below a project: collapsible, files natural-sorted."""
        abs_d = os.path.abspath(dir_path)
        is_open = abs_d in self.expanded_folders
        row, name, parts = self._tree_row(parent, depth, "▾" if is_open else "▸",
                                          lambda r: self._folder_icon(r, is_open),
                                          os.path.basename(abs_d), TXT_BRIGHT)

        def _ctx(event, p=abs_d, fn=os.path.basename(abs_d)):
            m = SpotifyPopupMenu(self)
            m.add_command("สร้างไฟล์ใหม่ในโฟลเดอร์นี้", command=lambda: self.start_inline_new_file(target_dir=p))
            m.add_command("เปิดโฟลเดอร์ใน Windows Explorer", command=lambda: os.startfile(p))
            m.add_separator()
            m.add_command(f"ลบโฟลเดอร์ ({fn})", command=lambda: self.delete_folder_direct(p))
            m.show(event.x_root, event.y_root)

        def _toggle(p=abs_d):
            if p in self.expanded_folders:
                self.expanded_folders.discard(p)
            else:
                self.expanded_folders.add(p)
            self.refresh_project_explorer()

        self._bind_row(parts, _toggle, _ctx)
        box = tk.Frame(parent, bg=self.TREE_ROW_BG)
        self.folder_frames[abs_d] = box
        if is_open:
            box.pack(fill=tk.X)
            for sub in self._list_subdirs(abs_d):
                self._render_subdir(box, depth + 1, sub)
            for fn in sorted(self._list_files_in_dir(abs_d), key=self._natural_key):
                self._render_file_row(box, depth + 1, os.path.abspath(os.path.join(abs_d, fn)), abs_d)

    def refresh_project_explorer(self):
        self._clear_inline_entry()
        for w in self.file_list_frame.winfo_children():
            w.destroy()
        self.file_buttons.clear()
        self.folder_frames.clear()
        open_keys = self._tree_expanded()

        for folder_path in self._list_workspace_folders():
            abs_f = os.path.abspath(folder_path)
            is_expanded = abs_f in self.expanded_folders
            is_active_proj = (abs_f == os.path.abspath(self.project_dir))

            # --- project (workspace) folder
            title = truncate_to_pixel_width(os.path.basename(abs_f) or abs_f, (FONT_UI, 9, "bold"), max_px=190)
            proj_col = ACCENT_GREEN if is_active_proj else TXT_BRIGHT
            row, name, parts = self._tree_row(self.file_list_frame, 0, "▾" if is_expanded else "▸",
                                              lambda r, o=is_expanded, c=proj_col: self._folder_icon(r, o, c),
                                              title, proj_col, bold=True)

            def _show_folder_ctx(event, p=abs_f, fn=os.path.basename(abs_f)):
                m = SpotifyPopupMenu(self)
                m.add_command("สร้างไฟล์ใหม่ในโฟลเดอร์นี้", command=lambda: self.start_inline_new_file(target_dir=p))
                m.add_command("เปิดโฟลเดอร์ใน Windows Explorer", command=lambda: os.startfile(p))
                m.add_separator()
                m.add_command(f"ลบโฟลเดอร์ ({fn})", command=lambda: self.delete_folder_direct(p))
                m.show(event.x_root, event.y_root)

            self._bind_row(parts, lambda p=abs_f: self.toggle_folder_expand(p), _show_folder_ctx)

            files_box = tk.Frame(self.file_list_frame, bg=self.TREE_ROW_BG)
            self.folder_frames[abs_f] = files_box
            if not is_expanded:
                continue
            files_box.pack(fill=tk.X)

            # --- real sub-folders first
            for sub in self._list_subdirs(abs_f):
                self._render_subdir(files_box, 1, sub)

            # --- then the project's own files, grouped into virtual folders
            for gname, members in self._tree_group_files(self._list_files_in_dir(abs_f)):
                key = f"{abs_f}|{gname}"
                g_open = key in open_keys
                g_row, g_name, g_parts = self._tree_row(files_box, 1, "▾" if g_open else "▸",
                                                        lambda r, o=g_open: self._folder_icon(r, o, TXT_MUTED),
                                                        gname, TXT_PRIMARY, count=len(members))
                self._bind_row(g_parts, lambda k=key: self._toggle_tree_key(k))
                if g_open:
                    g_box = tk.Frame(files_box, bg=self.TREE_ROW_BG)
                    g_box.pack(fill=tk.X)
                    for fn in members:
                        self._render_file_row(g_box, 2, os.path.abspath(os.path.join(abs_f, fn)), abs_f)

        self._highlight_active_file_in_explorer()
        self.file_list_frame.update_idletasks()
        self.exp_canvas.configure(scrollregion=self.exp_canvas.bbox("all"))

    def _highlight_active_file_in_explorer(self):
        cur_abs = os.path.abspath(self.current_file_path) if self.current_file_path else ""
        for full_p, (row, pill, name, err_dot, parts) in self.file_buttons.items():
            active = (full_p == cur_abs)
            missing_ext = self._is_file_missing_extension(full_p) is not None
            has_err = (full_p in self.file_errors) and not missing_ext
            self._set_row_bg(parts, self.TREE_ACTIVE_BG if active else self.TREE_ROW_BG)
            err_dot.config(
                text="●" if (has_err or missing_ext) else "",
                fg=ACCENT_YELLOW if missing_ext else ACCENT_RED
            )
            if missing_ext:
                name.config(fg=ACCENT_YELLOW)
            elif has_err:
                name.config(fg=ACCENT_RED)
            else:
                name.config(fg=ACCENT_GREEN if active else TXT_PRIMARY,
                            font=(FONT_UI, 9, "bold" if active else "normal"))

    # ==========================================================================
    # INLINE FILE & FOLDER CREATION / RENAME / DELETE
    # ==========================================================================
    def start_inline_new_file(self, target_dir=None):
        if self.left_sidebar_mode != "explorer":
            self.switch_left_sidebar("explorer", toggle=False)
        if target_dir:
            self.project_dir = os.path.abspath(target_dir)
        abs_proj = os.path.abspath(self.project_dir)
        if abs_proj not in self.expanded_folders:
            self.expanded_folders.add(abs_proj)
            self.refresh_project_explorer()
        else:
            self._clear_inline_entry()

        parent_box = self.folder_frames.get(abs_proj, self.file_list_frame)
        row = tk.Frame(parent_box, bg="#1F1F1F", highlightbackground=ACCENT_GREEN, highlightthickness=1, padx=6, pady=3)
        row.pack(fill=tk.X, padx=(14, 6), pady=3)
        self._inline_entry_row = row

        tk.Label(row, text="+", bg="#1F1F1F", fg=ACCENT_GREEN, font=(FONT_CODE, 9, "bold"), width=2).pack(side=tk.LEFT)

        ent = tk.Entry(
            row, bg="#1F1F1F", fg=TXT_BRIGHT, insertbackground=ACCENT_GREEN,
            bd=0, relief="flat", font=(FONT_CODE, 9)
        )
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ent.focus_set()

        done = [False]

        def commit_new_file(event=None):
            if done[0]:
                return
            fname = ent.get().strip()
            if not fname:
                cancel_new_file()
                return
            done[0] = True
            self._clear_inline_entry()

            fpath = os.path.join(self.project_dir, fname)
            if not os.path.exists(fpath):
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("")
            self.refresh_project_explorer()
            self.load_file_path(fpath)
            ext = os.path.splitext(fname)[1]
            mode_note = " (โหมด TEXT)" if not ext else ""
            self.status_lbl.config(text=f"สร้างไฟล์ว่าง {fname}{mode_note} เรียบร้อย")

        def cancel_new_file(event=None):
            if done[0]:
                return
            done[0] = True
            self._clear_inline_entry()

        def on_focus_out(event=None):
            if ent.get().strip() == "":
                cancel_new_file()

        ent.bind("<Return>", commit_new_file)
        ent.bind("<Escape>", cancel_new_file)
        ent.bind("<FocusOut>", on_focus_out)

    def start_inline_new_project(self):
        if self.left_sidebar_mode != "explorer":
            self.switch_left_sidebar("explorer", toggle=False)
        self._clear_inline_entry()

        row = tk.Frame(self.file_list_frame, bg="#1F1F1F", highlightbackground=ACCENT_GREEN, highlightthickness=1, padx=6, pady=3)
        row.pack(fill=tk.X, padx=6, pady=3)
        self._inline_entry_row = row

        tk.Label(row, text="▸", bg="#1F1F1F", fg=ACCENT_GREEN, font=(FONT_CODE, 9, "bold"), width=2).pack(side=tk.LEFT)

        ent = tk.Entry(
            row, bg="#1F1F1F", fg=TXT_BRIGHT, insertbackground=ACCENT_GREEN,
            bd=0, relief="flat", font=(FONT_CODE, 9)
        )
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ent.focus_set()

        done = [False]

        def commit_new_folder(event=None):
            if done[0]:
                return
            proj_name = ent.get().strip()
            if not proj_name:
                cancel_new_folder()
                return
            done[0] = True
            self._clear_inline_entry()

            new_dir = os.path.abspath(os.path.join(self.workspace_root, proj_name))
            os.makedirs(new_dir, exist_ok=True)
            self.project_dir = new_dir
            self.expanded_folders.add(new_dir)
            self.refresh_project_explorer()
            self.status_lbl.config(text=f"สร้างโฟลเดอร์ว่าง '{proj_name}' เรียบร้อย")

        def cancel_new_folder(event=None):
            if done[0]:
                return
            done[0] = True
            self._clear_inline_entry()

        def on_focus_out(event=None):
            if ent.get().strip() == "":
                cancel_new_folder()

        ent.bind("<Return>", commit_new_folder)
        ent.bind("<Escape>", cancel_new_folder)
        ent.bind("<FocusOut>", on_focus_out)

    def start_inline_rename_file(self, old_full_path, row_widget):
        self._clear_inline_entry()
        old_name = os.path.basename(old_full_path)
        folder_dir = os.path.dirname(old_full_path)
        parent_box = row_widget.master

        row = tk.Frame(parent_box, bg="#1F1F1F", highlightbackground=ACCENT_GREEN, highlightthickness=1, padx=6, pady=3)
        row.pack(fill=tk.X, padx=(14, 6), pady=2, before=row_widget)
        self._inline_entry_row = row

        ent = tk.Entry(
            row, bg="#1F1F1F", fg=TXT_BRIGHT, insertbackground=ACCENT_GREEN,
            bd=0, relief="flat", font=(FONT_CODE, 9)
        )
        ent.insert(0, old_name)
        ent.select_range(0, tk.END)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ent.focus_set()

        done = [False]

        def commit_rename(event=None):
            if done[0]:
                return
            new_name = ent.get().strip()
            if not new_name or new_name == old_name:
                cancel_rename()
                return
            done[0] = True
            self._clear_inline_entry()

            old_abs = os.path.abspath(old_full_path)
            new_p = os.path.abspath(os.path.join(folder_dir, new_name))
            try:
                os.rename(old_abs, new_p)
                if old_abs in self.file_errors:
                    self.file_errors[new_p] = self.file_errors.pop(old_abs)
                if old_abs in self.open_tabs:
                    self.open_tabs[self.open_tabs.index(old_abs)] = new_p
                self.refresh_project_explorer()
                if os.path.abspath(self.current_file_path) == old_abs:
                    self.load_file_path(new_p)
                else:
                    self._refresh_editor_tabs()
                self.status_lbl.config(text=f"เปลี่ยนชื่อไฟล์เป็น {new_name} เรียบร้อย")
            except Exception as e:
                self.status_lbl.config(text=f"เปลี่ยนชื่อไม่สำเร็จ: {e}")

        def cancel_rename(event=None):
            if done[0]:
                return
            done[0] = True
            self._clear_inline_entry()

        def on_focus_out(event=None):
            if ent.get().strip() == "":
                cancel_rename()

        ent.bind("<Return>", commit_rename)
        ent.bind("<Escape>", cancel_rename)
        ent.bind("<FocusOut>", on_focus_out)

    def open_folder_dialog(self):
        chosen = filedialog.askdirectory(
            title="เลือกโฟลเดอร์โปรเจกต์ (คลิกขวาสร้างโฟลเดอร์/ไฟล์ในหน้าต่างนี้ได้เลย)",
            initialdir=self.workspace_root,
            mustexist=False
        )
        if not chosen:
            return
        chosen_abs = os.path.abspath(chosen)
        os.makedirs(chosen_abs, exist_ok=True)
        parent_dir = os.path.dirname(chosen_abs)
        if os.path.isdir(parent_dir) and parent_dir != chosen_abs:
            self.workspace_root = parent_dir
        else:
            self.workspace_root = chosen_abs
        self.project_dir = chosen_abs
        self.expanded_folders.add(chosen_abs)
        self.refresh_project_explorer()
        files = self._list_files_in_dir(chosen_abs)
        if files:
            self.load_file_path(os.path.join(chosen_abs, files[0]))
        self.status_lbl.config(text=f"เปิดโฟลเดอร์: {os.path.basename(chosen_abs)}")

    def delete_file_direct(self, full_path):
        try:
            abs_p = os.path.abspath(full_path)
            fname = os.path.basename(abs_p)
            os.remove(abs_p)
            self.file_errors.pop(abs_p, None)
            if abs_p in self.open_tabs:
                self.open_tabs.remove(abs_p)
            self.refresh_project_explorer()
            if os.path.abspath(self.current_file_path) == abs_p:
                if self.open_tabs:
                    self.load_file_path(self.open_tabs[-1])
                else:
                    files = self._list_files_in_dir(self.project_dir)
                    if files:
                        self.load_file_path(os.path.join(self.project_dir, files[0]))
                    else:
                        self.current_file = ""
                        self.current_file_path = ""
                        self.code_text.delete("1.0", tk.END)
                        self._refresh_editor_tabs()
            else:
                self._refresh_editor_tabs()
            self.status_lbl.config(text=f"ลบไฟล์ {fname} เรียบร้อย")
        except Exception as e:
            self.status_lbl.config(text=f"ลบไฟล์ไม่สำเร็จ: {e}")

    def delete_folder_direct(self, folder_path):
        try:
            shutil.rmtree(folder_path)
            self.expanded_folders.discard(os.path.abspath(folder_path))
            folders = self._list_workspace_folders()
            if folders:
                self.project_dir = folders[0]
            self.refresh_project_explorer()
            self._refresh_editor_tabs()
        except Exception as e:
            self.status_lbl.config(text=f"ลบโฟลเดอร์ไม่สำเร็จ: {e}")

    # ==========================================================================
    # VIEW 2: SEARCH & INSTRUCTION FINDER SIDEBAR
    # ==========================================================================
    def _build_search_view(self):
        hdr = tk.Frame(self.view_search, bg=BG_SIDEBAR, padx=14, pady=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="SEARCH", bg=BG_SIDEBAR, fg=TXT_BRIGHT,
                 font=(FONT_UI, 10, "bold")).pack(side=tk.LEFT)

        search_box = tk.Frame(
            self.view_search, bg=BG_ELEVATED, padx=10, pady=6,
            highlightthickness=1, highlightbackground="#2E2E2E"
        )
        search_box.pack(fill=tk.X, padx=12, pady=(0, 8))
        add_hover_border(search_box, BG_ELEVATED, "#262626", "#2E2E2E", ACCENT_GREEN)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_box, textvariable=self.search_var,
            bg=BG_ELEVATED, fg=TXT_BRIGHT, insertbackground=ACCENT_GREEN,
            bd=0, relief="flat", font=(FONT_UI, 9)
        )
        self.search_entry.pack(fill=tk.X)
        self.search_entry.bind("<KeyRelease>", self._run_project_search)

        tk.Label(self.view_search, text="พิมพ์คำค้นหา เช่น SWITCH, lw, jal, 0x0018, 0xF0000000",
                 bg=BG_SIDEBAR, fg=TXT_DIM, font=(FONT_UI, 8), anchor="w", padx=14).pack(fill=tk.X)

        self.search_summary_lbl = tk.Label(
            self.view_search, text="ผลลัพธ์การค้นหา (คลิกเพื่อกระโดดไปยังจุดนั้น)",
            bg=BG_SIDEBAR, fg=ACCENT_GREEN, font=(FONT_UI, 9, "bold"), anchor="w", padx=14, pady=6
        )
        self.search_summary_lbl.pack(fill=tk.X)

        list_wrap = tk.Frame(self.view_search, bg="#181818", highlightthickness=1, highlightbackground="#242424")
        list_wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self.search_scroll = SpotifyAutoScrollbar(list_wrap, bg_track="#181818")
        self.search_results_list = tk.Listbox(
            list_wrap, bg="#181818", fg=TXT_PRIMARY,
            selectbackground="#282828", selectforeground=ACCENT_GREEN,
            bd=0, highlightthickness=0, font=(FONT_CODE, 8), activestyle="none",
            yscrollcommand=self.search_scroll.set
        )
        self.search_scroll.command = self.search_results_list.yview
        self.search_results_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.search_results_list.bind("<<ListboxSelect>>", self._on_search_result_clicked)
        self._search_targets = []

        isa_box = tk.Frame(self.view_search, bg="#181818", padx=12, pady=10, highlightthickness=1, highlightbackground="#242424")
        isa_box.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(isa_box, text="คู่มือคำสั่ง RISC-V / MIPS ด่วน", bg="#181818", fg=TXT_BRIGHT,
                 font=(FONT_UI, 9, "bold"), anchor="w").pack(fill=tk.X, pady=(0, 4))
        self.isa_hint_lbl = tk.Label(
            isa_box, text="พิมพ์ชื่อคำสั่ง (เช่น lui, addi, lw, sw, beq, jal) ในช่องค้นหาด้านบนเพื่อดูรูปแบบคำสั่ง",
            bg="#181818", fg=TXT_MUTED, font=(FONT_UI, 8), justify="left", wraplength=235, anchor="w"
        )
        self.isa_hint_lbl.pack(fill=tk.X)

    def _run_project_search(self, event=None):
        q = self.search_var.get().strip()
        self.search_results_list.delete(0, tk.END)
        self._search_targets.clear()
        self.code_text.tag_remove("search_hit", "1.0", tk.END)

        if not q:
            self.search_summary_lbl.config(text="ผลลัพธ์การค้นหา (คลิกเพื่อกระโดดไปยังจุดนั้น)")
            self.isa_hint_lbl.config(text="พิมพ์ชื่อคำสั่ง (เช่น lui, addi, lw, sw, beq, jal) ในช่องค้นหาด้านบนเพื่อดูรูปแบบคำสั่ง")
            return

        ql = q.lower()
        if ql in ISA_REFERENCE:
            self.isa_hint_lbl.config(text=ISA_REFERENCE[ql], fg=ACCENT_GREEN)
        else:
            self.isa_hint_lbl.config(text="ค้นหาทั้งในไฟล์โค้ดของโปรเจกต์ และในตาราง 32-bit Machine Code", fg=TXT_MUTED)

        for idx, ins in enumerate(self.compiled_ins):
            row_str = f"{ins['pc']} {ins['asm']} {ins['hex']} {ins['desc']}"
            if ql in row_str.lower():
                self.search_results_list.insert(tk.END, f"[32-bit {ins['pc']}] {ins['asm']} ({ins['hex']})")
                self._search_targets.append(("opcode", idx, None))

        for folder_p in self._list_workspace_folders():
            for fname in self._list_files_in_dir(folder_p):
                fpath = os.path.join(folder_p, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        for ln_no, line in enumerate(f, 1):
                            if ql in line.lower():
                                preview = line.strip()[:34]
                                self.search_results_list.insert(tk.END, f"[{fname}:{ln_no}] {preview}")
                                self._search_targets.append(("file", fpath, ln_no))
                except Exception:
                    pass

        code = self.code_text.get("1.0", tk.END)
        for m in re.finditer(re.escape(q), code, re.IGNORECASE):
            self.code_text.tag_add("search_hit", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

        self.search_summary_lbl.config(text=f"พบทั้งหมด {len(self._search_targets)} รายการ")

    def _on_search_result_clicked(self, event=None):
        sel = self.search_results_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._search_targets):
            return
        kind, a, b = self._search_targets[idx]
        if kind == "opcode":
            if not self.show_machine_panel_var.get():
                self.toggle_machine_panel()
            self.switch_right_view("opcode")
            iid = str(a)
            if self.op_tree.exists(iid):
                self.op_tree.selection_set(iid)
                self.op_tree.see(iid)
        elif kind == "file":
            if os.path.abspath(self.current_file_path) != os.path.abspath(a):
                self.load_file_path(a)
            self.code_text.mark_set(tk.INSERT, f"{b}.0")
            self.code_text.see(f"{b}.0")
            self._run_project_search()

    # ==========================================================================
    # VIEW 3: EXTENSIONS MARKETPLACE SIDEBAR
    # ==========================================================================
    def _build_extensions_view(self):
        hdr = tk.Frame(self.view_extensions, bg=BG_SIDEBAR, padx=14, pady=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="EXTENSIONS", bg=BG_SIDEBAR, fg=TXT_BRIGHT,
                 font=(FONT_UI, 10, "bold")).pack(side=tk.LEFT)

        tk.Label(
            self.view_extensions,
            text="ติดตั้งส่วนเสริมภาษาเพื่อเขียน C++, Python, Rust หรือส่งออก Verilog HDL ลงบอร์ด FPGA",
            bg=BG_SIDEBAR, fg=TXT_MUTED, font=(FONT_UI, 8), justify="left", wraplength=250, anchor="w", padx=14
        ).pack(fill=tk.X, pady=(0, 8))

        self.ext_cards_frame = tk.Frame(self.view_extensions, bg=BG_SIDEBAR)
        self.ext_cards_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self._refresh_extension_cards()

    def _refresh_extension_cards(self):
        for w in self.ext_cards_frame.winfo_children():
            w.destroy()

        for ext_info in EXTENSIONS_CATALOG:
            ext_id = ext_info["id"]
            is_inst = ext_id in self.installed_extensions

            card = tk.Frame(
                self.ext_cards_frame, bg="#181818", padx=10, pady=8,
                highlightthickness=1, highlightbackground="#252525"
            )
            card.pack(fill=tk.X, pady=4)
            add_hover_border(card, "#181818", "#202020", "#252525", BORDER_HOVER, sync_children=True)

            top = tk.Frame(card, bg="#181818")
            top.pack(fill=tk.X)

            badge = tk.Label(top, text=ext_info["badge"], bg=BG_ELEVATED, fg=ext_info["badge_color"],
                             font=(FONT_CODE, 9, "bold"), width=4, pady=3)
            badge.pack(side=tk.LEFT, padx=(0, 8))

            title_col = tk.Frame(top, bg="#181818")
            title_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(title_col, text=ext_info["name"], bg="#181818", fg=TXT_BRIGHT,
                     font=(FONT_UI, 9, "bold"), anchor="w").pack(fill=tk.X)
            tk.Label(title_col, text=ext_info["publisher"], bg="#181818", fg=TXT_DIM,
                     font=(FONT_UI, 8), anchor="w").pack(fill=tk.X)

            tk.Label(card, text=ext_info["desc"], bg="#181818", fg=TXT_MUTED,
                     font=(FONT_UI, 8), justify="left", wraplength=235, anchor="w").pack(fill=tk.X, pady=(6, 6))

            btn_row = tk.Frame(card, bg="#181818")
            btn_row.pack(fill=tk.X)

            if is_inst:
                b_uninst = SpotifyPillButton(
                    btn_row, text="✓ ติดตั้งแล้ว (ถอน)", bg_parent="#181818",
                    fill_col=BG_PILL_INACT, fg_col=ACCENT_GREEN, hover_fill="#2E2E2E",
                    font_spec=(FONT_UI, 8, "bold"), pad_x=10, height=26,
                    icon_font_name=self.icon_font_name,
                    command=lambda eid=ext_id: self.toggle_install_extension(eid)
                )
                b_uninst.pack(side=tk.LEFT)

                if ext_info["sample_file"]:
                    b_sample = SpotifyPillButton(
                        btn_row, text="+ ลองไฟล์ตัวอย่าง", bg_parent="#181818",
                        fill_col=ACCENT_GREEN, fg_col=TXT_ON_WHITE, hover_fill="#1FDF64",
                        font_spec=(FONT_UI, 8, "bold"), pad_x=10, height=26,
                        icon_font_name=self.icon_font_name,
                        command=lambda info=ext_info: self.create_extension_sample_file(info)
                    )
                    b_sample.pack(side=tk.RIGHT)
            else:
                b_inst = SpotifyPillButton(
                    btn_row, text="ดาวน์โหลด & ติดตั้ง (Install)", bg_parent="#181818",
                    fill_col=ACCENT_GREEN, fg_col=TXT_ON_WHITE, hover_fill="#1FDF64",
                    font_spec=(FONT_UI, 8, "bold"), pad_x=12, height=26,
                    icon_glyph="\uE896", icon_font_name=self.icon_font_name,
                    command=lambda eid=ext_id: self.toggle_install_extension(eid)
                )
                b_inst.pack(side=tk.LEFT)

    def toggle_install_extension(self, ext_id):
        ext_info = next((x for x in EXTENSIONS_CATALOG if x["id"] == ext_id), None)
        if not ext_info:
            return

        if ext_id in self.installed_extensions:
            self.installed_extensions.remove(ext_id)
            if ext_id == "verilog_exporter":
                self.tab_btn_verilog.pack_forget()
                if self.right_view_mode == "verilog":
                    self.switch_right_view("opcode")
            self.status_lbl.config(text=f"ถอนการติดตั้งส่วนเสริม {ext_info['name']} แล้ว")
        else:
            self.installed_extensions.add(ext_id)
            if ext_id == "verilog_exporter":
                self.tab_btn_verilog.pack(side=tk.LEFT, padx=(0, 6), before=self.tab_btn_coe)
            self._hide_extension_recommend_popup()
            self.status_lbl.config(text=f"ติดตั้งส่วนเสริม {ext_info['name']} สำเร็จ")

        self._save_extensions_state()
        self._refresh_extension_cards()
        self.refresh_project_explorer()
        self.compile_now()

    def create_extension_sample_file(self, ext_info):
        fname = ext_info["sample_file"]
        fpath = os.path.join(self.project_dir, fname)
        if not os.path.exists(fpath):
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(ext_info["sample_code"])
        self.expanded_folders.add(os.path.abspath(self.project_dir))
        self.refresh_project_explorer()
        self.load_file_path(fpath)
        self.switch_left_sidebar("explorer", toggle=False)
