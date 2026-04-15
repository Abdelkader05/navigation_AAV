from __future__ import annotations

import sqlite3
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.database import from_json, get_db_connection, to_json
from app.maitrise import calculer_maitrise, message
from app.models import Process, Tentative, TentativeCreate

router = APIRouter(tags=["Tentatives"])


def row_to_tentative(row: sqlite3.Row) -> Tentative:
    # conversion sqlite -> modèle
    data = dict(row)
    data["est_valide"] = (data.get("est_valide", 0) == 1)
    meta = data.get("metadata")
    data["metadata"] = from_json(meta) if meta else None
    return Tentative(**data)


@router.get("/attempts", response_model=List[Tentative])
def list_attempts(
    id_apprenant: Optional[int] = None,
    id_aav_cible: Optional[int] = None,
    est_valide: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
):
    # liste simple des tentatives
    query = "SELECT * FROM tentative"
    where = []
    params = []

    if id_apprenant is not None:
        where.append("id_apprenant = ?")
        params.append(id_apprenant)

    if id_aav_cible is not None:
        where.append("id_aav_cible = ?")
        params.append(id_aav_cible)

    if est_valide is not None:
        where.append("est_valide = ?")
        params.append(1 if est_valide else 0)

    if where:
        query += " WHERE " + " AND ".join(where)

    query += " ORDER BY date_tentative DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

    return [row_to_tentative(r) for r in rows]


@router.get("/attempts/{id}", response_model=Tentative)
def get_attempt(id: int):
    # une tentative
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tentative WHERE id = ?", (id,))
        row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Tentative introuvable: id={id}")

    return row_to_tentative(row)


@router.post("/attempts", response_model=Tentative, status_code=201)
def create_attempt(payload: TentativeCreate):
    # étape 1
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
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
        new_id = cur.lastrowid

        cur.execute("SELECT * FROM tentative WHERE id = ?", (new_id,))
        row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="Tentative créée mais introuvable")

    return row_to_tentative(row)


@router.delete("/attempts/{id}", status_code=204)
def delete_attempt(id: int):
    # si on veut supprimer
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tentative WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Tentative introuvable: id={id}")
    return


@router.post("/attempts/{id}/process", response_model=Process)
def process_attempt(id: int):
    # étape 2
    SEUIL_SUCCES = 0.9
    N_SUCCES_CONSEC = 5

    with get_db_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT * FROM tentative WHERE id = ?", (id,))
        attempt = cur.fetchone()
        if attempt is None:
            raise HTTPException(status_code=404, detail=f"Tentative introuvable: id={id}")

        id_apprenant = attempt["id_apprenant"]
        id_aav_cible = attempt["id_aav_cible"]

        # on regarde si le statut existe déjà
        cur.execute(
            "SELECT * FROM statut_apprentissage WHERE id_apprenant = ? AND id_aav_cible = ?",
            (id_apprenant, id_aav_cible),
        )
        statut = cur.fetchone()

        if statut is None:
            cur.execute(
                """
                INSERT INTO statut_apprentissage (id_apprenant, id_aav_cible, niveau_maitrise, historique_tentatives_ids)
                VALUES (?, ?, 0.0, ?)
                """,
                (id_apprenant, id_aav_cible, to_json([])),
            )
            cur.execute(
                "SELECT * FROM statut_apprentissage WHERE id_apprenant = ? AND id_aav_cible = ?",
                (id_apprenant, id_aav_cible),
            )
            statut = cur.fetchone()

        ancien_niveau = float(statut["niveau_maitrise"] or 0.0)

        # on garde l'id de la tentative dans l'historique
        hist_raw = statut["historique_tentatives_ids"]
        hist = from_json(hist_raw) if hist_raw else []
        if id not in hist:
            hist.append(id)

        # on reprend tous les scores pour recalculer
        cur.execute(
            """
            SELECT score_obtenu
            FROM tentative
            WHERE id_apprenant = ? AND id_aav_cible = ?
            ORDER BY date_tentative ASC, id ASC
            """,
            (id_apprenant, id_aav_cible),
        )
        scores = [float(r["score_obtenu"]) for r in cur.fetchall()]

        nouveau_niveau = calculer_maitrise(scores, SEUIL_SUCCES, N_SUCCES_CONSEC)
        est_maitrise = nouveau_niveau >= 1.0
        msg = message(ancien_niveau, nouveau_niveau, est_maitrise, N_SUCCES_CONSEC)

        # update du statut
        cur.execute(
            """
            UPDATE statut_apprentissage
            SET niveau_maitrise = ?,
                historique_tentatives_ids = ?,
                date_derniere_session = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (nouveau_niveau, to_json(hist), statut["id"]),
        )

    return Process(
        tentative_id=id,
        id_apprenant=id_apprenant,
        id_aav_cible=id_aav_cible,
        ancien_niveau=ancien_niveau,
        nouveau_niveau=nouveau_niveau,
        est_maitrise=est_maitrise,
        message=msg,
    )
