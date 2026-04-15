from typing import List


def calculer_maitrise(scores: List[float], seuil_succes: float, nombre_succes_consecutifs: int) -> float:
    """
    Reprise de la logique du groupe 3 pour calculer la maitrise.
    """
    if not scores:
        return 0.0

    # Le groupe 3 regarde d'abord les N derniers scores pour détecter
    # une vraie série de réussites consécutives.
    derniers_scores = scores[-nombre_succes_consecutifs:]
    succes_derniers_scores = [score for score in derniers_scores if score >= seuil_succes]

    if (
        len(derniers_scores) >= nombre_succes_consecutifs
        and len(succes_derniers_scores) == nombre_succes_consecutifs
    ):
        return 1.0

    # Sinon, le niveau retombe sur une moyenne bornée sous 1.0.
    moyenne = sum(scores) / len(scores)
    return min(round(moyenne, 2), 0.99)


def message(
    ancien_niveau: float,
    nouveau_niveau: float,
    est_maitrise: bool,
    nombre_succes_consecutifs: int,
) -> str:
    """
    Reprise de la logique de message du groupe 3.
    """
    if est_maitrise:
        return (
            f"Felicitation ! Vous avez atteint la maitrise de cet AAV avec "
            f"{nombre_succes_consecutifs} reussites consecutives."
        )

    if nouveau_niveau > ancien_niveau:
        return f"Bravo ! Votre niveau de maitrise a augmente de {ancien_niveau} a {nouveau_niveau}."

    return f"Votre niveau de maitrise est reste a {nouveau_niveau}."
