"""
utils/esmfold_api.py — NeoPept Pro
Fonctions de communication avec l'API publique ESMFold de Meta AI.
"""

from __future__ import annotations

from typing import Optional

import requests
import streamlit as st

ESMFOLD_URL = "https://api.esmatlas.com/foldSequence/v1/pdb/"
REQUEST_TIMEOUT = 120  # secondes


@st.cache_data(show_spinner=False)
def predict_structure(sequence: str) -> Optional[str]:
    """Envoie une séquence à l'API ESMFold et retourne le contenu PDB.

    Le résultat est mis en cache par Streamlit : des appels successifs avec
    la même séquence ne consomment pas de quota API.

    Args:
        sequence: Séquence d'acides aminés en lettres majuscules IUPAC
                  (ex: ``"HSQGTFTSDYSKYLDSRRAQDFVQWLMNT"``).

    Returns:
        Le contenu du fichier PDB sous forme de chaîne de caractères si
        la prédiction réussit, ``None`` sinon.
    """
    try:
        response = requests.post(
            ESMFOLD_URL,
            data=sequence,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        st.error(
            "⏱️ **Timeout ESMFold** : L'API n'a pas répondu dans les "
            f"{REQUEST_TIMEOUT}s. Réessayez avec une séquence plus courte (<400 AA)."
        )
        return None
    except requests.exceptions.HTTPError as exc:
        st.error(
            f"🚫 **Erreur HTTP ESMFold ({exc.response.status_code})** : "
            "Le serveur a rejeté la requête. Vérifiez la séquence."
        )
        return None
    except requests.exceptions.RequestException as exc:
        st.error(f"🌐 **Erreur réseau** : {exc}")
        return None


def validate_sequence(sequence: str) -> tuple[bool, str]:
    """Vérifie qu'une séquence ne contient que des acides aminés IUPAC valides.

    Args:
        sequence: Séquence brute saisie par l'utilisateur (sera mise en
                  majuscules avant validation).

    Returns:
        Un tuple ``(is_valid, message)`` :

        - ``is_valid`` vaut ``True`` si la séquence est conforme.
        - ``message`` est une chaîne vide si valide, sinon un message
          d'erreur indiquant les caractères illicites trouvés.
    """
    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
    seq_upper = sequence.upper().strip()

    if not seq_upper:
        return False, "La séquence est vide."

    invalid_chars = sorted({c for c in seq_upper if c not in valid_aa})

    if invalid_chars:
        return (
            False,
            f"Caractères non reconnus détectés : **{'**, **'.join(invalid_chars)}**. "
            "Seules les 20 lettres IUPAC standard sont autorisées (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y).",
        )

    if len(seq_upper) < 6:
        return False, "La séquence doit contenir au moins 6 acides aminés."

    if len(seq_upper) > 400:
        return (
            False,
            f"La séquence contient {len(seq_upper)} AA. L'API ESMFold est limitée à **400 AA** maximum.",
        )

    return True, ""
