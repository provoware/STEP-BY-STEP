"""Reusable info panels for the STEP-BY-STEP dashboard."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Callable, Dict, Iterable, Optional, Sequence, Tuple


def _hex_to_rgb(color: str) -> Tuple[float, float, float]:
    color = color.strip()
    if color.startswith("#"):
        color = color[1:]
    if len(color) != 6:
        raise ValueError("Farben bitte als #RRGGBB eingeben")
    r = int(color[0:2], 16) / 255.0
    g = int(color[2:4], 16) / 255.0
    b = int(color[4:6], 16) / 255.0
    return r, g, b


def _relative_luminance(rgb: Tuple[float, float, float]) -> float:
    def adjust(channel: float) -> float:
        return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4

    r, g, b = (adjust(channel) for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

LegendEntry = Tuple[str, str]
QuickLink = Tuple[str, str, Callable[[], None]]


def build_legend_panel(parent: ttk.LabelFrame, colors: Optional[Dict[str, str]] = None) -> None:
    """Create a legend that explains core tool areas in simple language."""
    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    bold_font = tkfont.Font(font=body_font)
    bold_font.configure(weight="bold")
    parent._legend_bold_font = bold_font  # type: ignore[attr-defined]
    description = ttk.Label(
        parent,
        text="Legende (Erklärung der Bereiche)",
        font=heading_font,
    )
    description.pack(anchor="w")

    legend_items: Iterable[LegendEntry] = (
        ("Dashboard", "Zentrale Übersicht mit Uhrzeit, Status und Speicherort."),
        (
            "Notizen",
            "Freies Textfeld zum Mitschreiben. Speichert automatisch beim Verlassen.",
        ),
        (
            "ToDo",
            "Liste offener Aufgaben. Zeigt Vorschau aus der Aufgabenverwaltung.",
        ),
        (
            "Playlist",
            "Anzeige gespeicherter Titel. Dient als Ausgangspunkt für den Audioplayer.",
        ),
        (
            "Legende & Mockup",
            "Hilfsbereich mit Erklärung, Entwurfsskizze (Mockup) und Strukturplan.",
        ),
    )

    for title, explanation in legend_items:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"{title}:", font=bold_font).pack(side="left")
        ttk.Label(
            row,
            text=explanation,
            wraplength=240,
            justify="left",
            font=body_font,
        ).pack(side="left", padx=(5, 0))


def build_mockup_panel(parent: ttk.LabelFrame, colors: Optional[Dict[str, str]] = None) -> None:
    """Create a simple text-based mockup that illustrates the grid layout."""
    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkTextFont")
    ttk.Label(parent, text="Mockup (Entwurf)", font=heading_font).pack(anchor="w")
    mockup_text = tk.Text(
        parent,
        height=8,
        width=40,
        wrap="word",
        relief="groove",
        font=body_font,
    )
    if colors:
        mockup_text.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            insertbackground=colors.get("accent", "black"),
        )
    mockup_text.pack(fill="both", expand=True, pady=(5, 0))
    mockup_text.insert(
        "1.0",
        """
+-------------------+-------------------+-------------------+
|  Notizen          |  ToDo Vorschau    |  Playlist         |
+-------------------+-------------------+-------------------+
|  Legende & Hilfe  |  Frei für Module  |  Frei für Module  |
+-------------------+-------------------+-------------------+
|  Strukturplan     |  Frei für Module  |  Frei für Module  |
+-------------------+-------------------+-------------------+
        """.strip()
    )
    mockup_text.configure(state="disabled")


def build_structure_panel(
    parent: ttk.LabelFrame, schema: Dict[str, Dict], colors: Optional[Dict[str, str]] = None
) -> None:
    """Render a folder structure tree view from a nested dictionary schema."""
    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Ordner- und Dateistruktur", font=heading_font).pack(
        anchor="w"
    )
    tree = ttk.Treeview(parent, show="tree", height=10)
    if colors:
        tree.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            fieldbackground=colors.get("surface", "white"),
        )
    tree.configure(font=body_font)
    tree.pack(fill="both", expand=True, pady=(5, 0))

    def insert_nodes(parent_id: str, node_schema: Dict[str, Dict]) -> None:
        for name, children in sorted(node_schema.items()):
            node_id = tree.insert(parent_id, "end", text=name)
            if isinstance(children, dict) and children:
                insert_nodes(node_id, children)

    insert_nodes("", schema)


def build_quicklinks_panel(
    parent: ttk.LabelFrame,
    links: Sequence[QuickLink],
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Render accessible quick actions for common tool workflows."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Schnelllinks", font=heading_font).pack(anchor="w")
    ttk.Label(
        parent,
        text=(
            "Tipp: Wählen Sie einen Button, um eine häufige Aktion zu starten. "
            "Alle Links besitzen eine Kurzbeschreibung."
        ),
        wraplength=260,
        justify="left",
        font=body_font,
    ).pack(anchor="w", pady=(2, 8))

    for label, description, command in links:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=4)
        button = ttk.Button(frame, text=label, command=command)
        if colors:
            button.configure(style="HighContrast.TButton")
        button.pack(side="left")
        ttk.Label(
            frame,
            text=description,
            wraplength=200,
            justify="left",
            font=body_font,
        ).pack(side="left", padx=(8, 0))


def build_font_tips_panel(
    parent: ttk.LabelFrame,
    colors: Optional[Dict[str, str]] = None,
    current_scale: float = 1.0,
) -> None:
    """Explain recommended zoom levels for each dashboard area."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Schriftgrößen-Empfehlungen", font=heading_font).pack(anchor="w")
    ttk.Label(
        parent,
        text=(
            "Aktueller Zoom (Schriftgröße): "
            f"{int(round(current_scale * 100))}% – über den Slider oben im Fenster anpassen."
        ),
        font=body_font,
        wraplength=320,
        justify="left",
    ).pack(anchor="w", pady=(2, 6))

    tree = ttk.Treeview(parent, columns=("bereich", "empfehlung"), show="headings", height=6)
    tree.heading("bereich", text="Bereich")
    tree.heading("empfehlung", text="Empfehlung")
    tree.column("bereich", width=140, anchor="w")
    tree.column("empfehlung", width=200, anchor="w")
    if colors:
        tree.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            fieldbackground=colors.get("surface", "white"),
        )
    tree.configure(font=body_font)
    tree.pack(fill="both", expand=True)

    recommendations = (
        ("Notizblock", "120 % – 140 % für lange Texte"),
        ("ToDo-Liste", "100 % – 120 % für mehr Zeilen"),
        ("Playlist", "100 % – 115 % damit Titel passen"),
        ("Info-Center", "115 % – 140 % für erklärende Texte"),
        ("Audiosteuerung", "120 % – 140 % für Regler"),
        ("Seitenleisten", "110 % – 130 % zum Lesen der Tipps"),
    )
    for entry in recommendations:
        tree.insert("", "end", values=entry)

    ttk.Label(
        parent,
        text=(
            "Tipp: Mit Strg+Plus/Minus (Zoom) bzw. dem Slider oben lässt sich der Wert auch per Tastatur anpassen."
        ),
        wraplength=320,
        justify="left",
        font=body_font,
    ).pack(anchor="w", pady=(6, 0))


def build_contrast_panel(parent: ttk.LabelFrame, colors: Optional[Dict[str, str]] = None) -> None:
    """Provide a simple WCAG contrast checker for custom color pairs."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Kontrast-Checker", font=heading_font).pack(anchor="w")
    ttk.Label(
        parent,
        text=(
            "Zwei Farben eingeben (Format #RRGGBB). Das Tool prüft, ob der Kontrast für Fließtext (4,5:1) "
            "und große Schrift (3,0:1) ausreicht."
        ),
        wraplength=320,
        justify="left",
        font=body_font,
    ).pack(anchor="w", pady=(2, 8))

    form = ttk.Frame(parent)
    form.pack(fill="x", pady=(0, 8))
    ttk.Label(form, text="Farbe 1 (Text)", font=body_font).grid(row=0, column=0, sticky="w")
    ttk.Label(form, text="Farbe 2 (Hintergrund)", font=body_font).grid(row=1, column=0, sticky="w", pady=(6, 0))

    entry_fg = ttk.Entry(form)
    entry_bg = ttk.Entry(form)
    entry_fg.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    entry_bg.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))
    form.columnconfigure(1, weight=1)

    if colors:
        entry_fg.insert(0, colors.get("on_surface", "#000000"))
        entry_bg.insert(0, colors.get("surface", "#FFFFFF"))
    else:
        entry_fg.insert(0, "#000000")
        entry_bg.insert(0, "#FFFFFF")

    result_var = tk.StringVar(value="Kontrast noch nicht berechnet")

    def evaluate_contrast() -> None:
        try:
            rgb_fg = _hex_to_rgb(entry_fg.get())
            rgb_bg = _hex_to_rgb(entry_bg.get())
            lum_fg = _relative_luminance(rgb_fg)
            lum_bg = _relative_luminance(rgb_bg)
            lighter = max(lum_fg, lum_bg)
            darker = min(lum_fg, lum_bg)
            ratio = (lighter + 0.05) / (darker + 0.05)
            meets_text = ratio >= 4.5
            meets_large = ratio >= 3.0
            text_part = "OK für Text" if meets_text else "zu niedrig für Fließtext"
            large_part = "; große Schrift passt" if meets_large else "; große Schrift kritisch"
            message = f"Kontrast {ratio:.2f}:1 – {text_part}{large_part}"
            result_var.set(message)
        except ValueError as error:
            result_var.set(str(error))

    button = ttk.Button(parent, text="Kontrast prüfen", command=evaluate_contrast)
    if colors:
        button.configure(style="HighContrast.TButton")
    button.pack(anchor="w")
    ttk.Label(parent, textvariable=result_var, wraplength=320, font=body_font).pack(
        anchor="w", pady=(6, 0)
    )


def build_release_panel(
    parent: ttk.LabelFrame,
    items: Sequence[Dict[str, object]],
    progress_text: str,
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Render the release checklist in a table."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Release-Checkliste", font=heading_font).pack(anchor="w")
    ttk.Label(parent, text=progress_text, font=body_font).pack(anchor="w", pady=(2, 6))

    tree = ttk.Treeview(parent, columns=("status", "title", "details"), show="headings", height=6)
    tree.heading("status", text="Status")
    tree.heading("title", text="Aufgabe")
    tree.heading("details", text="Details")
    tree.column("status", width=90, anchor="w")
    tree.column("title", width=220, anchor="w")
    tree.column("details", width=260, anchor="w")
    if colors:
        tree.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            fieldbackground=colors.get("surface", "white"),
        )
    tree.configure(font=body_font)
    tree.pack(fill="both", expand=True)

    for entry in items:
        done = bool(entry.get("done"))
        status = "✔ Erledigt" if done else "⏳ Offen"
        tree.insert(
            "",
            "end",
            values=(status, entry.get("title", ""), entry.get("details", "")),
            tags=("done" if done else "open",),
        )

    tree.tag_configure("done", foreground="#2e8540")
    tree.tag_configure("open", foreground="#c43c00")


__all__ = [
    "build_legend_panel",
    "build_font_tips_panel",
    "build_contrast_panel",
    "build_mockup_panel",
    "build_structure_panel",
    "build_quicklinks_panel",
    "build_release_panel",
]
