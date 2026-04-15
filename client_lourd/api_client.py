from __future__ import annotations

import requests


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        """Prepare l'URL de base du backend."""
        # On enleve le slash final pour eviter les doublons dans les routes.
        self.base_url = base_url.rstrip("/")

    def get_aavs(
        self,
        discipline: str | None = None,
        type_aav: str | None = None,
    ) -> list[dict]:
        """Recupere la liste des AAV avec filtres optionnels."""
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
        """Recupere le detail d'un AAV."""
        response = requests.get(
            f"{self.base_url}/aavs/{id_aav}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def create_aav(self, payload: dict) -> dict:
        """Envoie un nouvel AAV a l'API."""
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
        """Modifie seulement les prerequis d'un AAV."""
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

    def get_learners(self) -> list[dict]:
        """Charge la liste des apprenants."""
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
        """Charge le resume global d'un apprenant."""
        response = requests.get(
            f"{self.base_url}/learners/{id_apprenant}/learning-status/summary",
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()

    def get_learning_status(self, id_apprenant: int) -> list[dict]:
        """Charge le detail des statuts d'apprentissage d'un apprenant."""
        response = requests.get(
            f"{self.base_url}/learners/{id_apprenant}/learning-status",
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()

    def create_attempt(self, payload: dict) -> dict:
        """Cree une tentative avant de la traiter."""
        response = requests.post(
            f"{self.base_url}/attempts",
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

    def process_attempt(self, attempt_id: int) -> dict:
        """Lance le traitement de la tentative creee juste avant."""
        response = requests.post(
            f"{self.base_url}/attempts/{attempt_id}/process",
            timeout=10,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"{response.status_code} - {detail}")

        return response.json()
