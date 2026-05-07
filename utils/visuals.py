"""
utils/visuals.py — NeoPept Pro
Fonctions générant les graphiques Plotly pour le Dashboard.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Palette de couleurs cohérente avec le thème NeoPept
_COLOR_PRIMARY = "#4f8bf9"
_COLOR_SECONDARY = "#2563eb"
_COLOR_DANGER = "#ef4444"
_COLOR_SUCCESS = "#22c55e"


def plot_aa_composition(aa_count: Dict[str, int]) -> go.Figure:
    """Génère un graphique en barres de la composition en acides aminés.

    Args:
        aa_count: Dictionnaire ``{acide_aminé: nombre}`` retourné par
                  ``ProteinAnalysis.count_amino_acids()``.

    Returns:
        Un objet ``plotly.graph_objects.Figure`` prêt à être affiché
        avec ``st.plotly_chart()``.
    """
    df = (
        pd.DataFrame(list(aa_count.items()), columns=["Acide Aminé", "Quantité"])
        .sort_values("Quantité", ascending=False)
    )

    fig = px.bar(
        df,
        x="Acide Aminé",
        y="Quantité",
        color="Quantité",
        color_continuous_scale=[[0, "#dbeafe"], [1, _COLOR_SECONDARY]],
        text="Quantité",
        title="Composition en Acides Aminés",
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_title="Acide Aminé",
        yaxis_title="Occurrences",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=13),
        margin=dict(t=50, b=20, l=20, r=20),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig


def plot_hydrophobicity(
    scores: List[float],
    window_size: int = 9,
) -> go.Figure:
    """Génère un graphique linéaire du profil d'hydrophobicité Kyte-Doolittle.

    Les régions au-dessus de 0 sont colorées en orange (hydrophobes),
    celles en dessous en bleu (hydrophiles).

    Args:
        scores: Liste de scores retournée par ``calculate_hydrophobicity()``.
        window_size: Taille de fenêtre utilisée, affichée dans le titre.

    Returns:
        Un objet ``plotly.graph_objects.Figure`` prêt à être affiché.
    """
    positions = list(range(1, len(scores) + 1))

    fig = go.Figure()

    # Zone hydrophobe (au-dessus de 0)
    fig.add_trace(
        go.Scatter(
            x=positions,
            y=[s if s > 0 else 0 for s in scores],
            fill="tozeroy",
            fillcolor="rgba(239, 68, 68, 0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Hydrophobe",
            hoverinfo="skip",
        )
    )

    # Zone hydrophile (en dessous de 0)
    fig.add_trace(
        go.Scatter(
            x=positions,
            y=[s if s < 0 else 0 for s in scores],
            fill="tozeroy",
            fillcolor="rgba(79, 139, 249, 0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Hydrophile",
            hoverinfo="skip",
        )
    )

    # Courbe principale
    fig.add_trace(
        go.Scatter(
            x=positions,
            y=scores,
            mode="lines+markers",
            line=dict(color=_COLOR_PRIMARY, width=2.5),
            marker=dict(size=5, color=_COLOR_PRIMARY),
            name="Score KD",
            hovertemplate="Position %{x}<br>Score : %{y:.3f}<extra></extra>",
        )
    )

    # Ligne de référence à 0
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=_COLOR_DANGER,
        line_width=1.5,
        annotation_text="0 (limite hydrophobe/hydrophile)",
        annotation_position="top right",
        annotation_font_color=_COLOR_DANGER,
    )

    fig.update_layout(
        title=f"Profil d'Hydrophobicité Kyte-Doolittle (fenêtre = {window_size})",
        xaxis_title="Position de la fenêtre",
        yaxis_title="Score KD moyen",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=13),
        legend=dict(orientation="h", y=1.1, x=0),
        margin=dict(t=60, b=20, l=20, r=20),
        showlegend=True,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", zeroline=False)
    return fig


def plot_mutation_comparison(comparison: dict) -> go.Figure:
    """Génère un graphique en barres groupées comparant original vs. mutant.

    Args:
        comparison: Dictionnaire retourné par ``compare_profiles()``,
                    de la forme ``{metric: {original, mutant, delta}}``.

    Returns:
        Un objet ``plotly.graph_objects.Figure`` prêt à être affiché.
    """
    metrics = list(comparison.keys())
    originals = [comparison[m]["original"] for m in metrics]
    mutants = [comparison[m]["mutant"] for m in metrics]

    fig = go.Figure(
        data=[
            go.Bar(
                name="Séquence originale",
                x=metrics,
                y=originals,
                marker_color=_COLOR_PRIMARY,
                text=[f"{v:.2f}" for v in originals],
                textposition="auto",
            ),
            go.Bar(
                name="Séquence mutante",
                x=metrics,
                y=mutants,
                marker_color=_COLOR_DANGER,
                text=[f"{v:.2f}" for v in mutants],
                textposition="auto",
            ),
        ]
    )
    fig.update_layout(
        barmode="group",
        title="Comparaison Original vs. Mutant",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=60, b=20, l=20, r=20),
        xaxis=dict(tickangle=-15),
    )
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    return fig


def plot_secondary_structure(
    fraction_helix: float,
    fraction_turn: float,
    fraction_sheet: float,
) -> go.Figure:
    """Génère un graphique en secteurs de la composition en structure secondaire.

    Args:
        fraction_helix: Fraction d'hélices alpha (0–1).
        fraction_turn:  Fraction de coudes / turns (0–1).
        fraction_sheet: Fraction de feuillets bêta (0–1).

    Returns:
        Un objet ``plotly.graph_objects.Figure`` prêt à être affiché.
    """
    labels = ["Hélices Alpha 🌀", "Coudes (Turns) ↪️", "Feuillets Bêta 〰️"]
    values = [fraction_helix * 100, fraction_turn * 100, fraction_sheet * 100]
    colors = [_COLOR_PRIMARY, _COLOR_SUCCESS, "#f59e0b"]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            textinfo="label+percent",
            hovertemplate="%{label}<br>%{value:.1f} %<extra></extra>",
            hole=0.45,
        )
    )
    fig.update_layout(
        title="Structure Secondaire Prédite",
        showlegend=False,
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=13),
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig
