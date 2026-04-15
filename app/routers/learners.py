# app/routers/aavs.py

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models import Learner, LearnerCreate, LearnerUpdate
from app.models import LearningStatus, LearningStatusSummary
from app.models import ExternalPrerequisite, ExternalPrerequisiteCreate
from app.models import OntologyReference, OntologySwitchResponse
from app.models import ProgressResponse
from app.database import get_db_connection, BaseRepository, to_json, from_json
import sqlite3

router = APIRouter(
    prefix="/learners",
    tags=["Learners"],
    responses={
        404: {"description": "Apprenant non trouvé"},
        422: {"description": "Données invalides"}
    }
)

# Repository spécifique


class LearnerRepository(BaseRepository):
    def __init__(self):
        super().__init__("apprenant", "id_apprenant")

    def get_by_id(self, id_value: int):
        """Récupère un apprenant uniquement s'il est actif."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM apprenant
                WHERE id_apprenant = ? AND is_active = 1""",
                (id_value,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def create(self, data: dict) -> int:  # ?a changer
        """Crée un apprentant et retourne son ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Conversion des listes en JSON
            status_json = to_json(data.get('statuts_actifs_ids', []))
            prerequis_json = to_json(
                data.get('codes_prerequis_externes_valides', []))

            cursor.execute("""
                INSERT INTO apprenant (
                    id_apprenant, nom_utilisateur, email,
                    ontologie_reference_id,
                    statuts_actifs_ids,
                    codes_prerequis_externes_valides,
                    derniere_connexion
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data['id_apprenant'],
                data['nom_utilisateur'],
                data['email'],
                data['ontologie_reference_id'],
                status_json,
                prerequis_json,
                data['derniere_connexion']
            )
            )

            return data['id_apprenant']

    def update(self, id_apprenant: int, data: dict) -> bool:
        """Met à jour un apprenant (partiellement ou complètement)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Construction dynamique de la requête UPDATE
            # Seuls les champs non-null sont mis à jour
            fields = []
            values = []

            for key, value in data.items():
                if value is not None:
                    fields.append(f"{key} = ?")
                    # Conversion JSON si nécessaire
                    if isinstance(value, list):
                        value = to_json(value)
                    values.append(value)

            if not fields:
                return False

            values.append(id_apprenant)
            query = f"""UPDATE apprenant SET {
                ', '.join(fields)} WHERE id_apprenant = ?"""

            cursor.execute(query, values)
            return cursor.rowcount > 0


# Instance du repository
repo = LearnerRepository()

# ============================================
# ENDPOINTS CRUD
# ============================================


@router.get("/", response_model=List[Learner])
def list_learners(
    nom: Optional[str] = Query(
        None,
        description="Filtrer par nom d'utilisateur"),
        limit: int = Query(
            100,
            ge=1,
            le=1000,
            description="Nombre maximum de résultats"),
        offset: int = Query(
            0,
            ge=0,
            description="Offset pour la pagination")):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM apprenant WHERE is_active = 1"
        params = []

        if nom:
            query += " AND nom_utilisateur = ?"
            params.append(nom)

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [Learner(**dict(row)) for row in rows]


@router.get("/{id_apprenant}", response_model=Learner)
def get_learner(id_apprenant: int):
    data = repo.get_by_id(id_apprenant)
    if not data:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")
    return Learner(**data)


@router.post("/", response_model=Learner, status_code=201)
def create_learner(learner: LearnerCreate):
    exists = repo.get_by_id(learner.id_apprenant)
    if exists:
        raise HTTPException(
            status_code=400,
            detail=f"""Il existe déjà un apprenant avec l'ID {
                learner.id_apprenant}""")

    try:
        repo.create(learner.model_dump())
        created = repo.get_by_id(learner.id_apprenant)
        return Learner(**created)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id_apprenant}", response_model=Learner)
def update_learner_full(id_apprenant: int, learner: LearnerCreate):
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(status_code=404, detail="L'apprenant n'existe pas")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE apprenant SET
                nom_utilisateur = ?,
                email = ?,
                ontologie_reference_id = ?,
                statuts_actifs_ids = ?,
                codes_prerequis_externes_valides = ?
            WHERE id_apprenant = ?
        """, (
            learner.nom_utilisateur,
            learner.email,
            learner.ontologie_reference_id,
            to_json(learner.statuts_actifs_ids),
            to_json(learner.codes_prerequis_externes_valides),
            id_apprenant
        ))

    updated = repo.get_by_id(id_apprenant)
    return Learner(**updated)


@router.patch("/{id_apprenant}", response_model=Learner)
def update_learner_partial(id_apprenant: int, learner: LearnerUpdate):
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(
            status_code=404,
            detail="L'apprenant n'existe pas"
        )

    update_data = {k: v for k, v in learner.model_dump().items()
                   if v is not None}

    if update_data:
        repo.update(id_apprenant, update_data)

    updated = repo.get_by_id(id_apprenant)
    return Learner(**updated)


@router.delete("/{id_apprenant}", status_code=204)
def delete_learner(id_apprenant: int):
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(
            status_code=404,
            detail="L'apprenant n'existe pas"
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE apprenant SET is_active = 0 WHERE id_apprenant = ?",
            (id_apprenant,)
        )

    return None

# ============================================
# ENDPOINTS : Prérequis Externes
# ============================================


@router.get("/{id_apprenant}/external-prerequisites",
            response_model=List[ExternalPrerequisite])
def get_external_prerequisites(id_apprenant: int):
    # Vérifier que l'apprenant existe
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM external_prerequisite_validation
            WHERE id_apprenant = ?""",
            (id_apprenant,)
        )
        rows = cursor.fetchall()
        return [ExternalPrerequisite(**dict(row)) for row in rows]


@router.post("/{id_apprenant}/external-prerequisites",
             response_model=ExternalPrerequisite, status_code=201)
def add_external_prerequisite(id_apprenant: int,
                              prerequisite: ExternalPrerequisiteCreate):
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    # Vérifier le duplicate AVANT d'ouvrir la transaction
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 1 FROM external_prerequisite_validation
            WHERE id_apprenant = ? AND code_prerequis = ?""",
            (id_apprenant, prerequisite.code_prerequis)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400, detail=f"""Le prérequis '{
                    prerequisite.code_prerequis}' est déjà validé""")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO external_prerequisite_validation
            (id_apprenant, code_prerequis, validated_by, notes)
            VALUES (?, ?, ?, ?)""",
            (id_apprenant,
             prerequisite.code_prerequis,
             prerequisite.validated_by,
             prerequisite.notes))
        cursor.execute(
            """SELECT * FROM external_prerequisite_validation
            WHERE id_apprenant = ? AND code_prerequis = ?""",
            (id_apprenant, prerequisite.code_prerequis)
        )
        created = cursor.fetchone()
        return ExternalPrerequisite(**dict(created))


@router.delete("/{id_apprenant}/external-prerequisites/{code}",
               status_code=204)
def delete_external_prerequisite(id_apprenant: int, code: str):
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    # Vérifier existence AVANT la transaction de suppression
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 1 FROM external_prerequisite_validation
            WHERE id_apprenant = ? AND code_prerequis = ?""",
            (id_apprenant, code)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404,
                                detail=f"Le prérequis '{code}' n'existe pas")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """DELETE FROM external_prerequisite_validation
            WHERE id_apprenant = ? AND code_prerequis = ?""",
            (id_apprenant, code)
        )
    return None

# ============================================
# ENDPOINTS : Statuts d'Apprentissage
# ============================================


@router.get("/{id_apprenant}/learning-status",
            response_model=List[LearningStatus])
def get_learning_status(id_apprenant: int):
    # Vérifier que l'apprenant existe
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM statut_apprentissage WHERE id_apprenant = ?",
            (id_apprenant,)
        )
        rows = cursor.fetchall()

        result = []
        for row in rows:
            data = dict(row)
            # Désérialiser le JSON des tentatives
            data['historique_tentatives_ids'] = from_json(
                data.get('historique_tentatives_ids') or '[]')
            result.append(LearningStatus(**data))

        return result


@router.get("/{id_apprenant}/learning-status/summary",
            response_model=LearningStatusSummary)
def get_learning_status_summary(id_apprenant: int):
    # Vérifier que l'apprenant existe
    exists = repo.get_by_id(id_apprenant)
    if not exists:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM statut_apprentissage WHERE id_apprenant = ?",
            (id_apprenant,)
        )
        rows = cursor.fetchall()
        statuts = [dict(row) for row in rows]

        total = len(statuts)
        maitrise = sum(1 for s in statuts if s['niveau_maitrise'] >= 0.9)
        en_cours = sum(1 for s in statuts if 0 < s['niveau_maitrise'] < 0.9)
        non_commence = sum(1 for s in statuts if s['niveau_maitrise'] == 0)

        taux = round((maitrise / total * 100), 2) if total > 0 else 0.0

        return LearningStatusSummary(
            id_apprenant=id_apprenant,
            total=total,
            maitrise=maitrise,
            en_cours=en_cours,
            non_commence=non_commence,
            taux_maitrise_global=taux
        )

# ============================================
# ENDPOINTS : Ontologie
# ============================================


@router.get("/{id_apprenant}/ontologie", response_model=OntologyReference)
def get_ontologie(id_apprenant: int):
    # Vérifier que l'apprenant existe
    apprenant = repo.get_by_id(id_apprenant)
    if not apprenant:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    # Vérifier qu'il a une ontologie assignée
    if not apprenant['ontologie_reference_id']:
        raise HTTPException(
            status_code=404,
            detail="Cet apprenant n'a pas d'ontologie de référence assignée"
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ontology_reference WHERE id_reference = ?",
            (apprenant['ontologie_reference_id'],)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="L'ontologie référencée n'existe plus en base"
            )

        data = dict(row)
        data['aavs_ids_actifs'] = from_json(
            data.get('aavs_ids_actifs') or '[]')
        return OntologyReference(**data)


@router.post("/{id_apprenant}/ontologie/{id_reference}/switch",
             response_model=OntologySwitchResponse)
def switch_ontologie(id_apprenant: int, id_reference: int):
    # Vérifier que l'apprenant existe
    apprenant = repo.get_by_id(id_apprenant)
    if not apprenant:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    # Vérifier que la nouvelle ontologie existe (hors transaction)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ontology_reference WHERE id_reference = ?",
            (id_reference,)
        )
        nouvelle_ontologie = cursor.fetchone()
        nouvelle_onto_data = dict(
            nouvelle_ontologie) if nouvelle_ontologie else None

    if not nouvelle_onto_data:
        raise HTTPException(
            status_code=404,
            detail=f"L'ontologie {id_reference} n'existe pas")

    # Vérifier compatibilité des prérequis externes (hors transaction)
    codes_valides = from_json(apprenant.get(
        'codes_prerequis_externes_valides') or '[]')
    aavs_ids = from_json(nouvelle_onto_data.get('aavs_ids_actifs') or '[]')

    if aavs_ids:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(aavs_ids))
            cursor.execute(
                f"""SELECT prerequis_externes_codes FROM aav
                WHERE id_aav IN ({placeholders})""",
                aavs_ids)
            aav_rows = cursor.fetchall()

        prerequis_requis = set()
        for aav_row in aav_rows:
            codes = from_json(aav_row['prerequis_externes_codes'] or '[]')
            prerequis_requis.update(codes)

        manquants = prerequis_requis - set(codes_valides)
        if manquants:
            raise HTTPException(
                status_code=400,
                detail=f"""Prérequis externes manquants pour cette ontologie : {
                    list(manquants)}""")

    # Tout est bon : effectuer le changement (hors de tout raise)
    ancienne_ontologie_id = apprenant['ontologie_reference_id']
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE apprenant SET ontologie_reference_id = ?
            WHERE id_apprenant = ?""",
            (id_reference, id_apprenant)
        )

    return OntologySwitchResponse(
        success=True,
        message="Ontologie changée avec succès",
        id_apprenant=id_apprenant,
        ancienne_ontologie_id=ancienne_ontologie_id,
        nouvelle_ontologie_id=id_reference
    )

# ============================================
# ENDPOINT : Progression
# ============================================


@router.get("/{id_apprenant}/progress", response_model=ProgressResponse)
def get_progress(id_apprenant: int):
    # Vérifier que l'apprenant existe
    apprenant = repo.get_by_id(id_apprenant)
    if not apprenant:
        raise HTTPException(status_code=404, detail="Apprenant non trouvé")

    # Vérifier qu'il a une ontologie assignée
    if not apprenant['ontologie_reference_id']:
        raise HTTPException(
            status_code=404,
            detail="Cet apprenant n'a pas d'ontologie de référence assignée"
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Récupérer les AAVs actifs de l'ontologie
        cursor.execute(
            """SELECT aavs_ids_actifs FROM ontology_reference
            WHERE id_reference = ?""",
            (apprenant['ontologie_reference_id'],)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="L'ontologie référencée n'existe plus en base"
            )

        aavs_ids = from_json(dict(row).get('aavs_ids_actifs') or '[]')
        total_aavs = len(aavs_ids)

        if total_aavs == 0:
            return ProgressResponse(
                id_apprenant=id_apprenant,
                ontologie_reference_id=apprenant['ontologie_reference_id'],
                total_aavs=0,
                aavs_maitrise=0,
                taux_progression=0.0
            )

        # Compter combien de ces AAVs sont maîtrisés par l'apprenant
        # est_maitrise est une colonne générée automatiquement (niveau_maitrise
        # >= 0.9)
        placeholders = ','.join('?' * len(aavs_ids))
        cursor.execute(
            f"""
            SELECT COUNT(*) as nb_maitrise
            FROM statut_apprentissage
            WHERE id_apprenant = ?
              AND id_aav_cible IN ({placeholders})
              AND est_maitrise = 1
            """,
            [id_apprenant] + aavs_ids
        )

        result = cursor.fetchone()
        aavs_maitrise = result['nb_maitrise'] if result else 0
        taux = round(aavs_maitrise / total_aavs * 100, 2)

        return ProgressResponse(
            id_apprenant=id_apprenant,
            ontologie_reference_id=apprenant['ontologie_reference_id'],
            total_aavs=total_aavs,
            aavs_maitrise=aavs_maitrise,
            taux_progression=taux
        )
