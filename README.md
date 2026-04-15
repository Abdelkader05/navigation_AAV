# PlatonAAV — Groupe 5 · Opérateurs de Navigation

API REST FastAPI pour les opérateurs de navigation du projet PlatonAAV. Ce module gère la progression des apprenants à travers les AAV (Aptitudes et Acquis Visés) : accessibilité, suivi en cours, blocages, et révisions espacées.

---

## Structure du projet

```
app/
├── main.py          # Application FastAPI, lifespan, gestion globale des erreurs
├── database.py      # Connexion SQLite3, initialisation des tables
├── models.py        # Modèles Pydantic (AAV, réponses navigation)
├── config.py        # Configuration chargée depuis l'environnement
└── routers/
    └── navigation.py  # Endpoints de navigation

tests/
└── test_navigation.py  # Tests API avec base SQLite temporaire
```

## Endpoints principaux

- `GET /navigation/{id_apprenant}/accessible`
- `GET /navigation/{id_apprenant}/in-progress`
- `GET /navigation/{id_apprenant}/blocked`
- `GET /navigation/{id_apprenant}/reviewable`
- `GET /navigation/{id_apprenant}/dashboard`
- `GET /navigation/{id_apprenant}`


### Logique de navigation

- **Accessible** : prérequis tous ≥ 0.8 de maîtrise, AAV non encore commencé
- **In progress** : maîtrise > 0 et < 0.9
- **Blocked** : au moins un prérequis < 0.8
- **Reviewable** : maîtrise ≥ 0.8 et révision jamais effectuée ou échéance dépassée

Les résultats sont mis en cache dans `navigation_cache` pour éviter les recalculs.


#### Installation et lancement

```bash
pip install -r requirements.txt
```

```bash
# Développement (rechargement automatique)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

La documentation interactive est disponible sur `http://localhost:8000/docs`.

---

##### Initialisation de la base de données

python -m tests.load_sql_dump




```bash
# Tous les tests
pytest

# Avec rapport de couverture
pytest --cov=app --cov-report=html

# Tests d'un fichier spécifique
pytest tests/test_profond.py -v
```
