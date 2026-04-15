
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Literal
from enum import Enum
from datetime import datetime

# ============================================
# ÉNUMÉRATIONS
# ============================================

class TypeEvaluationAAV(str, Enum):
    """Types d'évaluation possibles pour un AAV."""
    HUMAINE = "Humaine"
    CALCUL = "Calcul Automatisé"
    CHUTE = "Compréhension par Chute"
    INVENTION = "Validation par Invention"
    CRITIQUE = "Exercice de Critique"
    EVALUATION_PAIRS = "Évaluation par les Pairs"
    EVALUATION_AGREGEE = "Agrégation (Composite)"

class TypeAAV(str, Enum):
    """Types d'AAV possibles."""
    ATOMIQUE = "Atomique"
    COMPOSITE = "Composite (Chapitre)"

class NiveauDifficulte(str, Enum):
    """Niveaux de difficulté pour les exercices."""
    DEBUTANT = "debutant"
    INTERMEDIAIRE = "intermediaire"
    AVANCE = "avance"

# ============================================
# MODÈLES DE BASE (Communs à tous les groupes)
# ============================================

class RegleProgression(BaseModel):
    """
    Règles déterminant comment un apprenant progresse sur un AAV.

    Exemple:
        - seuil_succes: 0.7 (70% pour réussir)
        - nombre_succes_consecutifs: 3 (3 réussites d'affilée = maîtrise)
    """
    seuil_succes: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Score minimum pour considérer une tentative comme réussie"
    )
    maitrise_requise: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Niveau de maîtrise à atteindre pour valider l'AAV"
    )
    nombre_succes_consecutifs: int = Field(
        default=1,
        ge=1,
        description="Nombre de réussites consécutives requises"
    )
    nombre_jugements_pairs_requis: int = Field(
        default=3,
        ge=1,
        description="Pour évaluation par les pairs: jugements nécessaires"
    )
    tolerance_jugement: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Marge de tolérance pour les évaluations par pairs"
    )

class AAVBase(BaseModel):
    """Champs de base pour un AAV (création et mise à jour)."""
    nom: str = Field(..., min_length=3, max_length=200, description="Nom technique de l'AAV")
    libelle_integration: str = Field(
        ...,
        min_length=5,
        description="Forme grammaticale pour insertion dans une phrase"
    )
    discipline: str = Field(..., min_length=2, description="Discipline (ex: Mathématiques)")
    enseignement: str = Field(..., description="Enseignement spécifique (ex: Algèbre)")
    type_aav: TypeAAV
    description_markdown: str = Field(..., min_length=10, description="Description complète")
    prerequis_ids: List[int] = Field(default_factory=list, description="IDs des AAV prérequis")
    prerequis_externes_codes: List[str] = Field(default_factory=list)
    code_prerequis_interdisciplinaire: Optional[str] = None
    type_evaluation: TypeEvaluationAAV

    @field_validator('libelle_integration')
    @classmethod
    def validate_libelle(cls, v: str) -> str:
        """Vérifie que le libellé peut s'intégrer dans une phrase."""
        phrase_test = f"Nous allons travailler {v}"
        if len(phrase_test) > 250:
            raise ValueError("Libellé trop long pour une phrase fluide")
        return v

class AAVCreate(AAVBase):
    """Modèle pour la création d'un AAV (POST)."""
    id_aav: int = Field(..., gt=0, description="Identifiant unique de l'AAV")
    regles_progression: RegleProgression = Field(default_factory=RegleProgression)

class AAVUpdate(BaseModel):
    """Modèle pour la mise à jour partielle (PATCH). Tous les champs sont optionnels."""
    nom: Optional[str] = Field(None, min_length=3, max_length=200)
    libelle_integration: Optional[str] = None
    description_markdown: Optional[str] = None
    prerequis_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class AAV(AAVBase):
    """Modèle complet d'un AAV (réponse API)."""
    id_aav: int
    is_active: bool = True
    version: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        """Configuration Pydantic V2."""
        from_attributes = True  # Permet de créer depuis un objet SQLAlchemy/dict

# ============================================
# MODÈLES POUR LES RÉPONSES API
# ============================================

class ErrorResponse(BaseModel):
    """Format standard pour les réponses d'erreur."""
    error: str = Field(..., description="Type d'erreur")
    message: str = Field(..., description="Message lisible par l'utilisateur")
    details: Optional[dict] = Field(None, description="Détails techniques supplémentaires")
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginatedResponse(BaseModel):
    """Format standard pour les réponses paginées."""
    items: List[dict]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_previous: bool

class SuccessResponse(BaseModel):
    """Format standard pour les confirmations de succès."""
    success: bool = True
    message: str
    id: Optional[int] = None
    data: Optional[dict] = None


# ============================================
# MODÈLES GROUPE 6: REMÉDIATION // POST du cahier de charges
# ============================================

class TriggerRemediation(BaseModel):
    """Méthode pour déclencher une analyse de remédiation."""
    id_apprenant: int = Field(..., description="ID de l'apprenant")
    id_aav_source: int = Field(..., description="ID de l'AAV de l'échec")
    score_obtenu: float = Field(..., ge=0.0, le=1.0, description="Score de l'apprenant")
    type_echec: Literal["calcul","comprehension","prerequis_manquant"] = Field(..., description="Détail de l'échec")
    
class GeneratePath(BaseModel):
    """Méthode pour générer un parcours personnalisé."""
    id_apprenant: int
    id_aav_cible: int
    profondeur_max: int = Field(default=3, ge=1, le=10, description="Profondeur max de l'analyse")
    
class RemediationResponse(BaseModel):
    """Format standard pour la réponse d'une analyse"""
    id_diagnostic: int
    id_apprenant: int
    id_aav_source: int
    aav_defaillants: List[int]
    recommandations: List[dict]
    date_diagnostic: datetime
    
class PathRequest(BaseModel):
    """Méthode pour demander l'analyse d'une séquence d'AVV"""
    id_apprenant: int
    chemin_aavs: List[int] = Field(..., description="AVVs à analyser")
    
class ErreurApprenant(BaseModel):
    """Format standard pour la réponse d'une analyse sur le niveau de l'apprenant sur un AVV"""
    id_aav: int
    maitrise: float
    reussi: bool
    
class DiagnosticRemediationRead(BaseModel):
    id_diagnostic: int
    id_apprenant: int
    id_aav_source: int
    aav_racines_defaillants: List[int]
    score_obtenu: Optional[float] = None
    date_diagnostic: datetime
    profondeur_analyse: Optional[int] = None
    recommandations: List[dict]

    class Config:
        from_attributes = True




class LearnerBase(BaseModel):  # ?voir quoi retirer
    id_apprenant: int = Field(..., gt=0)
    nom_utilisateur: str = Field(..., min_length=1,
                                 description="Nom de l'apprenti")
    email: str = Field(description="E-mail de l'apprenti")
    # Car on veux pouvoir accepter None
    ontologie_reference_id: Optional[int] = None
    statuts_actifs_ids: List[int] = Field(default_factory=list)
    codes_prerequis_externes_valides: List[str] = Field(default_factory=list)
    date_inscription: Optional[datetime] = None
    derniere_connexion: Optional[datetime] = None
    is_active: bool = True  # on met a True direct et on changera au cas ou

    @field_validator('email')
    @classmethod
    def test_email_valide(cls, value: str) -> str:
        if '@' not in value or '.' not in value.split(
                '@')[-1]:  # comme ça on autorise les .fr .org etc
            raise ValueError(
                "Invalid email format (supposed to be exemple@xyz.com)")
        return value.lower()

    @field_validator('statuts_actifs_ids',
                     'codes_prerequis_externes_valides',
                     mode='before')
    @classmethod
    def parse_json_list(cls, v):
        """Convertit automatiquement les strings JSON en listes."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except BaseException:
                return []
        return v or []


class LearnerCreate(LearnerBase):  # ? rajouter les choses retirées
    pass


class LearnerUpdate(BaseModel):  # Maintenant on est convaincu
    ontologie_reference_id: Optional[int] = None
    statuts_actifs_ids: Optional[List[int]] = None
    codes_prerequis_externes_valides: Optional[List[str]] = None


class Learner(LearnerBase):  # ? a rajouter
    model_config = ConfigDict(from_attributes=True)


class LearningStatus(BaseModel):
    id: int
    id_apprenant: int
    id_aav_cible: int
    niveau_maitrise: float
    historique_tentatives_ids: List[int] = Field(default_factory=list)
    date_debut_apprentissage: Optional[datetime] = None
    date_derniere_session: Optional[datetime] = None
    est_maitrise: bool = False

    model_config = ConfigDict(from_attributes=True)


class LearningStatusSummary(BaseModel):
    id_apprenant: int
    total: int
    maitrise: int
    en_cours: int
    non_commence: int
    taux_maitrise_global: float


class ExternalPrerequisiteBase(BaseModel):
    code_prerequis: str = Field(..., min_length=1)
    validated_by: Optional[str] = None
    notes: Optional[str] = None


class ExternalPrerequisiteCreate(ExternalPrerequisiteBase):
    pass


class ExternalPrerequisite(ExternalPrerequisiteBase):
    id_apprenant: int
    date_validation: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OntologyReference(BaseModel):
    id_reference: int
    discipline: str
    aavs_ids_actifs: List[int] = Field(default_factory=list)
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OntologySwitchResponse(BaseModel):
    success: bool
    message: str
    id_apprenant: int
    ancienne_ontologie_id: Optional[int] = None
    nouvelle_ontologie_id: int


class ProgressResponse(BaseModel):
    id_apprenant: int
    ontologie_reference_id: int
    total_aavs: int
    aavs_maitrise: int
    taux_progression: float


class TentativeBase(BaseModel):
    id_exercice_ou_evenement: int
    id_apprenant: int
    id_aav_cible: int
    score_obtenu: float = Field(..., ge=0.0, le=1.0)
    est_valide: bool = False
    temps_resolution_secondes: Optional[int] = None
    metadata: Optional[dict] = None


class TentativeCreate(TentativeBase):
    pass


class Tentative(TentativeBase):
    id: int
    date_tentative: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Process(BaseModel):
    tentative_id: int
    id_apprenant: int
    id_aav_cible: int
    ancien_niveau: float
    nouveau_niveau: float
    est_maitrise: bool
    message: str
