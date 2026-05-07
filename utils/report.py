"""
utils/report.py — NeoPept Pro
Génération de rapports PDF qualité publication avec ReportLab.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from utils.biophysics import BiophysicsProfile, ScientificAlert

# Couleurs NeoPept
_BLUE      = colors.HexColor("#4f8bf9")
_DARK      = colors.HexColor("#0f1117")
_LIGHT_BG  = colors.HexColor("#f8f9fa")
_ORANGE    = colors.HexColor("#f59e0b")
_RED       = colors.HexColor("#ef4444")
_GREEN     = colors.HexColor("#22c55e")
_GREY_TEXT = colors.HexColor("#6c757d")


def _build_styles() -> dict:
    """Construit le dictionnaire de styles ReportLab pour le rapport."""
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "NeoTitle",
            parent=base["Title"],
            fontSize=26,
            textColor=_DARK,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "NeoSubtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=_GREY_TEXT,
            spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "NeoH2",
            parent=base["Heading2"],
            fontSize=13,
            textColor=_BLUE,
            spaceBefore=14,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "NeoBody",
            parent=base["Normal"],
            fontSize=10,
            textColor=_DARK,
            spaceAfter=6,
            leading=15,
        ),
        "code": ParagraphStyle(
            "NeoCode",
            parent=base["Code"],
            fontSize=9,
            textColor=colors.HexColor("#2563eb"),
            backColor=colors.HexColor("#eff6ff"),
            borderPadding=(4, 6, 4, 6),
            spaceAfter=10,
        ),
        "caption": ParagraphStyle(
            "NeoCaption",
            parent=base["Normal"],
            fontSize=8,
            textColor=_GREY_TEXT,
            spaceAfter=4,
        ),
    }
    return styles


def _table_style_metrics() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND",  (0, 0), (-1, 0), _BLUE),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0), 10),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT_BG, colors.white]),
            ("FONTSIZE",    (0, 1), (-1, -1), 9),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("TOPPADDING",  (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", [4]),
        ]
    )


def generate_pdf_report(
    profile: BiophysicsProfile,
    protein_name: str,
    alerts: Optional[List[ScientificAlert]] = None,
    mutation_desc: Optional[str] = None,
) -> bytes:
    """Génère un rapport PDF qualité publication pour une analyse de protéine.

    Le rapport contient : en-tête NeoPept Pro, informations du projet,
    séquence analysée, tableau des paramètres physico-chimiques, structure
    secondaire, alertes de formulation (si présentes) et une section mutation
    optionnelle.

    Args:
        profile: Profil biophysique calculé par ``analyse_sequence()``.
        protein_name: Nom du projet / de la protéine.
        alerts: Liste d'alertes ``ScientificAlert`` à inclure dans le rapport.
                Passer ``None`` ou liste vide pour omettre la section.
        mutation_desc: Description de la mutation appliquée (ex: ``"A5W"``),
                       ou ``None`` si pas de mutation.

    Returns:
        Contenu du fichier PDF sous forme de ``bytes``, prêt pour
        ``st.download_button()``.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"NeoPept Pro — {protein_name}",
        author="NeoPept Pro v3.0",
    )

    S = _build_styles()
    story = []

    # ── En-tête ──────────────────────────────────────────────────────────────
    story.append(Paragraph("🧬 NeoPept <b>Pro</b>", S["title"]))
    story.append(Paragraph("Rapport d'Analyse Biophysique — Qualité Publication", S["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=_BLUE, spaceAfter=12))

    # ── Informations du projet ────────────────────────────────────────────────
    story.append(Paragraph("Informations du Projet", S["h2"]))
    meta_data = [
        ["Champ", "Valeur"],
        ["Nom de la protéine / projet", protein_name],
        ["Date d'analyse", datetime.now().strftime("%d %B %Y à %H:%M")],
        ["Longueur de la séquence", f"{len(profile.sequence)} acides aminés"],
        ["Outil de génération", "NeoPept Pro v3.0 — ESMFold (Meta AI)"],
    ]
    if mutation_desc:
        meta_data.append(["Mutation appliquée", mutation_desc])

    meta_table = Table(meta_data, colWidths=[6 * cm, 11 * cm])
    meta_table.setStyle(_table_style_metrics())
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ── Séquence ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Séquence Analysée", S["h2"]))
    seq_chunks = [
        profile.sequence[i : i + 10] for i in range(0, len(profile.sequence), 10)
    ]
    seq_display = "  ".join(
        f"{(i // 10) * 10 + 1:>4}  {chunk}"
        for i, chunk in enumerate(seq_chunks)
    )
    story.append(Paragraph(profile.sequence, S["code"]))
    story.append(
        Paragraph(
            f"La séquence contient <b>{len(profile.sequence)}</b> acides aminés (notation IUPAC standard).",
            S["caption"],
        )
    )
    story.append(Spacer(1, 6))

    # ── Paramètres Physico-Chimiques ─────────────────────────────────────────
    story.append(Paragraph("Paramètres Physico-Chimiques", S["h2"]))
    params_data = [
        ["Paramètre", "Valeur", "Interprétation"],
        [
            "Poids Moléculaire",
            f"{profile.poids_moleculaire:.2f} Da",
            "Masse de la chaîne polypeptidique",
        ],
        [
            "Point Isoélectrique (pI)",
            f"{profile.pi_score:.2f}",
            "pH de charge nette nulle",
        ],
        [
            "Aromaticité",
            f"{profile.aromaticite * 100:.1f} %",
            "Fraction de Phe, Trp, Tyr",
        ],
        [
            "Indice d'Instabilité",
            f"{profile.instabilite:.1f}",
            "< 40 = Stable  |  ≥ 40 = Instable",
        ],
        [
            "Hélices Alpha (pred.)",
            f"{profile.fraction_helix * 100:.1f} %",
            "Structure secondaire prédite",
        ],
        [
            "Feuillets Bêta (pred.)",
            f"{profile.fraction_sheet * 100:.1f} %",
            "Structure secondaire prédite",
        ],
        [
            "Coudes / Turns (pred.)",
            f"{profile.fraction_turn * 100:.1f} %",
            "Structure secondaire prédite",
        ],
    ]
    params_table = Table(params_data, colWidths=[5.5 * cm, 3.5 * cm, 8 * cm])
    params_table.setStyle(_table_style_metrics())
    story.append(params_table)
    story.append(Spacer(1, 10))

    # ── Alertes de Formulation ────────────────────────────────────────────────
    if alerts:
        story.append(Paragraph("Alertes de Formulation", S["h2"]))
        for alert in alerts:
            level_color = _RED if alert.level == "error" else _ORANGE
            story.append(
                Paragraph(
                    f"<b>{alert.icon} [{alert.category.upper()}]</b> {alert.message}",
                    ParagraphStyle(
                        "AlertMsg",
                        parent=S["body"],
                        textColor=level_color,
                        fontName="Helvetica-Bold",
                    ),
                )
            )
            story.append(
                Paragraph(
                    f"<i>Recommandation :</i> {alert.recommendation}",
                    S["body"],
                )
            )
            story.append(Spacer(1, 4))

    # ── Section Structures (espace pour images) ───────────────────────────────
    story.append(Paragraph("Structure 3D (ESMFold)", S["h2"]))
    story.append(
        Paragraph(
            "La structure tridimensionnelle prédite par ESMFold (Meta AI) est disponible "
            "en téléchargement au format .PDB depuis le Dashboard NeoPept Pro. "
            "Importez le fichier dans PyMOL, UCSF ChimeraX ou VMD pour la visualisation "
            "et l'analyse de la conformation.",
            S["body"],
        )
    )
    story.append(Spacer(1, 6))

    # ── Composition en acides aminés ─────────────────────────────────────────
    story.append(Paragraph("Composition en Acides Aminés", S["h2"]))
    sorted_aa = sorted(profile.aa_count.items(), key=lambda x: -x[1])
    aa_present = [(aa, cnt) for aa, cnt in sorted_aa if cnt > 0]

    if aa_present:
        aa_rows = [["AA", "N", "%"]] + [
            [aa, str(cnt), f"{cnt / len(profile.sequence) * 100:.1f}%"]
            for aa, cnt in aa_present
        ]
        col_count = 3
        max_rows = (len(aa_rows) + col_count - 1) // col_count
        # Affichage en 3 colonnes côte à côte
        left   = aa_rows[:max_rows]
        middle = aa_rows[max_rows : 2 * max_rows]
        right  = aa_rows[2 * max_rows :]

        # Padding pour égaliser les colonnes
        while len(middle) < len(left):
            middle.append(["", "", ""])
        while len(right) < len(left):
            right.append(["", "", ""])

        combined = [l + m + r for l, m, r in zip(left, middle, right)]
        aa_table = Table(combined, colWidths=[1.2 * cm, 0.8 * cm, 1.0 * cm] * 3)
        aa_table.setStyle(_table_style_metrics())
        story.append(aa_table)

    # ── Pied de page ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=_GREY_TEXT))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f"Généré par <b>NeoPept Pro v3.0</b> · {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
            "Propulsé par ESMFold (Meta AI) &amp; Biopython",
            S["caption"],
        )
    )
    story.append(
        Paragraph(
            "Ce rapport est destiné à un usage scientifique et de recherche. "
            "Les prédictions bioinformatiques ne remplacent pas la validation expérimentale.",
            S["caption"],
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
