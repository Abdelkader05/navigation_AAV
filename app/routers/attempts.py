from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException

from app.database import from_json, get_db_connection, to_json
from app.models import Process, Tentative, TentativeCreate

router = APIRouter(tags=["Tentatives"])


def row_to_tentative(row: sqlite3.Row) -> Tentative:
    data = dict(row)
    data["est_valide"] = bool(data.get("est_valide", 0))
    meta = data.get("metadata")
    data["metadata"] = from_json(meta) if meta else None
    return Tentative(**data)


def calculer_maitrise(scores: list[float], seuil_succes: float = 0.9, succes_consecutifs: int = 5) -> float:
    if not scores:
        return 0.0

    succes = 0
    for score in reversed(scores):
        if score >= seuil_succes:
            succes += 1
        else:
            break

    return min(1.0, succes / succes_consecutifs)


def build_process_message(ancien: float, nouveau: float) -> str:
    if nouveau >= 1.0:
        return "AAV maitrise apres traitement de la tentative."
    if nouveau > ancien:
        return "La tentative a fait progresser le niveau de maitrise."
    if nouveau == ancien:
        return "La tentative n'a pas modifie le niveau de maitrise."
    return "Le niveau de maitrise a baisse apres traitement de la tentative."


@router.post("/attempts", response_model=Tentative, status_code=201)
def create_attempt(payload: TentativeCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tentative (
                id_exercice_ou_evenement,
                id_apprenant,
                id_aav_cible,
                score_obtenu,
                est_valide,
                temps_resolution_secondes,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.id_exercice_ou_evenement,
                payload.id_apprenant,
                payload.id_aav_cible,
                payload.score_obtenu,
                1 if payload.est_valide else 0,
                payload.temps_resolution_secondes,
                to_json(payload.metadata) if payload.metadata is not None else None,
            ),
        )
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tentative WHERE id = ?", (new_id,))
        row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="Tentative creee mais introuvable")

    return row_to_tentative(row)


@router.post("/attempts/{attempt_id}/process", response_model=Process)
def process_attempt(attempt_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tentative WHERE id = ?", (attempt_id,))
        attempt = cursor.fetchone()
        if attempt is None:
            raise HTTPException(status_code=404, detail=f"Tentative introuvable: id={attempt_id}")

        id_apprenant = attempt["id_apprenant"]
        id_aav_cible = attempt["id_aav_cible"]

        cursor.execute(
            """
            SELECT * FROM statut_apprentissage
            WHERE id_apprenant = ? AND id_aav_cible = ?
            """,
            (id_apprenant, id_aav_cible),
        )
        statut = cursor.fetchone()

        if statut is None:
            cursor.execute(
                """
                INSERT INTO statut_apprentissage (
                    id_apprenant,
                    id_aav_cible,
                    niveau_maitrise,
                    historique_tentatives_ids
                ) VALUES (?, ?, 0.0, ?)
                """,
                (id_apprenant, id_aav_cible, to_json([])),
            )
            cursor.execute(
                """
                SELECT * FROM statut_apprentissage
                WHERE id_apprenant = ? AND id_aav_cible = ?
                """,
                (id_apprenant, id_aav_cible),
            )
            statut = cursor.fetchone()

        ancien_niveau = float(statut["niveau_maitrise"] or 0.0)
        historique = from_json(statut["historique_tentatives_ids"]) if statut["historique_tentatives_ids"] else []
        if attempt_id not in historique:
            historique.append(attempt_id)

        cursor.execute(
            """
            SELECT score_obtenu
            FROM tentative
            WHERE id_apprenant = ? AND id_aav_cible = ?
            ORDER BY date_tentative ASC, id ASC
            """,
            (id_apprenant, id_aav_cible),
        )
        scores = [float(row["score_obtenu"]) for row in cursor.fetchall()]
        nouveau_niveau = calculer_maitrise(scores)
        est_maitrise = nouveau_niveau >= 1.0

        cursor.execute(
            """
            UPDATE statut_apprentissage
            SET niveau_maitrise = ?,
                historique_tentatives_ids = ?,
                date_derniere_session = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (nouveau_niveau, to_json(historique), statut["id"]),
        )

    return Process(
        tentative_id=attempt_id,
        id_apprenant=id_apprenant,
        id_aav_cible=id_aav_cible,
        ancien_niveau=ancien_niveau,
        nouveau_niveau=nouveau_niveau,
        est_maitrise=est_maitrise,
        message=build_process_message(ancien_niveau, nouveau_niveau),
    )
