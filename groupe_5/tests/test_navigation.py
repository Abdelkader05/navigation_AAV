import sqlite3

# connexion à la base
conn = sqlite3.connect("platonAAV.db")

# lire le fichier SQL
with open("../RessourcesCommunes-20260304/donnees_test.sql", "r") as f:
    sql_script = f.read()

# exécuter le script
conn.executescript(sql_script)

# sauvegarder
conn.commit()

# fermer
conn.close()

print("Dump chargé avec succès")