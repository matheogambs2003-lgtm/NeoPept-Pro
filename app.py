"""
app.py — NeoPept Pro
Point d'entrée principal de l'application Streamlit.
Initialise la base de données et affiche la page d'accueil / hub de navigation.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import init_db
from utils.ui import inject_css, sidebar_branding, sidebar_nav_links

# ---------------------------------------------------------------------------
# Initialisation de la base de données (exécuté une seule fois au démarrage)
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Configuration globale de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NeoPept Pro — TechBio SaaS",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------------------------------------------------------------------------
# Sidebar globale (branding + version)
# ---------------------------------------------------------------------------
with st.sidebar:
    sidebar_branding("TechBio SaaS · v3.0")
    st.caption("Naviguez via les liens rapides ci-dessous.")
    sidebar_nav_links()

# ---------------------------------------------------------------------------
# Contenu de la page d'accueil
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style='padding: 40px 0 20px;'>
        <h1 style='font-size:2.8rem; font-weight:800; margin-bottom:.3rem;'>
            🧬 NeoPept <span style='color:#4f8bf9;'>Pro</span>
        </h1>
        <p style='font-size:1.15rem; color:#6c757d; max-width:680px;'>
            Plateforme de <strong>De Novo Peptide Design</strong> — analyse biophysique avancée,
            modélisation 3D par IA (ESMFold) et mutagenèse in silico, en une seule interface.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_cta, _ = st.columns([1, 3])
with col_cta:
    if st.button("🚀 Ouvrir le Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/1_dashboard.py")

st.markdown("---")

# ---------------------------------------------------------------------------
# Cartes des fonctionnalités
# ---------------------------------------------------------------------------
st.markdown("### Fonctionnalités de la plateforme")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        "<div class='feature-card'><h4>🔬 Analyse Biophysique</h4>"
        "<p>Poids moléculaire, pI, aromaticité, instabilité et structure secondaire "
        "calculés instantanément avec <strong>Biopython</strong>.</p></div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        "<div class='feature-card'><h4>🧠 Structure 3D (IA)</h4>"
        "<p>Prédiction tertiaire par <strong>ESMFold (Meta AI)</strong> "
        "avec export .PDB et visualisation interactive.</p></div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        "<div class='feature-card'><h4>⚗️ Mutagenèse in silico</h4>"
        "<p>Mutation ponctuelle + comparaison ΔpI, ΔPoids et visualisation "
        "<strong>3D côte-à-côte</strong> WT vs Variant.</p></div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
c4, c5, c6 = st.columns(3)

with c4:
    st.markdown(
        "<div class='feature-card'><h4>⚡ Batch Screening</h4>"
        "<p>Upload d'un fichier <strong>FASTA</strong> et analyse biophysique "
        "de toutes les séquences en une passe + export CSV.</p></div>",
        unsafe_allow_html=True,
    )
with c5:
    st.markdown(
        "<div class='feature-card'><h4>🚨 Alertes de Formulation</h4>"
        "<p>Red flags automatiques : instabilité, précipitation au pI, "
        "hydrophobicité excessive — avec recommandations.</p></div>",
        unsafe_allow_html=True,
    )
with c6:
    st.markdown(
        "<div class='feature-card'><h4>📄 Export Rapport PDF</h4>"
        "<p>Génération d'un rapport <strong>qualité publication</strong> "
        "(ReportLab) : métriques, séquence, alertes, en un clic.</p></div>",
        unsafe_allow_html=True,
    )
