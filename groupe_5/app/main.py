"""Point d'entree FastAPI."""

from fastapi import FastAPI

from app.routers.votre_domaine import router as votre_domaine_router

app = FastAPI(title="Groupe 5 API")
app.include_router(votre_domaine_router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
