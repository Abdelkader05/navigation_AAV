"""Configuration de l'application."""

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Groupe 5 API"
    debug: bool = True


settings = Settings()
