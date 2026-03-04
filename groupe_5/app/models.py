"""Modeles Pydantic."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str
