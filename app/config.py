"""Configuration centrale de l'application.

Ce fichier regroupe tous les paramètres globaux utilisés par le projet.
L'idée est simple :
- éviter les "valeurs magiques" écrites en dur un peu partout ;
- pouvoir modifier facilement le comportement de l'application ;
- permettre, plus tard, une configuration via variables d'environnement.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de configuration chargeables depuis l'environnement.

    BaseSettings permet de surcharger ces valeurs via des variables
    d'environnement ou un fichier .env.

    Exemple :
        GROUPE5_DEBUG=true
        GROUPE5_DATABASE_PATH=/tmp/test.db
    """

    # Nom affiché de l'application
    app_name: str = "PlatonAAV Groupe 5 API"

    # Version logique de l'API
    app_version: str = "1.0.0"

    # Mode debug : utile pour le développement
    # En production, cette valeur devrait rester à False
    debug: bool = False

    # Chemin du fichier SQLite utilisé par l'application
    # Par défaut, on place la base à la racine du projet
    database_path: Path = Field(
        default=Path(__file__).resolve().parent.parent / "groupe5.db"
    )

    # Intervalles de révision espacée en jours
    # Exemple : après une réussite, on peut proposer une révision
    # à J+1, puis J+3, puis J+7, etc.
    review_intervals_days: tuple[int, ...] = (1, 3, 7, 14, 30)

    # Seuil à partir duquel un AAV est considéré comme "maîtrisé"
    # Exemple : 0.9 = 90% de maîtrise
    mastery_threshold: float = 0.9

    # Seuil à partir duquel un AAV est considéré comme suffisamment acquis
    # pour servir de base à d'autres AAV ou entrer en révision
    review_threshold: float = 0.8

    # Seuil de succès par défaut pour une tentative / un exercice
    # Exemple : 0.7 = réussite à 70%
    default_success_threshold: float = 0.7

    # Seuil de défaillance utilisé dans la logique de diagnostic :
    # en dessous, un AAV peut être considéré comme cause racine potentielle
    failure_threshold: float = 0.5

    # Configuration de Pydantic Settings :
    # - env_file : charge les variables depuis un fichier .env
    # - env_prefix : toutes les variables doivent commencer par GROUPE5_
    # - case_sensitive : False => pas sensible à la casse
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GROUPE5_",
        case_sensitive=False,
    )


# Instance globale utilisée dans le reste du projet
settings = Settings()