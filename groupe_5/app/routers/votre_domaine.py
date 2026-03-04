"""Endpoints du domaine du groupe 5."""

from fastapi import APIRouter

from app.models import MessageResponse

router = APIRouter(tags=["votre_domaine"])


@router.get("/votre-domaine", response_model=MessageResponse)
def get_votre_domaine() -> MessageResponse:
    return MessageResponse(message="Endpoint votre_domaine pret")
