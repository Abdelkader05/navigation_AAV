# Projet Python Option - Groupe 5

## Presentation

Ce projet tourne autour des AAV (Acquis d'Apprentissage Vises).
On a une API FastAPI pour gerer les donnees et un client lourd Flet pour afficher tout ca plus facilement.

Le projet final est un melange de plusieurs morceaux du travail de groupe.
On n'a donc pas tout recode de zero : quand une partie existait deja et collait au sujet, on l'a reprise puis adaptee a notre appli.

## Ce qu'on peut faire

- afficher la liste des AAV
- filtrer les AAV
- voir le detail d'un AAV
- voir ses prerequis
- voir les exercices lies a un AAV
- creer un AAV
- modifier les prerequis d'un AAV
- charger un apprenant
- afficher son suivi
- simuler une tentative
- recalculer son niveau de maitrise

## Organisation rapide

```text
python_option/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── maitrise.py
│   └── routers/
│       ├── aavs.py
│       ├── learners.py
│       ├── attempts.py
│       ├── navigation.py
│       └── remediation.py
├── client_lourd/
│   ├── api_client.py
│   └── main.py
├── tests/
├── docs/
├── requirements.txt
└── groupe5.db
```

## Role des fichiers principaux

- `app/main.py` : point d'entree de l'API
- `app/database.py` : gestion SQLite
- `app/models.py` : modeles Pydantic
- `app/routers/aavs.py` : routes CRUD des AAV
- `app/routers/learners.py` : routes des apprenants
- `app/routers/attempts.py` : routes des tentatives
- `client_lourd/api_client.py` : envoi des requetes a l'API
- `client_lourd/main.py` : interface graphique Flet

## Ce qu'on a repris / adapte

Pour respecter l'idee du projet, on a reutilise des morceaux deja faits par d'autres groupes quand c'etait pertinent.

En particulier :

- la logique des tentatives / traitement vient d'un autre groupe puis a ete branchee chez nous
- le suivi apprenant a ete adapte pour s'afficher dans notre client lourd
- on a relie les routes backend et le client pour que tout fonctionne ensemble

Donc notre travail a surtout ete un travail d'integration et d'adaptation, pas juste de recreation complete.

## Installation

```bash
pip install -r requirements.txt
```

## Lancer l'API

```bash
uvicorn app.main:app --reload
```

Ensuite on peut aller sur :

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## Lancer le client lourd

Dans un autre terminal :

```bash
cd client_lourd
flet run main.py
```

## Routes utiles

### AAV

- `GET /aavs/`
- `GET /aavs/{id}`
- `POST /aavs/`
- `PATCH /aavs/{id}`
- `DELETE /aavs/{id}`

### Apprenants

- `GET /learners/`
- `GET /learners/{id}/learning-status`
- `GET /learners/{id}/learning-status/summary`

### Tentatives

- `POST /attempts`
- `POST /attempts/{id}/process`

## Exemple d'utilisation

1. On lance l'API.
2. On lance le client lourd.
3. On choisit un apprenant.
4. On regarde les AAV suivis.
5. On simule une tentative sur un AAV.
6. On recharge pour voir si le niveau change.

## Tests

Il y a quelques tests dans le dossier `tests`.

```bash
pytest
```
