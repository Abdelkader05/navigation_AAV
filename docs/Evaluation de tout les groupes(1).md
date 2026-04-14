# Évaluation des Groupes - Projet PlatonAAV L3

CETTE NOTE PARTICIPE POUR 20% DANS LA NOTE FINALE.

ATTENTON AU RECOMMANDATIONS GLOBALES EN FIN DE DOCUMENT.

Les critères utilisés ici seront réutilisés dans la prochaine évaluation.


**Projet :** API REST PlatonAAV - Gestion des Acquis d'Apprentissage Visés

## Méthodologie d'Évaluation

Chaque groupe est évalué sur **4 critères principaux** (notation sur 20) :

| Critère | Pondération | Description |
|---------|-------------|-------------|
| **Respect des Normes** | 25% | PEP8, Structure projet, Convention de nommage |
| **Qualité du Code** | 30% | Documentation, Tests, Gestion d'erreurs, Typage |
| **Intelligence Algorithmique** | 30% | Efficacité, Pertinence des algorithmes, Optimisation |
| **Fonctionnalités & Livrables** | 15% | Complétude, Respect du cahier des charges |

---

## Résumé Global

| Groupe | Thème | Note Globale | Mention |
|--------|-------|--------------|---------|
| **Groupe 1** | AAV & Ontologies | 13/20 | Passable |
| **Groupe 2** | Apprenants & Profils | 16/20 | Bien |
| **Groupe 3** | Tentatives & Évaluation | 15.5/20 | Bien |
| **Groupe 4** | Activités Pédagogiques | 14/20 | Passable |
| **Groupe 5** | Navigation & Recommandations | 15/20 | Bien |
| **Groupe 6** | Diagnostic & Remédiation | 12/20 | Passable |
| **Groupe 7** | Métriques & Qualité | 17.5/20 | Très Bien |
| **Groupe 8** | Génération d'Exercices | 14.5/20 | Passable |

**Moyenne de la promotion :** 14.6/20

---

## Évaluation Détaillée par Groupe

### Groupe 1 : AAV et Ontologies



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 12/20 | ⚠️ Imports non organisés (`from app.db import` avant `from app.schemas`), commentaires en français mélangés avec du code anglais. Pas de docstrings sur les fonctions. |
| **Qualité du Code** | 13/20 | ✅ Utilisation correcte de Pydantic. ⚠️ Pas de gestion d'exceptions globales. Code répétitif dans les filtres. Pas de tests unitaires visibles. |
| **Intelligence Algorithmique** | 14/20 | ✅ Pagination implémentée correctement. ⚠️ Algorithmes de recherche basiques (LIKE SQL), pas d'indexation. |
| **Fonctionnalités** | 13/20 | ✅ CRUD AAV fonctionnel. ⚠️ Partie Ontologies peu développée. |

#### Points Forts
- Structure de base respectée avec FastAPI
- Utilisation de Pydantic pour la validation
- Filtrage par paramètres de requête

#### Points à Améliorer
- **Documentation absente** : aucune docstring
- Pas de gestion d'erreurs HTTP cohérente
- Nommage des variables (`requete` vs `query`, `param_filtre` vs `filter_params`)

#### Exemple de Code Problématique
```python
# Ligne 5: Import dupliqué (AAVPatch importé 2 fois)
from app.schemas.aavPydanticClasses import AAVPatch, AAVResponse, AAVCreate, AAVUpdate, AAVPatch

# Ligne 13: Commentaire superflu (évident que c'est pour Swagger)
# ajout des tags pour s'y retrouver apres dans le swager /docs
```

**Note Finale : 13/20** - Code fonctionnel mais manque de professionnalisme et de documentation.

---

### Groupe 2 : Apprenants et Profils



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 16/20 | ✅ Structure professionnelle avec Repository Pattern. ⚠️ Quelques fautes d'orthographe (`apprentant` vs `apprenant`). |
| **Qualité du Code** | 17/20 | ✅ Bonne encapsulation. Gestion du cycle de vie avec lifespan. ⚠️ Imports circulaires potentiels. |
| **Intelligence Algorithmique** | 15/20 | ✅ Repository pattern bien implémenté. ⚠️ Algorithmes de récupération basiques. |
| **Fonctionnalités** | 16/20 | ✅ CRUD complet avec gestion des prérequis externes. Bonne couverture fonctionnelle. |

#### Points Forts
- **Architecture excellente** : Repository Pattern avec classe `LearnerRepository`
- Gestion des exceptions personnalisées (`DatabaseError`)
- Gestion des champs JSON (conversion automatique)
- Utilisation de `lifespan` pour l'initialisation

#### Points à Améliorer
- Fautes d'orthographe dans les commentaires
- Certains imports pourraient être optimisés

#### Exemple de Code Positif
```python
class LearnerRepository(BaseRepository):
    def __init__(self):
        super().__init__("apprenant", "id_apprenant")

    def get_by_id(self, id_value: int):
        """Récupère un apprenant uniquement s'il est actif."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM apprenant
                WHERE id_apprenant = ? AND is_active = 1""",
                (id_value,)
            )
```

**Note Finale : 16/20** - Bon travail architectural, soigner la relecture.

---

### Groupe 3 : Tentatives et Évaluation



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 16/20 | ✅ Imports triés, typage complet. ⚠️ Fichier `maitrise.py` sans docstring de module. |
| **Qualité du Code** | 16/20 | ✅ Gestion d'exceptions globales très complète. Fonctions utilitaires bien pensées. |
| **Intelligence Algorithmique** | 15/20 | ✅ Fonction `row_to_tentative` intelligente. ⚠️ Calcul de maîtrise basique. |
| **Fonctionnalités** | 15/20 | ✅ CRUD tentatives + calcul de maîtrise. Bonne intégration avec G2. |

#### Points Forts
- **Gestion d'exceptions exceptionnelle** : 4 handlers complets
- Conversion automatique SQLite → Python (booléens, JSON)
- Filtrage dynamique bien construit

#### Points à Améliorer
- Documentation du module `maitrise.py`
- Tests unitaires à développer

#### Exemple de Code Positif
```python
def row_to_tentative(row: sqlite3.Row) -> Tentative:
    data = dict(row)
    # SQLite bool: 0/1 -> False/True
    data["est_valide"] = (data.get("est_valide", 0) == 1)
    # JSON metadata
    meta = data.get("metadata")
    data["metadata"] = from_json(meta) if meta else None
    return Tentative(**data)
```

**Note Finale : 15.5/20** - Code très propre, gestion d'erreurs exemplaire.

---

### Groupe 4 : Activités Pédagogiques



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 14/20 | ✅ Structure FastAPI standard. ⚠️ Routers multiples avec redondance (aavs.py redondant avec G1). |
| **Qualité du Code** | 14/20 | ✅ Gestion du cycle de vie. ⚠️ Manque de documentation sur les fonctions métier. |
| **Intelligence Algorithmique** | 14/20 | ✅ Gestion des sessions bien structurée. ⚠️ Algorithmes de bilan basiques. |
| **Fonctionnalités** | 14/20 | ✅ CRUD Activités et Sessions. ⚠️ Clôture de session à approfondir. |

#### Points Forts
- Bonne séparation des routers (activités, sessions, types)
- Utilisation cohérente de lifespan
- Gestion des activités pédagogiques complète

#### Points à Améliorer
- Éviter la duplication du router AAV (déjà en G1)
- Documentation des fonctions de bilan

**Note Finale : 14/20** - Bon travail, attention à la coordination avec G1.

---

### Groupe 5 : Navigation et Recommandations



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 15/20 | ✅ Structure propre. ⚠️ Router AAV redondant. |
| **Qualité du Code** | 15/20 | ✅ Gestion d'exceptions complète. Bonne validation des entrées. |
| **Intelligence Algorithmique** | 15/20 | ✅ Algorithme de recommandation présent. ⚠️ Peu optimisé pour de grandes ontologies. |
| **Fonctionnalités** | 15/20 | ✅ Filtrage AAV, recommandations, vérification des prérequis. |

#### Points Forts
- Gestion d'exceptions très complète (comme G3)
- Algorithme de navigation fonctionnel
- Bonne utilisation des dépendances FastAPI

#### Points à Améliorer
- Performance sur les graphes de prérequis complexes
- Éviter la duplication avec G1 sur les AAV

**Note Finale : 15/20** - Bonne intégration des fonctionnalités de navigation.

---

### Groupe 6 : Diagnostic et Remédiation



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 11/20 | ⚠️ Structure minimaliste. Manque de cohérence avec les autres groupes. |
| **Qualité du Code** | 12/20 | ⚠️ Code fonctionnel mais peu documenté. Pas de gestion d'exceptions globale. |
| **Intelligence Algorithmique** | 12/20 | ⚠️ Algorithme récursif pour l'analyse mais peu optimisé. |
| **Fonctionnalités** | 13/20 | ✅ Diagnostic et parcours de remédiation. ⚠️ Interface API limitée. |

#### Points Forts
- Algorithme récursif pour l'analyse des échecs
- Concept de parcours de remédiation intéressant

#### Points à Améliorer
- **Structure à revoir** : trop éloignée des autres groupes
- Documentation quasi absente
- Gestion d'erreurs insuffisante

**Note Finale : 12/20** - Fonctionnalités présentes mais intégration perfectible.

---

### Groupe 7 : Métriques et Qualité



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 18/20 | ✅ Architecture exceptionnelle avec séparation des services. ⚠️ Quelques imports absolus (`import routers`) au lieu de relatifs. |
| **Qualité du Code** | 18/20 | ✅ **Meilleure architecture** : séparation routers/services. Tests complets. Documentation. |
| **Intelligence Algorithmique** | 17/20 | ✅ Algorithmes de métriques bien pensés (couverture, taux de succès). Détection d'alertes. |
| **Fonctionnalités** | 17/20 | ✅ Dashboard, métriques, rapports, comparaisons. Très complet. |

#### Points Forts
- **Architecture professionnelle** : séparation claire routers/services
- Services dédiés : `metric_calculator.py`, `alert_detector.py`, `report_generator.py`
- Tests unitaires complets (`test_metric.py`, `test_dashboard.py`)
- Modèles bien structurés avec schemas Pydantic

#### Points à Améliorer
- Utiliser des imports relatifs (`from . import routers` → `from app import routers`)
- Quelques types pourraient être plus stricts

#### Exemple de Code Exemplaire
```python
# Séparation des responsabilités
# routers/metrics.py : gère les endpoints
# services/metric_calculator.py : logique métier

class MetricCalculator:
    def calculer_couverture(self, aav_id: int) -> float:
        """Calcule la couverture des ressources pour un AAV."""
        score = 0.0
        if self.count_exercices(aav_id) > 0:
            score += 0.4
        if self.count_prompts(aav_id) > 0:
            score += 0.3
        return score
```

**Note Finale : 17.5/20** - Référence de la promotion sur l'architecture.

---

### Groupe 8 : Génération d'Exercices



#### Détails des Critères

| Critère | Note | Commentaire |
|---------|------|-------------|
| **Respect des Normes** | 15/20 | ✅ Structure correcte. ⚠️ Utilisation de `routeurs` (français) au lieu de `routers`. |
| **Qualité du Code** | 14/20 | ✅ Services bien structurés. ⚠️ Code dense dans exerciseEngine, manque de modularité. |
| **Intelligence Algorithmique** | 15/20 | ✅ Moteur d'exercices complet. ⚠️ Complexité élevée, difficile à maintenir. |
| **Fonctionnalités** | 14/20 | ✅ Génération d'exercices, prompts, sélection. Fonctionnalités riches. |

#### Points Forts
- Moteur d'exercices très complet (27KB de code!)
- Gestion des prompts de fabrication
- Intégration avec les AAV

#### Points à Améliorer
- **Modularité** : `exerciseEngine.py` est trop dense (27KB)
- Renommer `routeurs` → `routers` pour cohérence
- Séparer le moteur en sous-modules

**Note Finale : 14.5/20** - Fonctionnalités riches mais code à modulariser.

---

## Recommandations Globales

### Pour tous les groupes

1. **Standardiser les imports** : Utiliser des imports relatifs partout
2. **Unifier la gestion d'erreurs** : Prendre exemple sur G3 et G7
3. **Documentation** : Ajouter des docstrings sur toutes les fonctions publiques
4. **Tests** : Seuls G7 et G8 ont des tests significatifs

### Améliorations Prioritaires par Groupe

| Groupe | Priorité 1 | Priorité 2 |
|--------|------------|------------|
| G1 | Ajouter docstrings | Gestion d'exceptions |
| G2 | Corriger orthographe | Optimiser imports |
| G3 | Documenter maitrise.py | Plus de tests |
| G4 | Retirer duplication AAV | Documenter bilans |
| G5 | Optimiser graphes | Retirer duplication AAV |
| G6 | **Restructurer le code** | Ajouter exceptions |
| G7 | Imports relatifs | - |
| G8 | **Modulariser exerciseEngine** | Renommer routeurs |

---

## Conclusion

**Points Positifs de la Promotion :**
- ✅ Architecture FastAPI globalement respectée
- ✅ Groupe 7 (Métriques) montre le niveau attendu
- ✅ Bonne répartition fonctionnelle entre groupes

**Points de Vigilance :**
- ⚠️ **Groupe 6** nécessite une restructuration significative
- ⚠️ **Duplications** : Trop de groupes ont recréé le router AAV (G1,G2,G4,G5,G8)
- ⚠️ **Tests** : Insuffisants dans la plupart des groupes

---

*Document généré automatiquement par analyse du code source.*
