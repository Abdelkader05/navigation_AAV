"""
Tests d'intégration complets pour l'API PlatonAAV.

But :
- charger une vraie base SQLite temporaire ;
- importer le dump SQL donnees_test.sql ;
- tester les routes AAV, Navigation et Remediation ;
- éviter d'utiliser la vraie base du projet.

Pré-requis :
- le fichier donnees_test.sql doit être accessible depuis le projet ;
- les routes doivent être bien incluses dans app.main ;
- pytest doit être installé.

Lancement :
    pytest -v tests/test_full_api.py
ou
    pytest -v
"""

from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

import app.database as db_module
import app.config as config_module
from app.main import app
from app.database import init_database, get_db_connection
from app.config import settings


# -------------------------------------------------------------------
# CLIENT HTTP DE TEST
# -------------------------------------------------------------------

client = TestClient(app)


# -------------------------------------------------------------------
# OUTILS
# -------------------------------------------------------------------

def find_sql_dump() -> Path:
    """
    Cherche le fichier donnees_test.sql à plusieurs endroits probables.

    Si ton projet a une autre arborescence, ajoute simplement un chemin ici.
    """
    path = Path("RessourcesCommunes/donnees_test.sql")

    if path.exists():
            return path.resolve()

    raise FileNotFoundError(
        "Impossible de trouver donnees_test.sql. "
        "Place le fichier à la racine du projet ou adapte la fonction find_sql_dump()."
    )


def load_sql_dump(sql_path: Path) -> None:
    """
    Charge le dump SQL complet dans la base de test.
    """
    sql_script = sql_path.read_text(encoding="utf-8")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(sql_script)


def fetch_one_value(query: str, params: tuple = ()):
    """
    Exécute une requête SQL et retourne la première colonne du premier résultat.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return None if row is None else row[0]


def get_any_user_id() -> int:
    """
    Retourne l'identifiant d'un apprenant quelconque existant dans la base.
    """
    user_id = fetch_one_value(
        "SELECT id_apprenant FROM apprenant ORDER BY id_apprenant LIMIT 1"
    )
    assert user_id is not None, "Aucun apprenant trouvé dans la base."
    return int(user_id)


def get_user_with_status() -> int:
    """
    Retourne un apprenant ayant au moins un statut d'apprentissage.
    Utile pour les routes de navigation et d'analyse.
    """
    user_id = fetch_one_value(
        """
        SELECT DISTINCT id_apprenant
        FROM statut_apprentissage
        ORDER BY id_apprenant
        LIMIT 1
        """
    )
    if user_id is not None:
        return int(user_id)
    return get_any_user_id()


def get_user_with_diagnostics() -> int:
    """
    Retourne un apprenant ayant déjà au moins un diagnostic.
    Utile pour les routes GET /learners/{id}/diagnostics, tree, activities, etc.
    """
    user_id = fetch_one_value(
        """
        SELECT DISTINCT id_apprenant
        FROM diagnostic_remediation
        ORDER BY id_apprenant
        LIMIT 1
        """
    )
    if user_id is not None:
        return int(user_id)
    return get_user_with_status()


def get_user_with_tentatives() -> int:
    """
    Retourne un apprenant ayant au moins une tentative.
    """
    user_id = fetch_one_value(
        """
        SELECT DISTINCT id_apprenant
        FROM tentative
        ORDER BY id_apprenant
        LIMIT 1
        """
    )
    if user_id is not None:
        return int(user_id)
    return get_user_with_status()


def get_any_active_aav_id() -> int:
    """
    Retourne l'ID d'un AAV actif quelconque.
    """
    aav_id = fetch_one_value(
        "SELECT id_aav FROM aav WHERE is_active = 1 ORDER BY id_aav LIMIT 1"
    )
    assert aav_id is not None, "Aucun AAV actif trouvé dans la base de test."
    return int(aav_id)


def get_failed_or_weak_aav_for_learner(id_apprenant: int) -> int:
    """
    Cherche un AAV problématique pour un apprenant :
    - d'abord un statut avec faible maîtrise ;
    - sinon un AAV vu dans une tentative ;
    - sinon un AAV actif quelconque.

    Cela permet d'appeler POST /diagnostics/remediation de façon robuste.
    """
    weak_aav = fetch_one_value(
        """
        SELECT id_aav_cible
        FROM statut_apprentissage
        WHERE id_apprenant = ?
          AND niveau_maitrise < ?
        ORDER BY niveau_maitrise ASC
        LIMIT 1
        """,
        (id_apprenant, settings.review_threshold),
    )
    if weak_aav is not None:
        return int(weak_aav)

    tried_aav = fetch_one_value(
        """
        SELECT id_aav_cible
        FROM tentative
        WHERE id_apprenant = ?
        ORDER BY date_tentative DESC
        LIMIT 1
        """,
        (id_apprenant,),
    )
    if tried_aav is not None:
        return int(tried_aav)

    return get_any_active_aav_id()


def get_existing_diagnostic_id_for_learner(id_apprenant: int):
    """
    Retourne un diagnostic déjà présent dans le dump SQL pour un apprenant.
    """
    return fetch_one_value(
        """
        SELECT id_diagnostic
        FROM diagnostic_remediation
        WHERE id_apprenant = ?
        ORDER BY date_diagnostic DESC
        LIMIT 1
        """,
        (id_apprenant,),
    )


# -------------------------------------------------------------------
# FIXTURE : BASE DE TEST TEMPORAIRE
# -------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_test_database(tmp_path, monkeypatch):
    """
    Avant chaque test :
    - on crée une base SQLite temporaire ;
    - on force le projet à l'utiliser ;
    - on crée le schéma ;
    - on charge le dump SQL.

    Après chaque test :
    - pytest détruit automatiquement tmp_path.
    """
    test_db_path = tmp_path / "platonAAV_test.db"

    # On patch à la fois le module de config et le module database
    # pour être sûr que toute l'application pointe vers la bonne base.
    monkeypatch.setattr(config_module.settings, "database_path", test_db_path)
    monkeypatch.setattr(db_module, "DATABASE_PATH", test_db_path)

    # Création des tables
    init_database()

    # Chargement du dump SQL complet
    sql_dump_path = find_sql_dump()
    load_sql_dump(sql_dump_path)

    yield


# -------------------------------------------------------------------
# TESTS DE BASE : ROOT / HEALTH
# -------------------------------------------------------------------

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "documentation" in data
    assert "version" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# -------------------------------------------------------------------
# TESTS AAV
# -------------------------------------------------------------------

def test_list_aavs_returns_non_empty_list():
    response = client.get("/aavs/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_existing_aav():
    aav_id = get_any_active_aav_id()

    response = client.get(f"/aavs/{aav_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id_aav"] == aav_id
    assert "nom" in data
    assert "discipline" in data
    assert "prerequis_ids" in data


def test_get_unknown_aav_returns_404():
    response = client.get("/aavs/999999")
    assert response.status_code == 404


# -------------------------------------------------------------------
# TESTS NAVIGATION
# -------------------------------------------------------------------

def test_navigation_dashboard_alice():
    """
    Alice est décrite comme débutante dans le dump.
    On vérifie surtout que le dashboard répond correctement.
    """
    alice_id = get_user_with_status()

    response = client.get(f"/navigation/{alice_id}/dashboard")
    assert response.status_code == 200

    data = response.json()
    assert "accessible_count" in data
    assert "in_progress_count" in data
    assert "blocked_count" in data
    assert "reviewable_count" in data
    assert "recommended_next" in data


def test_navigation_in_progress_bob():
    """
    Bob est censé être en progression.
    On s'attend à une route valide et à une liste.
    """
    bob_id = get_user_with_status()

    response = client.get(f"/navigation/{bob_id}/in-progress")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_navigation_blocked_david():
    """
    Teste la route des AAV bloqués pour un apprenant ayant des statuts.
    """
    user_id = get_user_with_status()

    response = client.get(f"/navigation/{user_id}/blocked")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if data:
        assert "id_aav" in data[0]
        assert "blocked_prerequisites" in data[0]


def test_navigation_reviewable_eve():
    """
    Eve est décrite comme ayant des maîtrises anciennes à réviser.
    """
    eve_id = get_user_with_status()

    response = client.get(f"/navigation/{eve_id}/reviewable")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_navigation_accessible_returns_list():
    user_id = get_user_with_status()

    response = client.get(f"/navigation/{user_id}/accessible")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_navigation_all_returns_list():
    charlie_id = get_user_with_status()

    response = client.get(f"/navigation/{charlie_id}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


# -------------------------------------------------------------------
# TESTS REMEDIATION : LECTURE DE L'EXISTANT
# -------------------------------------------------------------------

def test_get_learner_diagnostics_history():
    david_id = get_user_with_diagnostics()

    response = client.get(f"/learners/{david_id}/diagnostics")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if data:
        diag = data[0]
        assert "id_diagnostic" in diag
        assert "id_apprenant" in diag
        assert "id_aav_source" in diag
        assert "aav_racines_defaillants" in diag


def test_get_existing_diagnostic_by_id():
    user_id = get_user_with_diagnostics()
    diagnostic_id = get_existing_diagnostic_id_for_learner(user_id)

    if diagnostic_id is None:
        pytest.skip("Aucun diagnostic existant dans le dump SQL.")

    response = client.get(f"/diagnostics/{diagnostic_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id_diagnostic"] == diagnostic_id
    assert "recommandations" in data


def test_get_unknown_diagnostic_returns_404():
    response = client.get("/diagnostics/999999")
    assert response.status_code == 404


def test_get_diagnostic_tree():
    user_id = get_user_with_diagnostics()
    diagnostic_id = get_existing_diagnostic_id_for_learner(user_id)

    if diagnostic_id is None:
        pytest.skip("Aucun diagnostic existant pour David dans le dump SQL.")

    response = client.get(f"/diagnostics/{diagnostic_id}/tree")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "nodes" in data or "links" in data or "edges" in data


def test_get_remediation_activities():
    user_id = get_user_with_diagnostics()
    diagnostic_id = get_existing_diagnostic_id_for_learner(user_id)

    if diagnostic_id is None:
        pytest.skip("Aucun diagnostic existant pour David dans le dump SQL.")

    response = client.get(f"/remediation/activities/{diagnostic_id}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_get_weaknesses():
    user_id = get_user_with_diagnostics()

    response = client.get(f"/learners/{user_id}/weaknesses")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if data:
        weakness = data[0]
        assert "id_aav" in weakness
        assert "maitrise" in weakness
        assert "reussi" in weakness


def test_get_progression_map():
    user_id = get_user_with_diagnostics()

    response = client.get(f"/learners/{user_id}/progression-map")
    assert response.status_code == 200

    data = response.json()
    assert "progression_map" in data
    assert isinstance(data["progression_map"], list)

    if data["progression_map"]:
        point = data["progression_map"][0]
        assert "id_aav" in point
        assert "niveau_maitrise" in point
        assert "couleur_recommandee" in point


# -------------------------------------------------------------------
# TESTS REMEDIATION : CREATION D'UN NOUVEAU DIAGNOSTIC
# -------------------------------------------------------------------

def test_post_diagnostics_remediation():
    user_id = get_user_with_tentatives()
    aav_source = get_failed_or_weak_aav_for_learner(user_id)

    payload = {
        "id_apprenant": user_id,
        "id_aav_source": aav_source,
        "score_obtenu": 0.3,
        "type_echec": "prerequis_manquant"
    }

    response = client.post("/diagnostics/remediation", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["id_apprenant"] == user_id
    assert data["id_aav_source"] == aav_source
    assert "id_diagnostic" in data
    assert "aav_defaillants" in data
    assert "recommandations" in data
    assert isinstance(data["aav_defaillants"], list)
    assert isinstance(data["recommandations"], list)


def test_post_generate_remediation_path():
    user_id = get_user_with_status()
    aav_source = get_failed_or_weak_aav_for_learner(user_id)

    payload = {
        "id_apprenant": user_id,
        "id_aav_cible": aav_source,
        "profondeur_max": 3
    }

    response = client.post("/remediation/generate-path", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["id_aav_cible"] == aav_source
    assert "parcours_genere" in data
    assert isinstance(data["parcours_genere"], list)


def test_post_analyze_path():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_aav FROM aav WHERE is_active = 1 ORDER BY id_aav LIMIT 3"
        )
        aav_ids = [row["id_aav"] for row in cursor.fetchall()]

    assert len(aav_ids) > 0

    user_id = get_user_with_status()

    payload = {
        "id_apprenant": user_id,
        "chemin_aavs": aav_ids
    }

    response = client.post("/diagnostics/analyze-path", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert "path_analysis" in data
    assert isinstance(data["path_analysis"], list)

    if data["path_analysis"]:
        item = data["path_analysis"][0]
        assert "id_aav" in item
        assert "maitrise" in item
        assert "statut" in item


def test_root_causes_endpoint():
    user_id = get_user_with_status()
    aav_source = get_failed_or_weak_aav_for_learner(user_id)

    response = client.get(f"/learners/{user_id}/aavs/{aav_source}/root-causes")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["id_apprenant"] == user_id
    assert data["id_aav_analyse"] == aav_source
    assert "root_causes" in data
    assert isinstance(data["root_causes"], list)


# -------------------------------------------------------------------
# TESTS VALIDATION / ERREURS
# -------------------------------------------------------------------

def test_post_diagnostics_remediation_invalid_payload():
    """
    On envoie un payload invalide pour vérifier le 422.
    """
    payload = {
        "id_apprenant": "abc",   # invalide
        "id_aav_source": None,   # invalide
        "score_obtenu": 2.0,     # invalide (> 1)
        "type_echec": "nimportequoi"
    }

    response = client.post("/diagnostics/remediation", json=payload)
    assert response.status_code == 422


def test_post_generate_remediation_path_invalid_payload():
    payload = {
        "id_apprenant": 1,
        "id_aav_cible": 1,
        "profondeur_max": 999
    }

    response = client.post("/remediation/generate-path", json=payload)
    assert response.status_code == 422


def test_post_analyze_path_invalid_payload():
    payload = {
        "id_apprenant": 1,
        "chemin_aavs": "pas_une_liste"
    }

    response = client.post("/diagnostics/analyze-path", json=payload)
    assert response.status_code == 422