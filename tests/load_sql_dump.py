"""
Charge un dump SQL (donnees_test.sql) dans une base SQLite.

Utilisation :
    python load_sql_dump.py
"""

import sqlite3
from pathlib import Path
from app.database import init_database
from app.config import settings

# On utilise exactement la même base que l'application
print(settings.database_path)
# 🔧 À adapter si besoin
DATABASE_PATH = Path("groupe5.db")
SQL_DUMP_PATH = Path("RessourcesCommunes/donnees_test.sql")


def load_sql_dump(db_path: Path, sql_path: Path):
    """
    Charge un fichier SQL complet dans une base SQLite.

    - crée la base si elle n'existe pas
    - exécute tout le script SQL
    """

    if not sql_path.exists():
        raise FileNotFoundError(f"Fichier SQL introuvable : {sql_path}")

    print(f"📦 Chargement du dump : {sql_path}")

    # Lire le fichier SQL
    sql_script = sql_path.read_text(encoding="utf-8")

    # Connexion SQLite
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # Exécution du script complet
        cursor.executescript(sql_script)

        conn.commit()
        print("✅ Dump chargé avec succès")

    except Exception as e:
        conn.rollback()
        print("❌ Erreur lors du chargement :", e)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    load_sql_dump(DATABASE_PATH, SQL_DUMP_PATH)