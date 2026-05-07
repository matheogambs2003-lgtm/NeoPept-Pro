"""
pages/2_history.py — NeoPept Pro
Historique des analyses de protéines enregistrées en base de données SQLite.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import delete_record, get_all_records
from utils.ui import inject_css, sidebar_branding, sidebar_nav_links

# ---------------------------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Historique — NeoPept Pro",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    sidebar_branding("Historique · v3.0")
    sidebar_nav_links()

# ---------------------------------------------------------------------------
# Contenu principal
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='margin-bottom:.2rem;'>📋 Historique des Analyses</h1>"
    "<p style='color:#6c757d;'>Retrouvez toutes vos analyses passées, rechargez-les dans le Dashboard ou supprimez-les.</p>",
    unsafe_allow_html=True,
)

# Chargement des enregistrements
records = get_all_records()

if not records:
    st.info(
        "📭 **Aucune analyse enregistrée pour l'instant.**\n\n"
        "Lancez votre première analyse depuis le Dashboard pour voir l'historique apparaître ici.",
        icon="🔬",
    )
    st.page_link("pages/1_dashboard.py", label="→ Aller au Dashboard")
    st.stop()

# ---------------------------------------------------------------------------
# Métriques de résumé
# ---------------------------------------------------------------------------
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("🔬 Analyses totales", len(records))
col_m2.metric("⚖️ Poids moyen (Da)",    f"{sum(r.poids_moleculaire for r in records) / len(records):.1f}")
col_m3.metric("⚡ pI moyen",            f"{sum(r.pi_score for r in records) / len(records):.2f}")
col_m4.metric(
    "📅 Dernière analyse",
    records[0].date_analyse.strftime("%d/%m/%Y") if records[0].date_analyse else "—",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Tableau interactif
# ---------------------------------------------------------------------------
st.markdown("### 📊 Tableau des Analyses")

df = pd.DataFrame(
    [
        {
            "ID": r.id,
            "Nom de la protéine": r.nom_proteine,
            "Séquence (extrait)": r.sequence[:25] + ("…" if len(r.sequence) > 25 else ""),
            "Longueur (AA)": len(r.sequence),
            "Poids (Da)": round(r.poids_moleculaire, 2),
            "pI": round(r.pi_score, 2),
            "Date d'analyse": r.date_analyse.strftime("%d/%m/%Y %H:%M") if r.date_analyse else "—",
            "_sequence_full": r.sequence,  # colonne cachée pour le rechargement
        }
        for r in records
    ]
)

# Colonnes affichées (sans la colonne cachée)
display_cols = [c for c in df.columns if not c.startswith("_")]

# Barre de recherche
search = st.text_input("🔍 Filtrer par nom", placeholder="Ex: Glucagon")
if search:
    df = df[df["Nom de la protéine"].str.contains(search, case=False, na=False)]

st.dataframe(
    df[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "ID": st.column_config.NumberColumn(width="small"),
        "Poids (Da)": st.column_config.NumberColumn(format="%.2f Da"),
        "pI": st.column_config.NumberColumn(format="%.2f"),
        "Longueur (AA)": st.column_config.NumberColumn(width="small"),
    },
)

st.caption(f"{len(df)} enregistrement(s) affiché(s) sur {len(records)} au total.")

# ---------------------------------------------------------------------------
# Actions sur un enregistrement sélectionné
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🎯 Actions sur un enregistrement")

col_sel, col_act = st.columns([2, 3])

with col_sel:
    record_ids = df["ID"].tolist()
    selected_id = st.selectbox(
        "Sélectionner un enregistrement (par ID)",
        options=record_ids,
        format_func=lambda x: f"#{x} — {df.loc[df['ID'] == x, 'Nom de la protéine'].values[0]}",
    )

selected_row = df[df["ID"] == selected_id].iloc[0] if selected_id else None

with col_act:
    if selected_row is not None:
        st.markdown(f"**Protéine sélectionnée :** {selected_row['Nom de la protéine']}")
        st.code(selected_row["_sequence_full"], language=None)

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("🔬 Recharger dans le Dashboard", type="primary", use_container_width=True):
                st.session_state["reload_sequence"] = selected_row["_sequence_full"]
                st.session_state["reload_name"]     = selected_row["Nom de la protéine"]
                st.success(
                    "✅ Séquence chargée dans la session. "
                    "Ouvrez le Dashboard — la séquence est prête à être analysée.",
                )
                st.page_link("pages/1_dashboard.py", label="→ Ouvrir le Dashboard")

        with col_btn2:
            if st.button("🗑️ Supprimer cet enregistrement", type="secondary", use_container_width=True):
                if delete_record(selected_id):
                    st.success(f"Enregistrement #{selected_id} supprimé.")
                    st.rerun()
                else:
                    st.error("Suppression échouée — enregistrement introuvable.")

# ---------------------------------------------------------------------------
# Export CSV
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("📥 Exporter l'historique", expanded=False):
    csv_data = df[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Télécharger en CSV",
        data=csv_data,
        file_name=f"neopept_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
