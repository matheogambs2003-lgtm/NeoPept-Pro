"""
pages/4_batch_analysis.py — NeoPept Pro v3.0
Traitement par lot (Batch Screening) : upload FASTA / TXT,
analyse biophysique de toutes les séquences, export CSV.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.biophysics import analyse_sequence, get_alerts
from utils.ui import inject_css, sidebar_branding, sidebar_nav_links

# ---------------------------------------------------------------------------
# Page config & CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Batch Screening — NeoPept Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    sidebar_branding("Batch Screening · v3.0")
    st.markdown("---")
    st.markdown("**Format attendu**")
    st.markdown(
        """
        **FASTA (.fasta / .fa)** :
        ```
        >Glucagon
        HSQGTFTSDYSKYLDSRRAQDFVQWLMNT
        >GLP-1
        HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR
        ```
        **Texte (.txt)** — une séquence par ligne :
        ```
        HSQGTFTSDYSKYLDSRRAQDFVQWLMNT
        HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR
        ```
        """
    )
    sidebar_nav_links()

# ---------------------------------------------------------------------------
# Fonctions de parsing
# ---------------------------------------------------------------------------

def parse_fasta(content: str) -> List[Tuple[str, str]]:
    """Parse le contenu d'un fichier FASTA et retourne des paires (nom, séquence).

    Args:
        content: Contenu textuel du fichier FASTA.

    Returns:
        Liste de tuples ``(nom, sequence)`` en lettres majuscules.
        Les séquences multi-lignes sont concaténées.
    """
    sequences: List[Tuple[str, str]] = []
    current_name: str | None = None
    current_seq: List[str] = []

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith(">"):
            if current_name is not None and current_seq:
                sequences.append((current_name, "".join(current_seq).upper()))
            current_name = line[1:].split()[0] if len(line) > 1 else f"seq_{len(sequences) + 1}"
            current_seq = []
        else:
            current_seq.append(line.upper())

    if current_name is not None and current_seq:
        sequences.append((current_name, "".join(current_seq).upper()))

    return sequences


def parse_txt(content: str) -> List[Tuple[str, str]]:
    """Parse un fichier texte avec une séquence par ligne.

    Args:
        content: Contenu textuel du fichier TXT.

    Returns:
        Liste de tuples ``(nom_auto, sequence)``.
        Les lignes vides et les commentaires (#) sont ignorés.
    """
    sequences: List[Tuple[str, str]] = []
    for i, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sequences.append((f"Sequence_{i}", line.upper()))
    return sequences


VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def is_valid_seq(seq: str) -> bool:
    """Retourne True si la séquence ne contient que des AA IUPAC valides."""
    return bool(seq) and all(c in VALID_AA for c in seq)


# ---------------------------------------------------------------------------
# Titre principal
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='margin-bottom:.2rem;'>⚡ Batch Screening</h1>"
    "<p style='color:#6c757d;'>Analysez des dizaines de séquences en une seule opération.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Upload du fichier
# ---------------------------------------------------------------------------
col_upload, col_manual = st.columns([3, 2])

with col_upload:
    uploaded_file = st.file_uploader(
        "Uploadez un fichier de séquences",
        type=["fasta", "fa", "txt"],
        help="Formats supportés : FASTA (.fasta, .fa) et texte brut (.txt, une séquence par ligne).",
    )

with col_manual:
    st.markdown("**Ou saisissez directement**")
    manual_input = st.text_area(
        "Séquences (FASTA ou une par ligne)",
        placeholder=">Glucagon\nHSQGTFTSDYSKYLDSRRAQDFVQWLMNT\n>GLP-1\nHAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
        height=140,
        label_visibility="collapsed",
    )

kd_window = st.session_state.get("kd_window", 9)

run_batch = st.button("⚡ Lancer l'Analyse par Lot", type="primary")

# ---------------------------------------------------------------------------
# Parsing de l'input
# ---------------------------------------------------------------------------
sequences: List[Tuple[str, str]] = []
parse_error: str = ""

if run_batch:
    try:
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8", errors="replace")
            fname = uploaded_file.name.lower()
            if fname.endswith((".fasta", ".fa")):
                sequences = parse_fasta(content)
            else:
                sequences = parse_txt(content)
        elif manual_input.strip():
            content = manual_input.strip()
            if content.startswith(">"):
                sequences = parse_fasta(content)
            else:
                sequences = parse_txt(content)
        else:
            st.warning("⚠️ Uploadez un fichier ou saisissez des séquences dans le champ texte.")
            st.stop()
    except Exception as exc:
        parse_error = str(exc)

    if parse_error:
        st.error(
            f"❌ **Erreur de lecture du fichier** : {parse_error}\n\n"
            "Vérifiez que le fichier est bien encodé en UTF-8 et respecte le format FASTA ou TXT."
        )
        st.stop()

    if not sequences:
        st.warning("⚠️ Aucune séquence détectée dans le fichier. Vérifiez le format.")
        st.stop()

    st.info(f"🔍 **{len(sequences)} séquence(s) détectée(s)**. Analyse en cours…")

    # ── Analyse par lot avec barre de progression ─────────────────────────────
    results = []
    errors  = []

    progress_bar = st.progress(0, text="Initialisation…")
    status_text  = st.empty()

    for idx, (name, seq) in enumerate(sequences):
        pct = (idx + 1) / len(sequences)
        progress_bar.progress(pct, text=f"Analyse de {name} ({idx + 1}/{len(sequences)})…")
        status_text.caption(f"⚙️ Traitement : **{name}** · {len(seq)} AA")

        # Validation
        if not is_valid_seq(seq):
            invalid = sorted({c for c in seq if c not in VALID_AA})
            errors.append({
                "Nom": name,
                "Séquence (extrait)": seq[:20] + "…",
                "Erreur": f"Caractères invalides : {', '.join(invalid)}",
            })
            continue

        if len(seq) < 6:
            errors.append({"Nom": name, "Séquence (extrait)": seq, "Erreur": "Séquence trop courte (< 6 AA)"})
            continue

        # Calcul biophysique
        try:
            profile = analyse_sequence(seq, window_size=kd_window)
            alerts  = get_alerts(profile)

            results.append({
                "Nom":                  name,
                "Longueur (AA)":        len(seq),
                "Poids Moléculaire (Da)": round(profile.poids_moleculaire, 2),
                "pI":                   round(profile.pi_score, 3),
                "Aromaticité (%)":      round(profile.aromaticite * 100, 1),
                "Instabilité":          round(profile.instabilite, 1),
                "Stable?":              "✅ Stable" if profile.instabilite <= 40 else "⚠️ Instable",
                "Red Flags":            len(alerts),
                "Séquence":             seq,
            })
        except Exception as exc:
            errors.append({"Nom": name, "Séquence (extrait)": seq[:20] + "…", "Erreur": str(exc)})

    progress_bar.progress(1.0, text="Analyse terminée ✅")
    status_text.empty()

    # ── Stockage en session ────────────────────────────────────────────────────
    st.session_state["batch_results"] = results
    st.session_state["batch_errors"]  = errors

    st.toast(
        f"✅ {len(results)} séquence(s) analysée(s) avec succès"
        + (f" · {len(errors)} erreur(s)" if errors else ""),
        icon="⚡",
    )
    if results:
        st.balloons()

# ---------------------------------------------------------------------------
# Affichage des résultats (depuis la session)
# ---------------------------------------------------------------------------
results = st.session_state.get("batch_results", [])
errors  = st.session_state.get("batch_errors",  [])

if not results and not errors:
    st.info(
        "Uploadez un fichier FASTA ou saisissez des séquences, puis cliquez sur "
        "**⚡ Lancer l'Analyse par Lot**.",
        icon="📂",
    )
    with st.expander("📋 Exemple de fichier FASTA", expanded=False):
        st.code(
            ">Glucagon\nHSQGTFTSDYSKYLDSRRAQDFVQWLMNT\n"
            ">GLP-1\nHAEGTFTSDVSSYLEGQAAKEFIAWLVKGR\n"
            ">Angiotensine_II\nDRVYIHPF\n"
            ">Insuline_A\nGIVEQCCTSICSLYQLENYCN",
            language=None,
        )
    st.stop()

# ── Métriques résumé ──────────────────────────────────────────────────────────
df = pd.DataFrame(results)

st.markdown("---")
st.markdown("### 📊 Résultats du Batch Screening")

cm1, cm2, cm3, cm4 = st.columns(4)
cm1.metric("✅ Séquences analysées", len(results))
cm2.metric("❌ Erreurs / ignorées",  len(errors))
if len(results) > 0:
    cm3.metric("⚖️ Poids moyen (Da)",  f"{df['Poids Moléculaire (Da)'].mean():.1f}")
    cm4.metric("⚡ pI moyen",           f"{df['pI'].mean():.2f}")

# ── DataFrame interactif ──────────────────────────────────────────────────────
display_cols = [c for c in df.columns if c != "Séquence"]

search_batch = st.text_input("🔍 Filtrer par nom", placeholder="Ex: Glucagon")
if search_batch:
    df_display = df[df["Nom"].str.contains(search_batch, case=False, na=False)]
else:
    df_display = df

st.dataframe(
    df_display[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Poids Moléculaire (Da)": st.column_config.NumberColumn(format="%.2f Da"),
        "pI":                     st.column_config.NumberColumn(format="%.3f"),
        "Aromaticité (%)":        st.column_config.NumberColumn(format="%.1f %%"),
        "Instabilité":            st.column_config.NumberColumn(format="%.1f"),
        "Red Flags":              st.column_config.NumberColumn(
            "🚨 Red Flags", help="Nombre d'alertes de formulation détectées"
        ),
        "Stable?": st.column_config.TextColumn("Stabilité"),
    },
)
st.caption(f"{len(df_display)} séquence(s) affichée(s) sur {len(results)} analysée(s).")

# ── Erreurs ───────────────────────────────────────────────────────────────────
if errors:
    with st.expander(f"⚠️ {len(errors)} séquence(s) ignorée(s) / en erreur", expanded=False):
        st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True)

# ── Export CSV ────────────────────────────────────────────────────────────────
st.markdown("---")
col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    csv_summary = df[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export CSV — Résultats (sans séquences)",
        data=csv_summary,
        file_name=f"neopept_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_exp2:
    csv_full = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export CSV — Complet (avec séquences)",
        data=csv_full,
        file_name=f"neopept_batch_full_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ── Visualisation rapide ─────────────────────────────────────────────────────
if len(results) >= 2:
    st.markdown("---")
    st.markdown("### 📈 Visualisation Comparative")

    import plotly.express as px

    col_v1, col_v2 = st.columns(2)

    with col_v1:
        fig_pi = px.scatter(
            df,
            x="pI",
            y="Poids Moléculaire (Da)",
            color="Stable?",
            text="Nom",
            color_discrete_map={"✅ Stable": "#4f8bf9", "⚠️ Instable": "#ef4444"},
            title="pI vs Poids Moléculaire",
        )
        fig_pi.update_traces(textposition="top center", marker_size=10)
        fig_pi.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=11),
        )
        st.plotly_chart(fig_pi, use_container_width=True)

    with col_v2:
        fig_inst = px.bar(
            df.sort_values("Instabilité", ascending=False),
            x="Nom",
            y="Instabilité",
            color="Stable?",
            color_discrete_map={"✅ Stable": "#4f8bf9", "⚠️ Instable": "#ef4444"},
            title="Indice d'Instabilité par Séquence",
        )
        fig_inst.add_hline(
            y=40,
            line_dash="dash",
            line_color="#ef4444",
            annotation_text="Seuil d'instabilité (40)",
        )
        fig_inst.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=11),
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_inst, use_container_width=True)
