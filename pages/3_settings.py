"""
pages/3_settings.py — NeoPept Pro
Paramètres utilisateur : configuration de l'analyse, fenêtre KD,
gestion de la base de données locale.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import get_all_records, init_db
from utils.ui import inject_css, sidebar_branding, sidebar_nav_links

# ---------------------------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Paramètres — NeoPept Pro",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
st.markdown(
    """
    <style>
    .settings-section {
        background: rgba(79,139,249,.04);
        border-radius: 12px; padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 16px;
        border: 1px solid rgba(79,139,249,.12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    sidebar_branding("Paramètres · v3.0")
    sidebar_nav_links()

# ---------------------------------------------------------------------------
# Contenu principal
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='margin-bottom:.2rem;'>⚙️ Paramètres</h1>"
    "<p style='color:#6c757d;'>Personnalisez votre expérience NeoPept Pro.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Section 1 — Analyse Biophysique
# ---------------------------------------------------------------------------
st.markdown("### 🔬 Paramètres d'Analyse Biophysique")

with st.container():
    st.markdown("<div class='settings-section'>", unsafe_allow_html=True)

    col_kd, col_info_kd = st.columns([2, 3])

    with col_kd:
        kd_window = st.slider(
            "Fenêtre Kyte-Doolittle",
            min_value=5,
            max_value=21,
            value=st.session_state.get("kd_window", 9),
            step=2,
            help="Taille de la fenêtre glissante pour le calcul d'hydrophobicité. "
                 "9 = standard global, 19 = domaines transmembranaires.",
        )
        st.session_state["kd_window"] = kd_window

    with col_info_kd:
        st.info(
            f"**Fenêtre actuelle : {kd_window} AA**\n\n"
            "- **7** : Signal peptides\n"
            "- **9** : Profil global standard ✅\n"
            "- **19** : Détection domaines transmembranaires"
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section 2 — API ESMFold
# ---------------------------------------------------------------------------
st.markdown("### 🧠 Paramètres API ESMFold")

with st.container():
    st.markdown("<div class='settings-section'>", unsafe_allow_html=True)

    col_api1, col_api2 = st.columns([2, 3])

    with col_api1:
        max_seq_length = st.number_input(
            "Longueur maximale de séquence pour ESMFold (AA)",
            min_value=50,
            max_value=400,
            value=st.session_state.get("max_seq_length", 400),
            step=10,
            help="Les séquences dépassant cette limite ne seront pas envoyées à l'API.",
        )
        st.session_state["max_seq_length"] = max_seq_length

        timeout_val = st.number_input(
            "Timeout de la requête (secondes)",
            min_value=30,
            max_value=300,
            value=st.session_state.get("api_timeout", 120),
            step=10,
        )
        st.session_state["api_timeout"] = timeout_val

    with col_api2:
        st.warning(
            "⚠️ **API publique** : L'API ESMFold de Meta est gratuite mais publique. "
            "Pour une utilisation en production, envisagez un déploiement local d'ESMFold "
            "ou l'API privée Meta."
        )
        st.markdown(
            "📖 [Documentation ESMFold](https://esmatlas.com/resources?action=fold)",
            unsafe_allow_html=False,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section 3 — Gestion de la Base de Données
# ---------------------------------------------------------------------------
st.markdown("### 🗄️ Gestion de la Base de Données Locale")

with st.container():
    st.markdown("<div class='settings-section'>", unsafe_allow_html=True)

    records = get_all_records()
    db_path = Path("neopept.db")

    col_db1, col_db2 = st.columns([2, 3])

    with col_db1:
        st.metric("📊 Enregistrements en base", len(records))
        if db_path.exists():
            size_kb = db_path.stat().st_size / 1024
            st.metric("💾 Taille de la base", f"{size_kb:.1f} Ko")
        else:
            st.metric("💾 Taille de la base", "0 Ko")

    with col_db2:
        st.markdown("**Actions**")

        if st.button("🔄 Réinitialiser les tables (sans supprimer les données)", use_container_width=True):
            init_db()
            st.success("Tables vérifiées / recréées si absentes.")

        st.markdown("---")
        st.markdown("**Zone de danger**")

        with st.expander("🗑️ Supprimer TOUTES les analyses", expanded=False):
            st.error(
                "⚠️ **Action irréversible** : Cette opération supprimera définitivement "
                f"**{len(records)} enregistrement(s)** de la base de données."
            )
            confirm_delete = st.text_input(
                "Tapez **CONFIRMER** pour valider",
                placeholder="CONFIRMER",
            )
            if st.button("🗑️ Vider la base de données", type="primary", use_container_width=True):
                if confirm_delete == "CONFIRMER":
                    from database import engine, Base
                    Base.metadata.drop_all(bind=engine)
                    init_db()
                    st.success("✅ Base de données vidée et réinitialisée.")
                    st.rerun()
                else:
                    st.warning("Tapez exactement **CONFIRMER** pour valider l'opération.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section 4 — À propos
# ---------------------------------------------------------------------------
st.markdown("### ℹ️ À propos de NeoPept Pro")

with st.expander("Informations sur la plateforme", expanded=False):
    col_about1, col_about2 = st.columns(2)

    with col_about1:
        st.markdown(
            """
            **NeoPept Pro v2.0**
            Plateforme SaaS TechBio de De Novo Peptide Design.

            | Composant | Version |
            |---|---|
            | Streamlit | ≥ 1.36 |
            | Biopython | ≥ 1.83 |
            | SQLAlchemy | ≥ 2.0 |
            | Plotly | ≥ 5.18 |
            | ESMFold | API publique Meta |
            """
        )

    with col_about2:
        st.markdown(
            """
            **Architecture**
            ```
            NeoPept_Project/
            ├── app.py          # Routeur / Home
            ├── database.py     # SQLAlchemy ORM
            ├── pages/
            │   ├── 1_dashboard.py
            │   ├── 2_history.py
            │   └── 3_settings.py
            └── utils/
                ├── esmfold_api.py
                ├── biophysics.py
                └── visuals.py
            ```
            """
        )
