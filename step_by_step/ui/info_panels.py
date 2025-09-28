"""Reusable info panels for the STEP-BY-STEP dashboard."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


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


def build_database_insights_panel(
    parent: ttk.LabelFrame,
    stats: Optional[Dict[str, object]] = None,
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Show SQLite (leichte Datenbank) highlights in an accessible layout."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    mono_font = tkfont.nametofont("TkFixedFont")
    bold_font = tkfont.Font(font=body_font)
    bold_font.configure(weight="bold")
    parent._db_fonts = (bold_font, mono_font)  # type: ignore[attr-defined]

    ttk.Label(parent, text="Datenbank-Überblick", font=heading_font).pack(anchor="w")
    ttk.Label(
        parent,
        text=(
            "Schnellüberblick über das Archiv. \n"
            "Erklärung: SQLite = leichte Datenbank, Eintrag = gespeicherter Datensatz."
        ),
        wraplength=260,
        justify="left",
        font=body_font,
    ).pack(anchor="w", pady=(2, 8))

    safe_stats: Dict[str, object] = stats or {}
    total_entries = int(safe_stats.get("total_entries", 0) or 0)
    last_added: Optional[Dict[str, str]] = None
    raw_last = safe_stats.get("last_added")
    if isinstance(raw_last, dict):
        last_added = {
            "title": str(raw_last.get("title", "")),
            "created_at": str(raw_last.get("created_at", "")),
        }

    summary_lines: List[str] = [f"Gesamt: {total_entries} Einträge (Datensätze)"]
    if last_added:
        summary_lines.append(
            f"Letzter Eintrag: {last_added['title']} – gespeichert am {last_added['created_at']}"
        )
    else:
        summary_lines.append("Noch keine Einträge vorhanden. Über das Datenbank-Modul ergänzen.")

    ttk.Label(
        parent,
        text="\n".join(summary_lines),
        font=body_font,
        wraplength=260,
        justify="left",
    ).pack(anchor="w", pady=(0, 8))

    latest_entries: List[Dict[str, str]] = []
    raw_latest = safe_stats.get("latest_entries")
    if isinstance(raw_latest, list):
        latest_entries = [
            {
                "title": str(item.get("title", "")),
                "created_at": str(item.get("created_at", "")),
            }
            for item in raw_latest[:5]
            if isinstance(item, dict)
        ]

    initials: List[Dict[str, object]] = []
    raw_initials = safe_stats.get("top_initials")
    if isinstance(raw_initials, list):
        initials = [
            {
                "initial": str(item.get("initial", "?")),
                "count": int(item.get("count", 0) or 0),
            }
            for item in raw_initials[:5]
            if isinstance(item, dict)
        ]

    if latest_entries:
        ttk.Label(parent, text="Neueste Einträge", font=bold_font).pack(anchor="w")
        tree = ttk.Treeview(
            parent,
            columns=("title", "created"),
            show="headings",
            height=min(5, len(latest_entries)),
        )
        if colors:
            tree.configure(
                background=colors.get("surface", "white"),
                foreground=colors.get("on_surface", "black"),
                fieldbackground=colors.get("surface", "white"),
            )
        tree.heading("title", text="Titel")
        tree.heading("created", text="Gespeichert am")
        tree.column("title", width=160, anchor="w")
        tree.column("created", width=120, anchor="w")
        for entry in latest_entries:
            tree.insert("", "end", values=(entry["title"], entry["created_at"]))
        tree.configure(font=body_font)
        tree.pack(fill="x", pady=(4, 8))
        parent._db_latest_tree = tree  # type: ignore[attr-defined]
    else:
        ttk.Label(
            parent,
            text="Noch keine Liste der neuesten Einträge – zuerst Datensätze speichern.",
            font=body_font,
            wraplength=260,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

    if initials:
        ttk.Label(parent, text="Häufigste Anfangsbuchstaben", font=bold_font).pack(anchor="w")
        info_lines = [f"{item['initial']}: {item['count']}×" for item in initials]
        ttk.Label(
            parent,
            text=", ".join(info_lines),
            font=mono_font,
            wraplength=260,
        ).pack(anchor="w", pady=(4, 0))
    else:
        ttk.Label(
            parent,
            text="Noch keine Statistik zu Anfangsbuchstaben.",
            font=body_font,
        ).pack(anchor="w")


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

    evaluate_contrast()


def build_palette_panel(parent: ttk.LabelFrame, colors: Dict[str, str]) -> None:
    """Display the active color palette including contrast ratios."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")

    ttk.Label(parent, text="Aktive Farbpalette", font=heading_font).pack(anchor="w")
    ttk.Label(
        parent,
        text=(
            "Die Tabelle zeigt die wichtigsten Farbkombinationen des aktuellen Schemas "
            "inklusive berechnetem Kontrastwert (WCAG-Richtlinie)."
        ),
        wraplength=320,
        font=body_font,
        justify="left",
    ).pack(anchor="w", pady=(2, 6))

    tree = ttk.Treeview(parent, columns=("element", "farbe", "kontrast"), show="headings", height=6)
    tree.heading("element", text="Element")
    tree.heading("farbe", text="Hex-Wert")
    tree.heading("kontrast", text="Kontrast")
    tree.column("element", width=140, anchor="w")
    tree.column("farbe", width=110, anchor="w")
    tree.column("kontrast", width=110, anchor="w")
    tree.configure(font=body_font)
    tree.pack(fill="both", expand=True)

    def contrast(fg: str, bg: str) -> float:
        rgb_fg = _hex_to_rgb(fg)
        rgb_bg = _hex_to_rgb(bg)
        lum_fg = _relative_luminance(rgb_fg)
        lum_bg = _relative_luminance(rgb_bg)
        lighter = max(lum_fg, lum_bg)
        darker = min(lum_fg, lum_bg)
        return (lighter + 0.05) / (darker + 0.05)

    entries = (
        ("Hintergrund", colors.get("on_background", "#FFFFFF"), colors.get("background", "#000000")),
        ("Flächen", colors.get("on_surface", "#FFFFFF"), colors.get("surface", "#000000")),
        ("Aktion", colors.get("surface", "#000000"), colors.get("accent", "#FFFFFF")),
        ("Warnung", colors.get("background", "#000000"), colors.get("warning", "#FFD43B")),
        ("Erfolg", colors.get("background", "#000000"), colors.get("success", "#4CC38A")),
    )

    for label, fg, bg in entries:
        ratio = contrast(fg, bg)
        tree.insert(
            "",
            "end",
            values=(label, f"FG {fg} / BG {bg}", f"{ratio:.2f}:1"),
            tags=("ok" if ratio >= 4.5 else "warn",),
        )

    tree.tag_configure("ok", foreground="#2e8540")
    tree.tag_configure("warn", foreground="#c43c00")


def build_color_audit_panel(
    parent: ttk.LabelFrame,
    audit: Optional[Dict[str, object]],
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Show summary of the automated color contrast audit."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Farbaudit", font=heading_font).pack(anchor="w")

    if not audit:
        ttk.Label(
            parent,
            text=(
                "Noch keine Auswertung vorhanden – Startroutine (start_tool.py) ausführen,"
                " um den Farbaudit zu erstellen."
            ),
            wraplength=320,
            font=body_font,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
        return

    status = str(audit.get("overall_status", "unknown"))
    worst_ratio = float(audit.get("worst_ratio", 0.0))
    generated = audit.get("generated_at", "")
    summary_text = (
        "Ergebnis: Alle Mindestkontraste erfüllt"
        if status == "ok"
        else f"Ergebnis: Hinweise gefunden – niedrigster Kontrast {worst_ratio:.2f}:1"
    )
    ttk.Label(
        parent,
        text=f"{summary_text}\nStand: {generated}",
        font=body_font,
        justify="left",
    ).pack(anchor="w", pady=(2, 6))

    tree = ttk.Treeview(parent, columns=("schema", "kontrast", "status"), show="headings", height=5)
    tree.heading("schema", text="Schema")
    tree.heading("kontrast", text="Niedrigster Kontrast")
    tree.heading("status", text="Bewertung")
    tree.column("schema", width=120, anchor="w")
    tree.column("kontrast", width=120, anchor="w")
    tree.column("status", width=120, anchor="w")
    if colors:
        tree.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            fieldbackground=colors.get("surface", "white"),
        )
    tree.configure(font=body_font)
    tree.pack(fill="both", expand=True)

    for theme in audit.get("themes", []) or []:
        name = theme.get("name", "")
        ratio = float(theme.get("worst_ratio", 0.0))
        status_text = "OK" if theme.get("status") == "ok" else "Bitte prüfen"
        tag = "ok" if theme.get("status") == "ok" else "warn"
        tree.insert(
            "",
            "end",
            values=(name, f"{ratio:.2f}:1", status_text),
            tags=(tag,),
        )

    tree.tag_configure("ok", foreground="#2e8540")
    tree.tag_configure("warn", foreground="#c43c00")

    issues = audit.get("issues", []) or []
    if issues:
        ttk.Label(parent, text="Hinweise", font=heading_font).pack(anchor="w", pady=(6, 0))
        issue_tree = ttk.Treeview(parent, columns=("hinweis",), show="headings", height=4)
        issue_tree.heading("hinweis", text="Beschreibung")
        issue_tree.column("hinweis", width=320, anchor="w")
        if colors:
            issue_tree.configure(
                background=colors.get("surface", "white"),
                foreground=colors.get("on_surface", "black"),
                fieldbackground=colors.get("surface", "white"),
            )
        issue_tree.configure(font=body_font)
        issue_tree.pack(fill="both", expand=True)
        for issue in issues:
            issue_tree.insert("", "end", values=(issue,), tags=("warn",))
        issue_tree.tag_configure("warn", foreground="#c43c00")

    recommendations = audit.get("recommendations", []) or []
    if recommendations:
        ttk.Label(parent, text="Empfehlungen", font=heading_font).pack(anchor="w", pady=(6, 0))
        tip_tree = ttk.Treeview(parent, columns=("tipp",), show="headings", height=4)
        tip_tree.heading("tipp", text="Kontrast verbessern")
        tip_tree.column("tipp", width=320, anchor="w")
        if colors:
            tip_tree.configure(
                background=colors.get("surface", "white"),
                foreground=colors.get("on_surface", "black"),
                fieldbackground=colors.get("surface", "white"),
            )
        tip_tree.configure(font=body_font)
        tip_tree.pack(fill="both", expand=True)
        for recommendation in recommendations:
            tip_tree.insert("", "end", values=(recommendation,), tags=("tip",))
        tip_tree.tag_configure("tip", foreground="#2e8540")

    ttk.Label(
        parent,
        text=(
            "Tipp: Die Ergebnisse stehen auch in data/color_audit.json."
            " Für eigene Paletten zuerst im Header ein Farbschema wählen."
        ),
        wraplength=320,
        justify="left",
        font=body_font,
    ).pack(anchor="w", pady=(6, 0))

    ttk.Label(
        parent,
        text="Tipp: Im Header kann zwischen High Contrast, Accessible und Dunkel/Hell gewechselt werden.",
        wraplength=320,
        font=body_font,
        justify="left",
    ).pack(anchor="w", pady=(8, 0))


def build_security_panel(
    parent: ttk.LabelFrame,
    summary: Optional[Dict[str, object]],
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Display the latest security manifest summary."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Datensicherheit", font=heading_font).pack(anchor="w")

    if not summary:
        ttk.Label(
            parent,
            text="Noch keine Sicherheitsprüfung vorhanden – Startroutine ausführen (start_tool.py).",
            wraplength=320,
            font=body_font,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
        return

    status = str(summary.get("status", "unknown"))
    verified = int(summary.get("verified", 0))
    issues = summary.get("issues", [])
    size_alerts = summary.get("size_alerts", []) or []
    backups = summary.get("backups", [])
    pruned = summary.get("pruned_backups", []) or []
    timestamp = summary.get("timestamp", "")
    restore_points = summary.get("restore_points", []) or []
    restore_issues = summary.get("restore_issues", []) or []

    message = (
        f"Status: {'Keine Auffälligkeiten' if status == 'ok' else 'Achtung – Details prüfen'}\n"
        f"Geprüfte Dateien: {verified}\n"
        f"Letzte Prüfung: {timestamp}\n"
        f"Restore-Checks: {len(restore_points)} getestet, {len(restore_issues)} Hinweise"
    )
    ttk.Label(parent, text=message, justify="left", font=body_font).pack(anchor="w", pady=(4, 6))

    tree = ttk.Treeview(parent, columns=("typ", "beschreibung"), show="headings", height=5)
    tree.heading("typ", text="Typ")
    tree.heading("beschreibung", text="Beschreibung")
    tree.column("typ", width=90, anchor="w")
    tree.column("beschreibung", width=220, anchor="w")
    tree.configure(font=body_font)
    tree.pack(fill="both", expand=True)

    known_size_alerts = set(size_alerts)
    for entry in issues:
        if entry in known_size_alerts:
            continue
        tree.insert("", "end", values=("Warnung", entry), tags=("warn",))
    for entry in size_alerts:
        tree.insert("", "end", values=("Größe", entry), tags=("warn",))
    for backup in backups:
        tree.insert("", "end", values=("Backup", backup))
    for cleanup in pruned:
        tree.insert("", "end", values=("Bereinigt", cleanup))
    for restore in restore_points:
        status_text = restore.get("status")
        file_label = restore.get("file", "")
        description = restore.get("message") or restore.get("backup") or "Kein Backup"
        tag = "ok" if status_text == "ok" else "warn"
        title = "Restore OK" if status_text == "ok" else "Restore"
        tree.insert(
            "",
            "end",
            values=(title, f"{file_label}: {description}"),
            tags=(tag,),
        )

    tree.tag_configure("ok", foreground="#2e8540")
    tree.tag_configure("warn", foreground="#c43c00")

    ttk.Label(
        parent,
        text=(
            "Hinweis: Manifest und Backups liegen unter data/security_manifest.json bzw. data/backups/."
            " Restore-Test: Letzte Sicherung kann über Kopieren der *.bak-Datei wiederhergestellt werden."
        ),
        wraplength=320,
        font=body_font,
        justify="left",
    ).pack(anchor="w", pady=(8, 0))


def build_diagnostics_panel(
    parent: ttk.LabelFrame,
    diagnostics: Optional[Dict[str, object]],
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Render a structured system diagnostics overview."""

    heading_font = tkfont.nametofont("TkHeadingFont")
    body_font = tkfont.nametofont("TkDefaultFont")
    ttk.Label(parent, text="Systemdiagnose", font=heading_font).pack(anchor="w")

    if not diagnostics:
        ttk.Label(
            parent,
            text="Noch keine Diagnose gespeichert – Startskript ausführen (start_tool.py).",
            wraplength=320,
            justify="left",
            font=body_font,
        ).pack(anchor="w", pady=(4, 0))
        return

    summary = diagnostics.get("summary", {}) or {}
    generated = diagnostics.get("generated_at", "")
    issues = summary.get("issues", []) or []
    recommendations = summary.get("recommendations", []) or []
    status_label = "Alles in Ordnung" if summary.get("status") == "ok" else "Hinweise prüfen"
    overview = (
        f"Stand: {generated}\nStatus: {status_label}\n"
        f"Hinweise: {len(issues)} – Empfehlungen: {len(recommendations)}"
    )
    ttk.Label(parent, text=overview, justify="left", font=body_font).pack(anchor="w", pady=(4, 6))

    python_info = diagnostics.get("python", {})
    runtime_text = (
        f"Python {python_info.get('version', '?')} "
        f"({python_info.get('implementation', 'Unbekannt')}) – "
        f"Pfad: {python_info.get('executable', 'n/a')}"
    )
    ttk.Label(parent, text=runtime_text, wraplength=320, justify="left", font=body_font).pack(anchor="w")

    virtualenv = diagnostics.get("virtualenv", {})
    venv_state = "aktiv" if virtualenv.get("active") else "nicht aktiv"
    venv_text = (
        f"Virtuelle Umgebung: {venv_state} – erwartet: {virtualenv.get('expected_path', '')}"
    )
    ttk.Label(parent, text=venv_text, wraplength=320, justify="left", font=body_font).pack(
        anchor="w", pady=(2, 6)
    )

    path_tree = ttk.Treeview(
        parent,
        columns=("pfad", "vorhanden", "schreibbar"),
        show="headings",
        height=4,
    )
    path_tree.heading("pfad", text="Pfad")
    path_tree.heading("vorhanden", text="Vorhanden")
    path_tree.heading("schreibbar", text="Schreibbar")
    path_tree.column("pfad", width=200, anchor="w")
    path_tree.column("vorhanden", width=80, anchor="center")
    path_tree.column("schreibbar", width=80, anchor="center")
    if colors:
        path_tree.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            fieldbackground=colors.get("surface", "white"),
        )
    path_tree.configure(font=body_font)
    path_tree.pack(fill="both", expand=True, pady=(0, 6))
    for entry in diagnostics.get("paths", []):
        exists = "Ja" if entry.get("exists") else "Nein"
        writable = "Ja" if entry.get("writable") else "Nein"
        tag = "warn" if not entry.get("writable") else "ok"
        path_tree.insert(
            "",
            "end",
            values=(entry.get("path", ""), exists, writable),
            tags=(tag,),
        )
    path_tree.tag_configure("warn", foreground="#c43c00")
    path_tree.tag_configure("ok", foreground="#2e8540")

    package_tree = ttk.Treeview(
        parent,
        columns=("paket", "status", "vorgabe", "info"),
        show="headings",
        height=4,
    )
    package_tree.heading("paket", text="Paket")
    package_tree.heading("status", text="Status")
    package_tree.heading("vorgabe", text="Vorgabe")
    package_tree.heading("info", text="Info")
    package_tree.column("paket", width=140, anchor="w")
    package_tree.column("status", width=100, anchor="center")
    package_tree.column("vorgabe", width=120, anchor="w")
    package_tree.column("info", width=200, anchor="w")
    if colors:
        package_tree.configure(
            background=colors.get("surface", "white"),
            foreground=colors.get("on_surface", "black"),
            fieldbackground=colors.get("surface", "white"),
        )
    package_tree.configure(font=body_font)
    package_tree.pack(fill="both", expand=True, pady=(0, 6))
    for pkg in diagnostics.get("packages", []):
        installed_flag = bool(pkg.get("installed"))
        meets_flag = bool(pkg.get("meets_requirement", True))
        installed = "Installiert" if installed_flag else "Fehlt"
        required = pkg.get("required") or "–"
        version = pkg.get("version") or ""
        info_text = version
        message = pkg.get("message") or ""
        if message:
            info_text = f"{info_text} – {message}" if info_text else message
        tag = "ok" if installed_flag and meets_flag else "warn"
        package_tree.insert(
            "",
            "end",
            values=(pkg.get("name", ""), installed, required, info_text),
            tags=(tag,),
        )
    package_tree.tag_configure("warn", foreground="#c43c00")
    package_tree.tag_configure("ok", foreground="#2e8540")

    if issues:
        ttk.Label(parent, text="Hinweise", font=heading_font).pack(anchor="w", pady=(4, 0))
        issue_list = tk.Listbox(parent, height=min(len(issues), 5))
        if colors:
            issue_list.configure(
                background=colors.get("surface", "white"),
                foreground=colors.get("on_surface", "black"),
                highlightbackground=colors.get("background", "#000000"),
                highlightcolor=colors.get("accent", "#0000ff"),
            )
        issue_list.configure(font=body_font)
        for issue in issues:
            issue_list.insert(tk.END, issue)
        issue_list.pack(fill="both", expand=True, pady=(0, 6))

    if recommendations:
        ttk.Label(parent, text="Empfehlungen", font=heading_font).pack(anchor="w", pady=(4, 0))
        recommendations_text = "\n".join(f"• {item}" for item in recommendations)
        ttk.Label(
            parent,
            text=recommendations_text,
            wraplength=320,
            justify="left",
            font=body_font,
        ).pack(anchor="w", pady=(0, 6))

    ttk.Label(
        parent,
        text=(
            "Tipp: Der vollständige Bericht liegt unter data/diagnostics_report.json."
            " Dort stehen alle Details für Support (Unterstützung) und Fehlersuche."
        ),
        wraplength=320,
        justify="left",
        font=body_font,
    ).pack(anchor="w", pady=(4, 0))
    html_path = diagnostics.get("html_report_path") if isinstance(diagnostics, dict) else None
    if html_path:
        ttk.Label(
            parent,
            text=(
                "Neu: Eine barrierefreundliche HTML-Ansicht liegt zusätzlich unter "
                f"{html_path}."
            ),
            wraplength=320,
            justify="left",
            font=body_font,
        ).pack(anchor="w", pady=(0, 0))


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
    "build_color_audit_panel",
    "build_palette_panel",
    "build_mockup_panel",
    "build_structure_panel",
    "build_quicklinks_panel",
    "build_release_panel",
    "build_security_panel",
    "build_diagnostics_panel",
]
