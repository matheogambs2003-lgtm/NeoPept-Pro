"""
utils/ui.py — NeoPept Pro
Composants UI partagés : injection CSS globale, thème compatible Dark/Light Mode.
À appeler en tête de chaque page avec inject_css().
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# CSS global — Dark Mode safe
# Règles :
#   - Pas de couleurs de fond fixes sur les métriques (utilise rgba transparent)
#   - Pas de couleurs de texte explicites sur les métriques (héritage du thème)
#   - Sidebar toujours en thème sombre pour un look SaaS pro
#   - Navigation native Streamlit masquée (double menu évité)
# ---------------------------------------------------------------------------
_GLOBAL_CSS = """
<style>
/* ── Masque le menu de navigation natif Streamlit ── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Métriques — compatible Dark & Light mode ──
   Fond semi-transparent au lieu d'un gris fixe, texte hérité du thème. */
[data-testid="stMetric"] {
    background: rgba(79, 139, 249, 0.08) !important;
    padding: 16px 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12) !important;
    border-left: 4px solid #4f8bf9 !important;
}

/* ── Sidebar — thème sombre fixe ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1117 0%, #1a1d2e 100%) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .element-container {
    color: #e9ecef !important;
}

/* ── Boutons primaires ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f8bf9, #2563eb) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    transition: opacity .2s !important;
}
.stButton > button[kind="primary"]:hover { opacity: .85 !important; }

/* ── Option-menu horizontal — compatible dark mode ── */
.nav-link { color: inherit !important; }

/* ── Boîte mutation — border accent, fond adaptatif ── */
.mutation-box {
    background: rgba(245, 158, 11, 0.08) !important;
    border-left: 4px solid #f59e0b !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
    margin-top: 10px !important;
}

/* ── Panneau d'alerte scientifique ── */
.alert-panel {
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.alert-error   { background: rgba(239,68,68,0.10); border-left: 4px solid #ef4444; }
.alert-warning { background: rgba(245,158,11,0.10); border-left: 4px solid #f59e0b; }

/* ── Cartes features accueil ── */
.feature-card {
    background: rgba(79,139,249,0.05);
    border-radius: 12px;
    padding: 22px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    border-top: 4px solid #4f8bf9;
    height: 100%;
}
.feature-card h4 { margin-top: 0; }
</style>
"""


def inject_css() -> None:
    """Injecte la feuille de style globale NeoPept Pro dans la page courante.

    Doit être appelé une fois en tête de chaque fichier de page, après
    ``st.set_page_config()``.
    """
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def sidebar_branding(subtitle: str = "v3.0") -> None:
    """Affiche le bloc de branding NeoPept Pro en haut de la sidebar.

    Args:
        subtitle: Sous-titre affiché sous le logo (ex: ``"Dashboard · v3.0"``).
    """
    st.markdown(
        f"""
        <div style='text-align:center; padding:10px 0 18px;'>
            <span style='font-size:2.6rem;'>🧬</span>
            <h2 style='margin:4px 0 2px; font-size:1.35rem; color:#ffffff;'>NeoPept Pro</h2>
            <span style='font-size:.76rem; color:#adb5bd; letter-spacing:.06em;'>{subtitle}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav_links(current_page: str = "") -> None:
    """Affiche les liens de navigation communs dans la sidebar.

    Args:
        current_page: Nom de la page active (pour un futur highlight visuel).
    """
    st.markdown("---")
    st.page_link("app.py",                  label="🏠 Accueil")
    st.page_link("pages/1_dashboard.py",    label="🔬 Dashboard Analyse")
    st.page_link("pages/2_history.py",      label="📋 Historique")
    st.page_link("pages/4_batch_analysis.py", label="⚡ Batch Screening")
    st.page_link("pages/3_settings.py",     label="⚙️  Paramètres")
    st.markdown("---")
    st.caption("© 2026 NeoPept Pro · ESMFold (Meta AI)")
