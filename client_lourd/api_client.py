from __future__ import annotations

import requests


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    # =========================
    # PHASE 1 / 2 : AAV
    # =========================

    def get_aavs(
        self,
        discipline: str | None = None,
        type_aav: str | None = None,
    ) -> list[dict]:
        params: dict[str, str] = {}

        if discipline:
            params["discipline"] = discipline
        if type_aav:
            params["type_aav"] = type_aav

        response = requests.get(
            f"{self.base_url}/aavs/",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_aav(self, id_aav: int) -> dict:
        response = requests.get(
            f"{self.base_url}/aavs/{id_aav}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def create_aav(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/aavs/",
            json=payload,
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()

    def update_aav_prerequis(self, id_aav: int, prerequis_ids: list[int]) -> dict:
        response = requests.patch(
            f"{self.base_url}/aavs/{id_aav}",
            json={"prerequis_ids": prerequis_ids},
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()

    # =========================
    # PHASE 3 : APPRENANT
    # =========================

    def get_learners(self) -> list[dict]:
        """
        Suppose une route GET /learners/
        qui renvoie une liste d'apprenants.
        """
        response = requests.get(
            f"{self.base_url}/learners/",
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()

    def get_learner_summary(self, id_apprenant: int) -> dict:
        """
        Suppose une route GET /learners/{id}/summary
        qui renvoie par exemple :
        {
            "id_apprenant": 1,
            "nom_utilisateur": "alice",
            "niveau_global": 0.67,
            "nombre_statuts": 12
        }
        """
        response = requests.get(
            f"{self.base_url}/learners/{id_apprenant}/summary",
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()

    def simulate_tentative(self, payload: dict) -> dict:
        """
        Suppose une route POST /tentatives/simulate
        avec un payload du style :
        {
            "id_apprenant": 1,
            "id_aav_cible": 2,
            "id_exercice_ou_evenement": 1001,
            "score_obtenu": 0.75
        }
        """
        response = requests.post(
            f"{self.base_url}/tentatives/simulate",
            json=payload,
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()