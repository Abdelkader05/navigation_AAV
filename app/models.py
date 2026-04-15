from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Literal
from enum import Enum
from datetime import datetime

# ============================================
# ENUMERATIONS
# ============================================

class TypeEvaluationAAV(str, Enum):
    """Types d'evaluation possibles pour un AAV."""
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
    """Niveaux de difficulte pour les exercices."""
    DEBUTANT = "debutant"
    INTERMEDIAIRE = "intermediaire"
    AVANCE = "avance"

# ============================================
# MODELES DE BASE (Communs a tous les groupes)
# ============================================

class RegleProgression(BaseModel):
    """
    Regles determinant comment un apprenant progresse sur un AAV.

    Exemple:
        - seuil_succes: 0.7 (70% pour reussir)
        - nombre_succes_consecutifs: 3 (3 reussites d'affilee = maitrise)
    """
    seuil_succes: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Score minimum pour considerer une tentative comme reussie"
    )
    maitrise_requise: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Niveau de maitrise a atteindre pour valider l'AAV"
    )
    nombre_succes_consecutifs: int = Field(
        default=1,
        ge=1,
        description="Nombre de reussites consecutives requises"
    )
    nombre_jugements_pairs_requis: int = Field(
        default=3,
        ge=1,
        description="Pour evaluation par les pairs: jugements necessaires"
    )
    tolerance_jugement: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Marge de tolerance pour les evaluations par pairs"
    )

class AAVBase(BaseModel):
    """Champs de base pour un AAV (creation et mise a jour)."""
    nom: str = Field(..., min_length=3, max_length=200, description="Nom technique de l'AAV")
    libelle_integration: str = Field(
        ...,
        min_length=5,
        description="Forme grammaticale pour insertion dans une phrase"
    )
    discipline: str = Field(..., min_length=2, description="Discipline (ex: Mathematiques)")
    enseignement: str = Field(..., description="Enseignement specifique (ex: Algebre)")
    type_aav: TypeAAV
    description_markdown: str = Field(..., min_length=10, description="Description complete")
    prerequis_ids: List[int] = Field(default_factory=list, description="IDs des AAV prerequis")
    ids_exercices: List[int] = Field(default_factory=list, description="IDs des exercices de l'AAV")
    prerequis_externes_codes: List[str] = Field(default_factory=list)
    code_prerequis_interdisciplinaire: Optional[str] = None
    type_evaluation: TypeEvaluationAAV

    @field_validator('libelle_integration')
    @classmethod
    def validate_libelle(cls, v: str) -> str:
        """Verifie que le libelle peut s'integrer dans une phrase."""
        phrase_test = f"Nous allons travailler {v}"
        if len(phrase_test) > 250:
            raise ValueError("Libelle trop long pour une phrase fluide")
        return v

class AAVCreate(AAVBase):
    """Modele pour la creation d'un AAV (POST)."""
    id_aav: int = Field(..., gt=0, description="Identifiant unique de l'AAV")
    regles_progression: RegleProgression = Field(default_factory=RegleProgression)

class AAVUpdate(BaseModel):
    """Modele pour la mise a jour partielle (PATCH). Tous les champs sont optionnels."""
    nom: Optional[str] = Field(None, min_length=3, max_length=200)
    libelle_integration: Optional[str] = None
    description_markdown: Optional[str] = None
    prerequis_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class AAV(AAVBase):
    """Modele complet d'un AAV (reponse API)."""
    id_aav: int
    is_active: bool = True
    version: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        """Configuration Pydantic V2."""
        from_attributes = True

# ============================================
# MODELES POUR LES REPONSES API
# ============================================

class ErrorResponse(BaseModel):
    """Format standard pour les reponses d'erreur."""
    error: str = Field(..., description="Type d'erreur")
    message: str = Field(..., description="Message lisible par l'utilisateur")
    details: Optional[dict] = Field(None, description="Details techniques supplementaires")
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginatedResponse(BaseModel):
    """Format standard pour les reponses paginees."""
    items: List[dict]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_previous: bool

class SuccessResponse(BaseModel):
    """Format standard pour les confirmations de succes."""
    success: bool = True
    message: str
    id: Optional[int] = None
    data: Optional[dict] = None


# ============================================
# MODELES GROUPE 6: REMEDIATION // POST du cahier de charges
# ============================================

class TriggerRemediation(BaseModel):
    """Methode pour declencher une analyse de remediation."""
    id_apprenant: int = Field(..., description="ID de l'apprenant")
    id_aav_source: int = Field(..., description="ID de l'AAV de l'echec")
    score_obtenu: float = Field(..., ge=0.0, le=1.0, description="Score de l'apprenant")
    type_echec: Literal["calcul","comprehension","prerequis_manquant"] = Field(..., description="Detail de l'echec")
    
class GeneratePath(BaseModel):
    """Methode pour generer un parcours personnalise."""
    id_apprenant: int
    id_aav_cible: int
    profondeur_max: int = Field(default=3, ge=1, le=10, description="Profondeur max de l'analyse")
    
class RemediationResponse(BaseModel):
    """Format standard pour la reponse d'une analyse"""
    id_diagnostic: int
    id_apprenant: int
    id_aav_source: int
    aav_defaillants: List[int]
    recommandations: List[dict]
    date_diagnostic: datetime
    
class PathRequest(BaseModel):
    """Methode pour demander l'analyse d'une sequence d'AVV"""
    id_apprenant: int
    chemin_aavs: List[int] = Field(..., description="AVVs a analyser")
    
class ErreurApprenant(BaseModel):
    """Format standard pour la reponse d'une analyse sur le niveau de l'apprenant sur un AVV"""
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


class LearnerBase(BaseModel):
    id_apprenant: int = Field(..., gt=0)
    nom_utilisateur: str = Field(..., min_length=1, description="Nom de l'apprenti")
    email: str = Field(description="E-mail de l'apprenti")
    ontologie_reference_id: Optional[int] = None
    statuts_actifs_ids: List[int] = Field(default_factory=list)
    codes_prerequis_externes_valides: List[str] = Field(default_factory=list)
    date_inscription: Optional[datetime] = None
    derniere_connexion: Optional[datetime] = None
    is_active: bool = True

    @field_validator('email')
    @classmethod
    def test_email_valide(cls, value: str) -> str:
        if '@' not in value or '.' not in value.split('@')[-1]:
            raise ValueError("Invalid email format (supposed to be exemple@xyz.com)")
        return value.lower()

    @field_validator('statuts_actifs_ids', 'codes_prerequis_externes_valides', mode='before')
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


class LearnerCreate(LearnerBase):
    pass


class LearnerUpdate(BaseModel):
    ontologie_reference_id: Optional[int] = None
    statuts_actifs_ids: Optional[List[int]] = None
    codes_prerequis_externes_valides: Optional[List[str]] = None


class Learner(LearnerBase):
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
