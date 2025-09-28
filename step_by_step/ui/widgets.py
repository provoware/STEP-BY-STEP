"""Reusable Tk widgets for the STEP-BY-STEP interface."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """Frame with vertical scrollbar that never hides content."""

    def __init__(self, parent: tk.Misc, *, padding: int = 10, style: str = "TFrame") -> None:
        super().__init__(parent)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, padding=padding, style=style)
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.bind("<Configure>", self._on_resize)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)

    @property
    def body(self) -> ttk.Frame:
        """Return the frame that should receive child widgets."""

        return self.inner

    # ------------------------------------------------------------------
    def _on_inner_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ------------------------------------------------------------------
    def _on_resize(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    # ------------------------------------------------------------------
    def _bind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    # ------------------------------------------------------------------
    def _unbind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    # ------------------------------------------------------------------
    def _on_mousewheel(self, event: tk.Event) -> None:
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(-1, "units")


__all__ = ["ScrollableFrame"]

