# Groupe 5 - API FastAPI

## Structure

- `app/main.py` : point d'entree FastAPI
- `app/database.py` : gestion SQLite3
- `app/models.py` : modeles Pydantic
- `app/config.py` : configuration
- `app/routers/votre_domaine.py` : endpoints du domaine
- `tests/test_votre_domaine.py` : tests API

## Lancer le projet

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Lancer les tests

```bash
pytest
```
