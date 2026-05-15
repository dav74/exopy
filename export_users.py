import os
import csv
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Erreur : DATABASE_URL doit être défini dans le fichier .env")
    print("Exemple : DATABASE_URL=postgresql://exopy:MOTDEPASSE@localhost:5432/exopy")
    exit(1)

def export_users():
    try:
        print("Connexion à la base de données...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT nom, prenom, username FROM users ORDER BY nom, prenom")
        users = cur.fetchall()

        cur.close()
        conn.close()

        if not users:
            print("Aucun utilisateur trouvé.")
            return

        output_file = 'tous_les_utilisateurs.csv'
        fieldnames = ['nom', 'prenom', 'username']

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in users:
                writer.writerow(user)

        print(f"Succès ! {len(users)} utilisateurs exportés dans {output_file}")
        return output_file

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        return None

if __name__ == "__main__":
    export_users()
