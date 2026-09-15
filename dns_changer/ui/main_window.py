"""
Main application window — Tkinter implementation (stdlib, no external deps).
RTL layout for Persian UI.
The UI layer knows nothing about WMI, providers internals, or OS calls.
It only speaks to DNSService.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from ..core import DNSService, ServiceError
from ..core.providers import providers_by_category


# ── design tokens ────────────────────────────────────────────────────────────
_BG = "#f4f5f7"
_CARD = "#ffffff"
_FG = "#1a1a2e"
_MUTED = "#7a7f8a"
_ACCENT = "#3b82f6"
_ACCENT_H = "#2563eb"
_GREEN = "#10b981"
_RED = "#ef4444"
_BORDER = "#dde0e6"
_BTN_OFF = "#b8bec9"

_F = ("Segoe UI", 10)
_FS = ("Segoe UI", 9)
_FX = ("Consolas", 9)
_FB = ("Segoe UI", 11, "bold")


class MainWindow:
    """Tkinter main window. Call .run() to enter the event loop."""

    def __init__(self, service: DNSService) -> None:
        self._s = service
        self._root = tk.Tk()
        self._root.title("DNS Changer")
        self._root.resizable(False, False)
        self._root.configure(bg=_BG)

        self._keys: list[str | None] = []
        self._build()
        self._refresh()
        self._center()

    # ── public ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        self._root.mainloop()

    # ── layout ──────────────────────────────────────────────────────────────

    def _center(self) -> None:
        self._root.update_idletasks()
        w, h = 440, self._root.winfo_reqheight()
        sw, sh = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
        x, y = max((sw - w) // 2, 0), max((sh - h) // 2, 0)
        self._root.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self) -> None:
        r = self._root

        # accent strip
        tk.Frame(r, bg=_ACCENT, height=4).pack(fill="x", side="top")

        # status row
        sf = tk.Frame(r, bg=_BG)
        sf.pack(fill="x", padx=20, pady=(16, 4))
        self._dot = tk.Canvas(sf, width=12, height=12, bg=_BG, highlightthickness=0)
        self._dot.pack(side="right", padx=(0, 6))
        self._status_lbl = tk.Label(sf, text="", font=_FB, bg=_BG, fg=_MUTED, anchor="e")
        self._status_lbl.pack(side="right")

        # current DNS
        self._dns_lbl = tk.Label(r, text="", font=_FX, bg=_BG, fg=_MUTED, anchor="e")
        self._dns_lbl.pack(fill="x", padx=20, pady=(0, 14))

        # provider dropdown in a card. ttk.Combobox can't right-align its text
        # on Windows, so this is a small custom widget: right-aligned Entry +
        # right-aligned Listbox popup.
        card = tk.Frame(r, bg=_CARD, highlightbackground=_BORDER, highlightthickness=1)
        card.pack(fill="x", padx=20, pady=(0, 10))
        self._dd = tk.Frame(card, bg=_CARD)
        self._dd.pack(fill="x", padx=10, pady=8)

        self._dd_win: tk.Toplevel | None = None
        self._dd_list: tk.Listbox | None = None
        self._dd_entry = tk.Entry(
            self._dd,
            font=_F,
            justify="right",
            bd=0,
            bg=_CARD,
            readonlybackground=_CARD,
            highlightthickness=0,
        )
        self._dd_entry.insert(0, "")
        self._dd_entry.configure(state="readonly")
        self._dd_entry.pack(side="right", fill="x", expand=True, padx=(0, 4))
        self._dd_arrow = tk.Label(self._dd, text="▾", font=("Segoe UI", 11), fg=_MUTED, bg=_CARD)
        self._dd_arrow.pack(side="right")
        for w in (self._dd_entry, self._dd_arrow):
            w.bind("<Button-1>", self._toggle_dd)
        self._populate()

        # description
        self._desc_lbl = tk.Label(
            r,
            text="",
            font=_FS,
            bg=_BG,
            fg=_MUTED,
            anchor="e",
            justify="right",
            wraplength=370,
        )
        self._desc_lbl.pack(fill="x", padx=20, pady=(0, 14))

        # activate / deactivate button
        bf = tk.Frame(r, bg=_BG)
        bf.pack(fill="x", padx=20, pady=(0, 18))
        self._btn = tk.Button(
            bf,
            text="  Activate  ",
            command=self._on_toggle,
            font=("Segoe UI", 10, "bold"),
            bg=_BTN_OFF,
            fg="white",
            activebackground=_ACCENT_H,
            activeforeground="white",
            bd=0,
            cursor="hand2",
            relief="flat",
            state="disabled",
        )
        self._btn.pack(anchor="e")

        # button hover
        self._btn.bind("<Enter>", lambda _e: self._btn_hover(True))
        self._btn.bind("<Leave>", lambda _e: self._btn_hover(False))

    # ── custom RTL dropdown ─────────────────────────────────────────────────

    def _populate(self) -> None:
        self._keys: list[str | None] = [None]
        self._dd_items = ["یک provider انتخاب کنید"]

        for cat, provs in providers_by_category().items():
            if not provs:
                continue
            self._dd_items.append(f"▸ {cat.value}")
            self._keys.append(None)
            for p in provs:
                self._dd_items.append(p.name)
                self._keys.append(p.name)

        self._dd_index = 0
        self._set_dd_text(0)

    def _set_dd_text(self, i: int) -> None:
        self._dd_index = i
        e = self._dd_entry
        e.configure(state="normal")
        e.delete(0, "end")
        e.insert(0, self._dd_items[i])
        e.configure(state="readonly")

    def _key(self) -> str | None:
        i = self._dd_index
        return self._keys[i] if 0 <= i < len(self._keys) else None

    def _toggle_dd(self, _e) -> None:
        if self._dd_win is not None:
            self._close_dd()
        else:
            self._open_dd()

    def _open_dd(self) -> None:
        n = len(self._dd_items)
        win = tk.Toplevel(self._dd)
        win.wm_overrideredirect(True)
        x, y = self._dd.winfo_rootx(), self._dd.winfo_rooty() + self._dd.winfo_height()
        lb = tk.Listbox(
            win,
            font=_F,
            justify="right",
            exportselection=False,
            selectbackground=_ACCENT,
            selectforeground="white",
            bd=0,
            highlightthickness=1,
            highlightbackground=_BORDER,
            activestyle="none",
            width=24,
            height=min(n, 10),
        )
        for it in self._dd_items:
            lb.insert("end", it)
        lb.selection_set(self._dd_index)
        lb.pack(fill="both", expand=True)  # without this the listbox has zero size
        lb.bind("<ButtonRelease-1>", self._pick_dd)
        lb.bind("<Return>", lambda _e: self._pick_dd(lb.nearest(99999)))
        # size the borderless window to the listbox, aligned under the field
        win.update_idletasks()
        w = max(self._dd.winfo_width(), lb.winfo_reqwidth())
        win.geometry(f"{w}x{lb.winfo_reqheight()}+{x}+{y}")
        lb.focus_set()
        win.bind("<FocusOut>", lambda _e: self._close_dd())
        self._dd_win, self._dd_list = win, lb

    def _close_dd(self) -> None:
        if self._dd_win is not None:
            self._dd_win.destroy()
        self._dd_win = self._dd_list = None

    def _pick_dd(self, i) -> None:
        # <ButtonRelease-1> passes an event; <Return> passes an int
        if hasattr(i, "y"):
            i = self._dd_list.nearest(i.y)
        if isinstance(i, int) and 0 <= i < len(self._dd_items):
            self._set_dd_text(i)
        self._close_dd()
        self._on_select()

    # ── helpers ─────────────────────────────────────────────────────────────

    def _set_dot(self, color: str) -> None:
        c = self._dot
        c.delete("all")
        c.create_oval(2, 2, 10, 10, fill=color, outline="")

    def _btn_hover(self, on: bool) -> None:
        if self._btn["state"] == "disabled":
            return
        self._btn.config(bg=_ACCENT_H if on else _ACCENT)

    def _warn(self, msg: str) -> None:
        messagebox.showwarning("هشدار", msg)

    # ── slots ───────────────────────────────────────────────────────────────

    def _on_select(self) -> None:
        key = self._key()
        if key is None:
            self._btn.config(state="disabled", bg=_BTN_OFF)
            self._desc_lbl.config(text="")
            return

        p = self._s.available_providers().get(key)
        self._desc_lbl.config(text=p.description if p else "")
        self._btn.config(state="normal", bg=_ACCENT)

        if self._s.is_active:
            try:
                self._s.deactivate()
            except ServiceError as e:
                self._warn(str(e))
            self._status_lbl.config(text="Provider تغییر کرد — دوباره Activate کنید.")
            self._btn.config(text="  Activate  ")
            self._refresh()

    def _on_toggle(self) -> None:
        key = self._key()
        if key is None:
            return
        try:
            if self._s.is_active:
                self._s.deactivate()
            else:
                self._s.activate(key)
        except ServiceError as e:
            self._warn(str(e))
        self._refresh()

    # ── refresh ─────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        try:
            servers = self._s.current_dns()
        except Exception:
            servers = []
        dns_text = ", ".join(servers) if servers else "Automatic"
        self._dns_lbl.config(text=f"Current DNS:  {dns_text}")

        if self._s.is_active:
            self._status_lbl.config(text=f"DNS روی {self._s.active_provider} فعال است.", fg=_GREEN)
            self._btn.config(text="  Deactivate  ", state="normal", bg=_ACCENT)
            self._set_dot(_GREEN)
        else:
            msg = "یک provider انتخاب کنید." if self._key() is None else "DNS در حالت پیش‌فرض است."
            self._status_lbl.config(text=msg, fg=_MUTED)
            self._btn.config(text="  Activate  ")
            self._set_dot(_RED)
