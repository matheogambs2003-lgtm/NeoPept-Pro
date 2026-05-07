"""
pages/1_dashboard.py — NeoPept Pro v3.0
Dashboard principal : analyse biophysique, alertes scientifiques,
modélisation 3D, export rapport et mutagenèse in silico (comparaison 3D côte-à-côte).
"""

from __future__ import annotations

import sys
from pathlib import Path

import py3Dmol
import streamlit as st
from streamlit_option_menu import option_menu
from stmol import showmol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import save_record
from utils.biophysics import analyse_sequence, apply_mutation, compare_profiles, get_alerts
from utils.esmfold_api import predict_structure, validate_sequence
from utils.report import generate_pdf_report
from utils.ui import inject_css, sidebar_branding, sidebar_nav_links
from utils.visuals import (
    plot_aa_composition,
    plot_hydrophobicity,
    plot_mutation_comparison,
    plot_secondary_structure,
)

# ---------------------------------------------------------------------------
# Page config & CSS global
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard — NeoPept Pro",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------------------------------------------------------------------------
# Session state — persistence entre reruns (navigation option_menu)
# ---------------------------------------------------------------------------
_SS_DEFAULTS = {
    "profile":         None,
    "sequence":        None,
    "protein_name":    None,
    "alerts":          None,
    "mutant_profile":  None,
    "mutant_sequence": None,
    "change_desc":     None,
}
for key, default in _SS_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

DEFAULT_SEQ = "HSQGTFTSDYSKYLDSRRAQDFVQWLMNT"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    sidebar_branding("Dashboard · v3.0")

    protein_name = st.text_input(
        "🏷️ Nom du projet / protéine",
        value=st.session_state.get("reload_name", "Glucagon"),
        help="Ce nom sera enregistré dans l'historique.",
    )

    raw_seq = st.text_area(
        "🔤 Séquence d'acides aminés",
        value=st.session_state.get("reload_sequence", DEFAULT_SEQ),
        height=140,
        help="20 lettres IUPAC (A C D E F G H I K L M N P Q R S T V W Y).",
    )
    sequence: str = raw_seq.upper().strip()

    # Nettoie les clés de rechargement après utilisation
    st.session_state.pop("reload_sequence", None)
    st.session_state.pop("reload_name", None)

    st.caption(f"Longueur : **{len(sequence)} AA**")
    st.markdown("---")
    st.info("💡 Séquences < **400 AA** recommandées pour ESMFold.")

    run_btn = st.button("🚀 Lancer l'Analyse Complète", type="primary", use_container_width=True)

    # Bouton rapport (visible seulement si une analyse est en session)
    if st.session_state["profile"] is not None:
        st.markdown("---")
        if st.button("📄 Générer le Rapport PDF", use_container_width=True):
            with st.spinner("Génération du PDF…"):
                try:
                    pdf_bytes = generate_pdf_report(
                        profile=st.session_state["profile"],
                        protein_name=st.session_state["protein_name"],
                        alerts=st.session_state["alerts"] or [],
                        mutation_desc=st.session_state["change_desc"],
                    )
                    st.session_state["pdf_bytes"] = pdf_bytes
                    st.session_state["pdf_ready"] = True
                    st.toast("✅ Rapport PDF généré avec succès !", icon="📄")
                except Exception as exc:
                    st.error(f"❌ Erreur génération PDF : {exc}")

        if st.session_state.get("pdf_ready"):
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=st.session_state["pdf_bytes"],
                file_name=f"NeoPept_{st.session_state['protein_name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    sidebar_nav_links()

# ---------------------------------------------------------------------------
# Titre principal
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='margin-bottom:.2rem;'>🔬 Dashboard Analyse</h1>"
    "<p style='color:#6c757d;'>Analyse biophysique complète, alertes de formulation, modélisation 3D IA et mutagenèse in silico.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Lancement de l'analyse
# ---------------------------------------------------------------------------
if run_btn:
    is_valid, error_msg = validate_sequence(sequence)
    if not is_valid:
        st.warning(f"⚠️ **Séquence invalide** — {error_msg}")
        st.stop()

    with st.spinner("Analyse biophysique en cours…"):
        try:
            profile = analyse_sequence(
                sequence,
                window_size=st.session_state.get("kd_window", 9),
            )
        except Exception as exc:
            st.error(f"❌ Erreur Biopython : {exc}")
            st.stop()

    # Calcul des alertes
    alerts = get_alerts(profile)

    # Stockage en session
    st.session_state["profile"]      = profile
    st.session_state["sequence"]     = sequence
    st.session_state["protein_name"] = protein_name or "Sans nom"
    st.session_state["alerts"]       = alerts
    # Réinitialise les données de mutation lors d'une nouvelle analyse
    st.session_state["mutant_profile"]  = None
    st.session_state["mutant_sequence"] = None
    st.session_state["change_desc"]     = None
    st.session_state["pdf_ready"]       = False

    # Sauvegarde silencieuse en DB
    try:
        save_record(
            nom=protein_name or "Sans nom",
            sequence=sequence,
            poids_moleculaire=profile.poids_moleculaire,
            pi_score=profile.pi_score,
        )
    except Exception:
        pass

    st.toast(f"✅ Analyse de '{protein_name}' complétée !", icon="🔬")

# ---------------------------------------------------------------------------
# Contenu principal — visible si une analyse est disponible en session
# ---------------------------------------------------------------------------
profile      = st.session_state["profile"]
alerts       = st.session_state["alerts"]
cur_sequence = st.session_state["sequence"]
cur_name     = st.session_state["protein_name"]

if profile is None:
    st.info(
        "👈 **Saisissez votre séquence** dans la barre latérale, donnez-lui un nom, "
        "puis cliquez sur **🚀 Lancer l'Analyse Complète**.",
        icon="🧪",
    )
    with st.expander("📖 Exemples de séquences", expanded=True):
        examples = {
            "Glucagon (29 AA)":           "HSQGTFTSDYSKYLDSRRAQDFVQWLMNT",
            "Insuline A-chain (21 AA)":   "GIVEQCCTSICSLYQLENYCN",
            "GLP-1 (30 AA)":              "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
            "Angiotensine II (8 AA)":     "DRVYIHPF",
        }
        for name, seq in examples.items():
            c1, c2 = st.columns([2, 4])
            c1.markdown(f"**{name}**")
            c2.code(seq, language=None)
    st.stop()

# ---------------------------------------------------------------------------
# Panneau d'Alertes Scientifiques (Red Flags)
# ---------------------------------------------------------------------------
if alerts:
    with st.expander(
        f"🚨 Alertes de Formulation ({len(alerts)} détectée{'s' if len(alerts) > 1 else ''})",
        expanded=True,
    ):
        for alert in alerts:
            css_class = "alert-error" if alert.level == "error" else "alert-warning"
            st.markdown(
                f"""
                <div class='alert-panel {css_class}'>
                    <strong>{alert.icon} [{alert.category}]</strong> {alert.message}<br>
                    <span style='font-size:.9rem;'>💡 <em>{alert.recommendation}</em></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.success("✅ Aucun red flag détecté — La séquence présente un profil de formulation favorable.", icon="✅")

st.markdown("---")

# ---------------------------------------------------------------------------
# Navigation option_menu
# ---------------------------------------------------------------------------
nav = option_menu(
    menu_title=None,
    options=["Propriétés Physico-Chimiques", "Structure 3D", "Data Visualisation", "Mutagenèse in silico"],
    icons=["clipboard-data", "badge-3d", "bar-chart-line", "activity"],
    orientation="horizontal",
    styles={
        "container":        {"padding": "0", "background-color": "transparent", "border-radius": "10px"},
        "icon":             {"color": "#4f8bf9", "font-size": "15px"},
        "nav-link":         {"font-size": "13px", "font-weight": "600", "--hover-color": "rgba(79,139,249,.12)"},
        "nav-link-selected":{"background-color": "#4f8bf9", "color": "white", "border-radius": "8px"},
    },
    key="main_nav",
)

# ============================================================================
# ONGLET 1 — Propriétés Physico-Chimiques
# ============================================================================
if nav == "Propriétés Physico-Chimiques":
    st.markdown("### 📊 Indicateurs Physico-Chimiques Globaux")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⚖️ Poids Moléculaire",    f"{profile.poids_moleculaire:.2f} Da")
    c2.metric("⚡ pI (Isoélectrique)",   f"{profile.pi_score:.2f}")
    c3.metric("💍 Aromaticité",          f"{profile.aromaticite * 100:.1f} %")
    c4.metric(
        "🌡️ Indice d'Instabilité",
        f"{profile.instabilite:.1f}",
        delta="Instable" if profile.instabilite > 40 else "Stable",
        delta_color="inverse",
    )

    st.markdown("---")

    col_struct, col_pie = st.columns(2)

    with col_struct:
        st.markdown("### 🏗️ Structure Secondaire Prédite")
        cs1, cs2, cs3 = st.columns(3)
        cs1.metric("🌀 Hélices Alpha",  f"{profile.fraction_helix  * 100:.1f} %")
        cs2.metric("↪️ Coudes (Turns)", f"{profile.fraction_turn   * 100:.1f} %")
        cs3.metric("〰️ Feuillets Bêta", f"{profile.fraction_sheet  * 100:.1f} %")

    with col_pie:
        fig_pie = plot_secondary_structure(
            profile.fraction_helix,
            profile.fraction_turn,
            profile.fraction_sheet,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with st.expander("📋 Séquence analysée", expanded=False):
        st.code(cur_sequence, language=None)
        st.caption(f"Longueur : {len(cur_sequence)} AA · Projet : {cur_name}")

# ============================================================================
# ONGLET 2 — Structure 3D
# ============================================================================
elif nav == "Structure 3D":
    st.markdown("### 🧬 Modélisation 3D par IA (ESMFold — Meta AI)")

    with st.spinner("Prédiction de la structure 3D en cours (ESMFold)…"):
        pdb_data = predict_structure(cur_sequence)

    if pdb_data:
        col_3d, col_ctrl = st.columns([4, 1])

        with col_ctrl:
            st.markdown("**Style de rendu**")
            style = st.selectbox(
                "Style",
                ["Cartoon (Spectre)", "Cartoon (Bleu)", "Surface", "Bâtons"],
                label_visibility="collapsed",
            )
            bg_color = st.color_picker("Fond", "#ffffff")
            st.download_button(
                "📥 Télécharger .PDB",
                data=pdb_data,
                file_name=f"{cur_name.replace(' ', '_')}.pdb",
                mime="chemical/x-pdb",
                use_container_width=True,
            )

        with col_3d:
            view = py3Dmol.view(width=780, height=520)
            view.addModel(pdb_data, "pdb")
            style_map = {
                "Cartoon (Spectre)": {"cartoon": {"color": "spectrum"}},
                "Cartoon (Bleu)":    {"cartoon": {"color": "#4f8bf9"}},
                "Surface":           {"surface": {"opacity": 0.8, "color": "spectrum"}},
                "Bâtons":            {"stick": {}},
            }
            view.setStyle(style_map.get(style, {"cartoon": {"color": "spectrum"}}))
            view.setBackgroundColor(bg_color)
            view.zoomTo()
            showmol(view, height=520, width=780)
    else:
        st.error("La prédiction 3D a échoué. Vérifiez votre connexion ou réessayez plus tard.")

# ============================================================================
# ONGLET 3 — Data Visualisation
# ============================================================================
elif nav == "Data Visualisation":
    st.markdown("### 📈 Visualisations Interactives")

    col_aa, col_hydro = st.columns(2)

    with col_aa:
        fig_aa = plot_aa_composition(profile.aa_count)
        st.plotly_chart(fig_aa, use_container_width=True)

    with col_hydro:
        kd_window = st.session_state.get("kd_window", 9)
        if profile.hydrophobicity_scores:
            fig_hydro = plot_hydrophobicity(
                profile.hydrophobicity_scores,
                window_size=kd_window,
            )
            st.plotly_chart(fig_hydro, use_container_width=True)
        else:
            st.info(
                f"La séquence ({len(cur_sequence)} AA) est trop courte pour "
                f"une fenêtre KD de {kd_window}. Réduisez dans les Paramètres."
            )

# ============================================================================
# ONGLET 4 — Mutagenèse in silico
# ============================================================================
elif nav == "Mutagenèse in silico":
    st.markdown("### ⚗️ Mutagenèse Ponctuelle in silico")
    st.markdown(
        "Modifiez un acide aminé à une position précise et comparez instantanément "
        "les propriétés biophysiques. Visualisation 3D côte-à-côte disponible.",
    )

    # ── Formulaire de mutation ────────────────────────────────────────────────
    col_m1, col_m2, col_m3 = st.columns([2, 2, 1])

    with col_m1:
        mutation_pos = st.number_input(
            "Position (1-indexée)",
            min_value=1,
            max_value=len(cur_sequence),
            value=min(5, len(cur_sequence)),
            step=1,
            help=f"Séquence : {len(cur_sequence)} AA",
        )
    with col_m2:
        valid_aa_list = list("ACDEFGHIKLMNPQRSTVWY")
        new_aa = st.selectbox("Nouvel acide aminé", valid_aa_list, index=valid_aa_list.index("W"))
    with col_m3:
        st.markdown("<br>", unsafe_allow_html=True)
        mutate_btn = st.button("🔁 Muter", type="primary", use_container_width=True)

    # Prévisualisation en temps réel
    if 1 <= mutation_pos <= len(cur_sequence):
        orig_aa = cur_sequence[mutation_pos - 1]
        st.markdown(
            f"<div class='mutation-box'>"
            f"Mutation prévue : <strong>{orig_aa}{mutation_pos}{new_aa}</strong> "
            f"— <code>{orig_aa}</code> → <code>{new_aa}</code> à la position {mutation_pos}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Calcul de la mutation ─────────────────────────────────────────────────
    if mutate_btn:
        try:
            mutated_seq, change_desc = apply_mutation(cur_sequence, mutation_pos, new_aa)
        except ValueError as exc:
            st.error(f"❌ {exc}")
            st.stop()

        with st.spinner("Analyse du variant en cours…"):
            try:
                mutant_profile = analyse_sequence(
                    mutated_seq,
                    window_size=st.session_state.get("kd_window", 9),
                )
            except Exception as exc:
                st.error(f"❌ Erreur Biopython (variant) : {exc}")
                st.stop()

        # Persistance en session
        st.session_state["mutant_profile"]  = mutant_profile
        st.session_state["mutant_sequence"] = mutated_seq
        st.session_state["change_desc"]     = change_desc
        st.toast(f"✅ Mutation {change_desc} appliquée !", icon="⚗️")

    # ── Résultats (depuis la session — persistants entre reruns) ─────────────
    mutant_profile  = st.session_state["mutant_profile"]
    mutant_sequence = st.session_state["mutant_sequence"]
    change_desc     = st.session_state["change_desc"]

    if mutant_profile is not None:
        comparison = compare_profiles(profile, mutant_profile)
        st.markdown(f"#### 📊 Résultats — Mutation **{change_desc}**")

        # Tableau comparatif côte à côte avec deltas
        col_wt, col_mt = st.columns(2)

        with col_wt:
            st.markdown(
                "<div style='text-align:center; padding:8px; background:rgba(79,139,249,.12); "
                "border-radius:8px; font-weight:700; margin-bottom:10px;'>🔵 Séquence Sauvage (WT)</div>",
                unsafe_allow_html=True,
            )
            st.metric("⚖️ Poids Moléculaire", f"{profile.poids_moleculaire:.2f} Da")
            st.metric("⚡ pI",                f"{profile.pi_score:.2f}")
            st.metric("💍 Aromaticité",       f"{profile.aromaticite * 100:.1f} %")
            st.metric("🌡️ Instabilité",       f"{profile.instabilite:.1f}")

        with col_mt:
            st.markdown(
                "<div style='text-align:center; padding:8px; background:rgba(239,68,68,.12); "
                "border-radius:8px; font-weight:700; margin-bottom:10px;'>🔴 Variant Muté</div>",
                unsafe_allow_html=True,
            )
            d_poids = mutant_profile.poids_moleculaire - profile.poids_moleculaire
            d_pi    = mutant_profile.pi_score - profile.pi_score
            d_aro   = (mutant_profile.aromaticite - profile.aromaticite) * 100
            d_inst  = mutant_profile.instabilite - profile.instabilite

            st.metric("⚖️ Poids Moléculaire", f"{mutant_profile.poids_moleculaire:.2f} Da",
                      delta=f"{d_poids:+.2f} Da")
            st.metric("⚡ pI",                f"{mutant_profile.pi_score:.2f}",
                      delta=f"{d_pi:+.3f}")
            st.metric("💍 Aromaticité",       f"{mutant_profile.aromaticite * 100:.1f} %",
                      delta=f"{d_aro:+.1f} %")
            st.metric("🌡️ Instabilité",       f"{mutant_profile.instabilite:.1f}",
                      delta=f"{d_inst:+.1f}", delta_color="inverse")

        # Tableau Delta récapitulatif
        st.markdown("---")
        st.markdown("##### Tableau Δ (Wild-Type → Mutant)")
        import pandas as pd
        delta_rows = [
            {
                "Paramètre": name,
                "Wild-Type": f"{vals['original']:.3f}",
                "Variant":   f"{vals['mutant']:.3f}",
                "Δ":         f"{vals['delta']:+.3f}",
            }
            for name, vals in comparison.items()
        ]
        st.dataframe(
            pd.DataFrame(delta_rows),
            hide_index=True,
            use_container_width=True,
        )

        # Graphique comparatif
        fig_comp = plot_mutation_comparison(comparison)
        st.plotly_chart(fig_comp, use_container_width=True)

        # ── Visualisation 3D côte-à-côte ─────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🧬 Comparaison des Structures 3D (ESMFold)")

        show_side_by_side = st.checkbox(
            "Afficher les deux structures 3D côte-à-côte (Wild-Type vs Variant)",
            value=False,
            help="Lance deux prédictions ESMFold et les affiche en parallèle.",
        )

        if show_side_by_side:
            col_wt3d, col_mt3d = st.columns(2)

            with col_wt3d:
                st.markdown(
                    "<div style='text-align:center;font-weight:700;color:#4f8bf9;margin-bottom:6px;'>"
                    "🔵 Wild-Type</div>",
                    unsafe_allow_html=True,
                )
                with st.spinner("Prédiction 3D — Wild-Type…"):
                    wt_pdb = predict_structure(cur_sequence)
                if wt_pdb:
                    v_wt = py3Dmol.view(width=440, height=400)
                    v_wt.addModel(wt_pdb, "pdb")
                    v_wt.setStyle({"cartoon": {"color": "spectrum"}})
                    v_wt.setBackgroundColor("#ffffff")
                    v_wt.zoomTo()
                    showmol(v_wt, height=400, width=440)
                    st.download_button(
                        "📥 .PDB Wild-Type",
                        data=wt_pdb,
                        file_name=f"{cur_name}_WT.pdb",
                        mime="chemical/x-pdb",
                    )
                else:
                    st.error("Prédiction WT échouée.")

            with col_mt3d:
                st.markdown(
                    "<div style='text-align:center;font-weight:700;color:#ef4444;margin-bottom:6px;'>"
                    f"🔴 Variant {change_desc}</div>",
                    unsafe_allow_html=True,
                )
                with st.spinner(f"Prédiction 3D — Variant {change_desc}…"):
                    mt_pdb = predict_structure(mutant_sequence)
                if mt_pdb:
                    v_mt = py3Dmol.view(width=440, height=400)
                    v_mt.addModel(mt_pdb, "pdb")
                    v_mt.setStyle({"cartoon": {"color": "spectrum"}})
                    v_mt.setBackgroundColor("#ffffff")
                    v_mt.zoomTo()
                    showmol(v_mt, height=400, width=440)
                    st.download_button(
                        f"📥 .PDB {change_desc}",
                        data=mt_pdb,
                        file_name=f"{cur_name}_{change_desc}.pdb",
                        mime="chemical/x-pdb",
                    )
                else:
                    st.error("Prédiction variante échouée.")
        else:
            # Visualisation simple du variant seulement
            with st.expander(f"🧬 Prédire la structure 3D du variant {change_desc}", expanded=False):
                if st.button("🚀 Lancer la prédiction ESMFold du variant", type="primary"):
                    with st.spinner(f"Prédiction ESMFold — {change_desc}…"):
                        mt_pdb = predict_structure(mutant_sequence)
                    if mt_pdb:
                        v = py3Dmol.view(width=760, height=480)
                        v.addModel(mt_pdb, "pdb")
                        v.setStyle({"cartoon": {"color": "spectrum"}})
                        v.setBackgroundColor("#ffffff")
                        v.zoomTo()
                        showmol(v, height=480, width=760)
                        st.download_button(
                            f"📥 Télécharger .PDB ({change_desc})",
                            data=mt_pdb,
                            file_name=f"{cur_name}_{change_desc}.pdb",
                            mime="chemical/x-pdb",
                        )
                    else:
                        st.error("La prédiction 3D du variant a échoué.")
    else:
        st.info(
            "Configurez la mutation ci-dessus et cliquez sur **🔁 Muter** pour voir les résultats.",
            icon="⚗️",
        )
