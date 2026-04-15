"""
Client HTTP minimal pour communiquer avec l'API PlatonAAV.
Sépare la logique réseau de l'interface graphique.
"""

import requests


class APIClient:
    """Petit client pour consommer l'API REST."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def get_aavs(self, discipline: str | None = None, type_aav: str | None = None):
        """
        Récupère la liste des AAV depuis l'API.
        Permet de filtrer par discipline et type.
        """
        params = {}

        if discipline:
            params["discipline"] = discipline
        if type_aav:
            params["type_aav"] = type_aav

        response = requests.get(f"{self.base_url}/aavs/", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_aav(self, id_aav: int):
        """Récupère un AAV précis à partir de son identifiant."""
        response = requests.get(f"{self.base_url}/aavs/{id_aav}", timeout=10)
        response.raise_for_status()
        return response.json()