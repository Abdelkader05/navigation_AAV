from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import networkx as nx
from app.models import TriggerRemediation, GeneratePath, RemediationResponse, PathRequest, ErreurApprenant
from app.remediation_service import trouver_causes_racines, generer_parcours_remediation, get_niveau_maitrise
from app.database import RemediationRepository, from_json, get_db_connection
from app.config import settings

router = APIRouter(
    tags=["Remediation & Diagnostic"],
    responses={404: {"description": "Ressource non trouvée"}, 422: {"description": "Données invalides"}}
)

repo = RemediationRepository()

@router.post("/diagnostics/remediation", response_model=RemediationResponse, status_code=201)
def trigger_remediation(request: TriggerRemediation):
    """Déclenche une analyse de remédiation suite à un échec."""
    causes, graphe = trouver_causes_racines(request.id_apprenant, request.id_aav_source)
    recommandations = generer_parcours_remediation(causes, request.id_apprenant)
    
    diag_id = repo.make(
        id_apprenant=request.id_apprenant,
        id_aav_source=request.id_aav_source,
        score=request.score_obtenu,
        racines=causes,
        recos=recommandations
    )
    
    return RemediationResponse(
        id_diagnostic=diag_id,
        id_apprenant=request.id_apprenant,
        id_aav_source=request.id_aav_source,
        aav_defaillants=causes,
        recommandations=recommandations,
        date_diagnostic=datetime.now()
    )

@router.get("/learners/{id_apprenant}/diagnostics")
def get_learner_history(id_apprenant: int):
    res = repo.get_apprenant(id_apprenant)
    for row in res:
        if isinstance(row.get("aav_racines_defaillants"), str):
            row["aav_racines_defaillants"] = from_json(row["aav_racines_defaillants"])
        if isinstance(row.get("recommandations"), str):
            row["recommandations"] = from_json(row["recommandations"])
            
    return res


#@router.get("/learners/{id_apprenant}/diagnostics")
#def get_learner_diagnostics(id_apprenant: int):
#    """Historique des diagnostics pour un apprenant."""
#    rows = repo.get_by_apprenant(id_apprenant)
#    for line in rows:
#        line['aav_racines_defaillants'] = from_json(line['aav_racines_defaillants'])
#        line['recommandations'] = from_json(line['recommandations'])
#    return rows
#

@router.get("/learners/{id_apprenant}/aavs/{id_aav}/root-causes")
def analyze_root_causes(id_aav: int, id_apprenant: int):
    """
    Analyse ascendante des prérequis pour identifier pourquoi 
    l'apprenant a échoué sur un AAV spécifique.
    """
    causes, _ = trouver_causes_racines(id_apprenant, id_aav)
    return {
        "id_apprenant": id_apprenant,
        "id_aav_analyse": id_aav,
        "root_causes": causes
    }

@router.post("/remediation/generate-path")
def generate_remediation_path(request: GeneratePath):
    """Génère un parcours personnalisé."""
    causes, _ = trouver_causes_racines(
    request.id_apprenant,
    request.id_aav_cible,
    seuil_defaillance=settings.review_threshold
    )
    return {
        "id_aav_cible": request.id_aav_cible,
        "parcours_genere": generer_parcours_remediation(causes, request.id_apprenant)}
        
@router.post("/diagnostics/analyze-path")
def analyze_path(request: PathRequest):
    """Analyse un chemin spécifique de prérequis."""
    resultats =[]
    for aav_id in request.chemin_aavs:
        niveau = get_niveau_maitrise(request.id_apprenant, aav_id)
        resultats.append({
            "id_aav": aav_id,
            "maitrise": niveau,
            "statut": "OK" if niveau >= 0.5 else "AJ"
        })
    return {"path_analysis": resultats}
        
@router.get("/learners/{id_apprenant}/weaknesses", response_model=List[ErreurApprenant])
def get_learner_weaknesses(id_apprenant: int):
    """Récupère les points faibles identifiés d'un apprenant."""
    diags = repo.get_apprenant(id_apprenant)
    weaknesses = {}
    for d in diags:
        defaillants = from_json(d['aav_racines_defaillants'])
        for aav_id in defaillants:
            if aav_id not in weaknesses:
                weaknesses[aav_id] = get_niveau_maitrise(id_apprenant, aav_id)
                
    return[
        ErreurApprenant(id_aav=k, maitrise=v, reussi=(v < 0.3)) 
        for k, v in weaknesses.items()
    ]
        
@router.get("/remediation/activities/{id_diagnostic}")
def get_remediation_activities(id_diagnostic: int):
    diag = repo.get_by_id(id_diagnostic)
    if diag is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Le diagnostic avec l'ID {id_diagnostic} n'existe pas en base."
        )
    racines = from_json(diag["aav_racines_defaillants"]) if isinstance(diag["aav_racines_defaillants"], str) else diag["aav_racines_defaillants"]
    if not racines:
        return []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        placeholders = ', '.join(['?'] * len(racines))
        query = f"SELECT * FROM activite_pedagogique WHERE id_aav IN ({placeholders})"
        cursor.execute(query, racines)
        return [dict(row) for row in cursor.fetchall()]
        
@router.get("/diagnostics/{id_diagnostic}/tree")
def get_diagnostic_tree(id_diagnostic: int):
    diag = repo.get_by_id(id_diagnostic)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnostic non trouvé")
    G = nx.DiGraph()
    source = diag["id_aav_source"]
    racines = from_json(diag["aav_racines_defaillants"]) if isinstance(diag["aav_racines_defaillants"], str) else diag["aav_racines_defaillants"]
    for racine in racines:
        G.add_edge(source, racine)
    return nx.node_link_data(G)
        
@router.get("/learners/{id_apprenant}/progression-map")
def get_progression_map(id_apprenant: int):
    """Carte de chaleur du graphe des compétences pour l'apprenant."""
    historique = repo.get_apprenant(id_apprenant)
    aavs = set()
    for row in historique:
        aavs.add(row['id_aav_source'])
        aavs.update(from_json(row['aav_racines_defaillants']))
        
    heatmap = [{
            "id_aav": aav_id,
            "niveau_maitrise": get_niveau_maitrise(id_apprenant, aav_id),
            "couleur_recommandee": "rouge" if get_niveau_maitrise(id_apprenant, aav_id) < settings.failure_threshold 
                                   else "jaune" if get_niveau_maitrise(id_apprenant, aav_id) < settings.mastery_threshold
                                   else "vert"
        }
        for aav_id in aavs
    ]

    return {"progression_map": heatmap}

@router.get("/diagnostics/{id_diagnostic}")
def get_diagnostic(id_diagnostic: int):
    diag = repo.get_by_id(id_diagnostic)
    if diag is None:
        raise HTTPException(status_code=404, detail="Diagnostic non trouvé")

    if isinstance(diag.get("aav_racines_defaillants"), str):
        diag["aav_racines_defaillants"] = from_json(diag["aav_racines_defaillants"])
    if isinstance(diag.get("recommandations"), str):
        diag["recommandations"] = from_json(diag["recommandations"])

    return diag