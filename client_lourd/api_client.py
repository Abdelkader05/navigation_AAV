"""
Client HTTP minimal pour consommer l'API PlatonAAV.
La GUI Flet ne doit pas contenir directement la logique réseau.
"""

from __future__ import annotations

import requests


class APIClient:
    """Client simple pour communiquer avec l'API REST."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.selected_aav: dict | None = None

    def get_aavs(
        self,
        discipline: str | None = None,
        type_aav: str | None = None,
    ) -> list[dict]:
        """Récupère la liste des AAV, avec filtres optionnels."""
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
        """Récupère le détail d'un AAV."""
        response = requests.get(
            f"{self.base_url}/aavs/{id_aav}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    
    def create_aav(self, payload: dict):
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

    def update_aav_prerequis(self, id_aav: int, prerequis_ids: list[int]):
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