from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.database import DatabaseError, init_database
from app.routers import aavs
from app.routers import navigation
from app.routers import remediation
from app.routers import learners
from app.routers import attempts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gere le demarrage et l'arret de l'application."""
    # On initialise la base au lancement pour que les routes puissent tourner direct.
    print("Initialisation de la base de donnees...")
    init_database()
    yield
    # Ici on n'a pas de gros nettoyage, juste un message de fin.
    print("Arret du serveur")


app = FastAPI(
    title="PlatonAAV API",
    description="""
    API REST pour la gestion des Acquis d'Apprentissage Vises (AAV).

    ## Groupes

    * **AAVs** - Gestion des acquis (Groupe 1)
    * **Learners** - Gestion des apprenants (Groupe 2)
    * etc.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# On branche ici tous les routers utiles de l'appli.
app.include_router(aavs.router)
app.include_router(navigation.router)
app.include_router(remediation.router)
app.include_router(learners.router)
app.include_router(attempts.router)


@app.get("/")
def root():
    """Route simple pour verifier que l'API repond."""
    return {
        "message": "Bienvenue sur l'API PlatonAAV",
        "documentation": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Petit check rapide pour voir si le serveur tourne."""
    return {"status": "healthy", "database": "connected"}


# ============================================
# GESTION DES ERREURS
# ============================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Gere les erreurs HTTP classiques comme 404 ou 400."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Gere les erreurs de validation des donnees envoyees a l'API."""
    errors = []
    for error in exc.errors():
        # On reformate un peu les erreurs pour qu'elles soient plus lisibles cote client.
        errors.append({
            "field": " ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Les donnees fournies sont invalides",
            "details": errors,
            "path": str(request.url)
        }
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Gere les erreurs qui viennent de la base de donnees."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "database_error",
            "message": "Une erreur est survenue lors de l'acces aux donnees",
            "details": {"error": str(exc)},
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Attrape les erreurs non prevues pour eviter de casser l'API."""
    # On n'envoie pas le detail brut de l'erreur au client.
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Une erreur interne est survenue",
            "path": str(request.url)
        }
    )
