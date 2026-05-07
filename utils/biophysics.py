"""
utils/biophysics.py — NeoPept Pro
Calculs biophysiques basés sur Biopython : poids moléculaire, pI,
aromaticité, hydrophobicité Kyte-Doolittle et structure secondaire.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Tuple

from Bio.SeqUtils.ProtParam import ProteinAnalysis

# Échelle de Kyte-Doolittle (1982) pour les 20 acides aminés standard
KD_SCALE: Dict[str, float] = {
    "A":  1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C":  2.5,
    "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I":  4.5,
    "L":  3.8, "K": -3.9, "M":  1.9, "F":  2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V":  4.2,
}


@dataclass
class BiophysicsProfile:
    """Résultat complet d'une analyse biophysique d'une protéine."""

    sequence: str
    poids_moleculaire: float
    pi_score: float
    aromaticite: float
    instabilite: float
    fraction_helix: float
    fraction_turn: float
    fraction_sheet: float
    aa_count: Dict[str, int]
    hydrophobicity_scores: List[float]


def analyse_sequence(sequence: str, window_size: int = 9) -> BiophysicsProfile:
    """Effectue l'analyse biophysique complète d'une séquence protéique.

    Calcule l'ensemble des propriétés physico-chimiques via Biopython et le
    profil d'hydrophobicité selon l'échelle de Kyte-Doolittle.

    Args:
        sequence: Séquence d'acides aminés en lettres majuscules IUPAC.
        window_size: Taille de la fenêtre glissante pour le calcul
                     d'hydrophobicité (défaut : 9).

    Returns:
        Un ``BiophysicsProfile`` contenant toutes les métriques calculées.

    Raises:
        ValueError: Si la séquence est vide ou contient des caractères invalides.
    """
    seq = sequence.upper().strip()
    analysis = ProteinAnalysis(seq)

    frac = analysis.secondary_structure_fraction()
    hydro = calculate_hydrophobicity(seq, window_size)
    aa_count = analysis.count_amino_acids()

    return BiophysicsProfile(
        sequence=seq,
        poids_moleculaire=analysis.molecular_weight(),
        pi_score=analysis.isoelectric_point(),
        aromaticite=analysis.aromaticity(),
        instabilite=analysis.instability_index(),
        fraction_helix=frac[0],
        fraction_turn=frac[1],
        fraction_sheet=frac[2],
        aa_count=aa_count,
        hydrophobicity_scores=hydro,
    )


def calculate_hydrophobicity(sequence: str, window_size: int = 9) -> List[float]:
    """Calcule le profil d'hydrophobicité par fenêtre glissante (Kyte-Doolittle).

    Args:
        sequence: Séquence d'acides aminés en lettres majuscules IUPAC.
        window_size: Nombre d'acides aminés par fenêtre. Valeurs typiques :
                     7 (signal peptides), 9 (globale), 19 (domaines TM).

    Returns:
        Liste de scores d'hydrophobicité moyens, un par position de fenêtre.
        La liste contient ``len(sequence) - window_size + 1`` éléments.
        Retourne une liste vide si la séquence est plus courte que ``window_size``.
    """
    seq = sequence.upper()
    if len(seq) < window_size:
        return []

    return [
        sum(KD_SCALE.get(aa, 0.0) for aa in seq[i : i + window_size]) / window_size
        for i in range(len(seq) - window_size + 1)
    ]


def apply_mutation(sequence: str, position: int, new_aa: str) -> Tuple[str, str]:
    """Applique une mutation ponctuelle sur une séquence (mutagenèse in silico).

    La position est exprimée en numérotation biologique (1-indexée).

    Args:
        sequence: Séquence originale en lettres majuscules IUPAC.
        position: Position de la mutation (1 = premier acide aminé).
        new_aa: Lettre IUPAC du nouvel acide aminé (ex: ``'W'``).

    Returns:
        Un tuple ``(mutated_sequence, change_description)`` où :

        - ``mutated_sequence`` est la nouvelle séquence avec la substitution.
        - ``change_description`` est une chaîne lisible, ex: ``"A5W"``.

    Raises:
        ValueError: Si la position est hors des bornes ou si ``new_aa`` est invalide.
    """
    seq = sequence.upper().strip()
    aa = new_aa.upper().strip()

    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")

    if aa not in valid_aa:
        raise ValueError(f"Acide aminé invalide : '{aa}'.")

    if not (1 <= position <= len(seq)):
        raise ValueError(
            f"Position {position} hors bornes (séquence de {len(seq)} AA)."
        )

    idx = position - 1
    original_aa = seq[idx]
    mutated = seq[:idx] + aa + seq[idx + 1 :]
    change_desc = f"{original_aa}{position}{aa}"

    return mutated, change_desc


def compare_profiles(
    original: BiophysicsProfile,
    mutant: BiophysicsProfile,
) -> Dict[str, Dict[str, float]]:
    """Compare les métriques clés entre une séquence originale et son mutant.

    Args:
        original: Profil biophysique de la séquence d'origine.
        mutant: Profil biophysique de la séquence mutée.

    Returns:
        Dictionnaire ``{metric: {original, mutant, delta}}`` pour chaque
        métrique numérique clé.
    """
    metrics = {
        "Poids moléculaire (Da)": (original.poids_moleculaire, mutant.poids_moleculaire),
        "Point isoélectrique": (original.pi_score, mutant.pi_score),
        "Aromaticité": (original.aromaticite, mutant.aromaticite),
        "Indice d'instabilité": (original.instabilite, mutant.instabilite),
    }

    return {
        name: {
            "original": orig,
            "mutant": mut,
            "delta": mut - orig,
        }
        for name, (orig, mut) in metrics.items()
    }


# ---------------------------------------------------------------------------
# Alertes Scientifiques (Red Flags)
# ---------------------------------------------------------------------------

AlertLevel = Literal["error", "warning", "info"]


@dataclass
class ScientificAlert:
    """Alerte de formulation générée par l'analyse biophysique."""

    level: AlertLevel
    category: str
    message: str
    recommendation: str
    icon: str = field(default="⚠️")


def get_alerts(profile: BiophysicsProfile) -> List[ScientificAlert]:
    """Analyse un profil biophysique et génère des alertes de formulation.

    Les seuils appliqués sont issus des standards de l'industrie
    biopharmaceutique (formulabilité, stabilité en solution).

    Args:
        profile: Profil biophysique calculé par ``analyse_sequence()``.

    Returns:
        Liste de ``ScientificAlert`` (vide si aucun problème détecté).
        Les alertes de niveau ``error`` précèdent celles de niveau ``warning``.
    """
    alerts: List[ScientificAlert] = []

    # ── Instabilité structurale ──────────────────────────────────────────────
    if profile.instabilite > 40:
        alerts.append(
            ScientificAlert(
                level="warning",
                category="Stabilité",
                message=f"Indice d'instabilité élevé ({profile.instabilite:.1f} > 40).",
                recommendation=(
                    "La protéine est classifiée comme instable in vitro. "
                    "Envisagez des substitutions stabilisatrices (Ala, Val) "
                    "ou l'ajout de ponts disulfure."
                ),
                icon="🌡️",
            )
        )

    # ── Zone de précipitation physiologique (pI ≈ pH 7.4) ───────────────────
    if 6.5 <= profile.pi_score <= 7.5:
        alerts.append(
            ScientificAlert(
                level="error",
                category="Formulation",
                message=(
                    f"pI ({profile.pi_score:.2f}) dans la zone de précipitation physiologique "
                    "(6.5 – 7.5). Risque d'agrégation à pH sanguin."
                ),
                recommendation=(
                    "Modifiez la composition en acides aminés chargés (Arg, Lys, Asp, Glu) "
                    "pour déplacer le pI hors de la zone critique, ou formulez à pH acide/basique."
                ),
                icon="🚨",
            )
        )

    # ── Hydrophobicité excessive ─────────────────────────────────────────────
    if profile.hydrophobicity_scores:
        avg_hydro = sum(profile.hydrophobicity_scores) / len(profile.hydrophobicity_scores)
        if avg_hydro > 1.5:
            alerts.append(
                ScientificAlert(
                    level="warning",
                    category="Solubilité",
                    message=(
                        f"Hydrophobicité moyenne élevée (KD moyen = {avg_hydro:.2f} > 1.5). "
                        "Risque d'agrégation en solution aqueuse."
                    ),
                    recommendation=(
                        "Introduisez des résidus chargés ou polaires (Ser, Thr, Glu) "
                        "ou envisagez une formulation avec détergent doux / excipient."
                    ),
                    icon="💧",
                )
            )

    # ── Séquence très courte (moins de 10 AA) ────────────────────────────────
    if len(profile.sequence) < 10:
        alerts.append(
            ScientificAlert(
                level="info",
                category="Longueur",
                message=f"Séquence très courte ({len(profile.sequence)} AA < 10).",
                recommendation=(
                    "Les peptides de moins de 10 AA sont susceptibles d'être "
                    "dégradés rapidement in vivo. Évaluez la stabilité protéolytique."
                ),
                icon="📏",
            )
        )

    # Tri : errors en premier, puis warnings, puis info
    order: Dict[str, int] = {"error": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: order.get(a.level, 9))

    return alerts
