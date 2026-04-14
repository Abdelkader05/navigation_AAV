import networkx as nx
from typing import List, Tuple, Dict
from app.database import get_db_connection, from_json
from app.config import settings

def get_prerequis(id_aav: int) -> List[int]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT prerequis_ids FROM aav WHERE id_aav = ? AND is_active = 1",
            (id_aav,)
        )
        row = cursor.fetchone()
        if not row:
            return []
        return from_json(row["prerequis_ids"]) or []


def get_niveau_maitrise(id_apprenant: int, id_aav: int) -> float:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT niveau_maitrise
            FROM statut_apprentissage
            WHERE id_apprenant = ? AND id_aav_cible = ?
            """,
            (id_apprenant, id_aav)
        )
        row = cursor.fetchone()
        if not row:
            return 0.0
        return float(row["niveau_maitrise"])

def trouver_causes_racines(
    id_apprenant: int,
    id_aav_source: int,
    seuil_defaillance: float = settings.failure_threshold
) -> List[int]:
    """
    Remonte récursivement le graphe des prérequis depuis l'AAV source.
    Pour chaque prérequis direct:
      - Si maîtrise < seuil: c'est une cause racine potentielle
      - Sinon: continue la remontée sur ses prérequis

    Optimisation: arrêter quand on atteint un AAV déjà maîtrisé (>= 0.9).
    """
    causes_racines =[]
    visites = set()
    G = nx.DiGraph()
    niveau_source = get_niveau_maitrise(id_apprenant, id_aav_source)
    G.add_node(id_aav_source, maitrise=niveau_source, est_source=True)
    def remonter(aav_id: int, aav_enfant: int, profondeur: int):
        if profondeur > 5:
            return
        if aav_id in visites:
            G.add_edge(aav_enfant, aav_id)
            return
        visites.add(aav_id)
        niveau = get_niveau_maitrise(id_apprenant, aav_id)
        G.add_node(aav_id, maitrise=niveau, est_source=False)
        G.add_edge(aav_enfant, aav_id)
        if niveau >= settings.mastery_threshold:
            return
        elif niveau < seuil_defaillance:
            causes_racines.append(aav_id)
            return 
        else:
            for prereq_id in get_prerequis(aav_id):
                remonter(prereq_id, aav_id, profondeur + 1)
    for prereq in get_prerequis(id_aav_source):
        remonter(prereq, id_aav_source, 1)

    return causes_racines, G   

def generer_parcours_remediation(causes_racines: List[int], id_apprenant: int) -> List[dict]:
    """
    Ordonne les causes racines pour un parcours de remédiation efficace.
    Stratégie:
    1. Trier par niveau de maîtrise croissant (les plus faibles d'abord)
    2. Pour chaque cause, inclure ses prérequis si nécessaire
    3. Éviter les redondances
    """
    parcours = []
    for cause_id in causes_racines:
        niveau = get_niveau_maitrise(id_apprenant, cause_id)
        parcours.append({
            "id_aav": cause_id,
            "priorite": "haute" if niveau < 0.3 else "moyenne",
            "type_action": "revision" if niveau > 0 else "apprentissage"
        })
    return parcours