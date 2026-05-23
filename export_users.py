import os
import csv
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Erreur : DATABASE_URL doit être défini dans le fichier .env")
    print("Exemple : DATABASE_URL=postgresql://exopy:MOTDEPASSE@localhost:5432/exopy")
    exit(1)

def export_users(admin_username=None):
    try:
        print("Connexion à la base de données...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if admin_username:
            cur.execute("SELECT id FROM admins WHERE username = %s", (admin_username,))
            admin_row = cur.fetchone()
            if not admin_row:
                print(f"Erreur : Admin '{admin_username}' non trouvé.")
                cur.close()
                conn.close()
                return
            admin_id = admin_row['id']
            cur.execute(
                "SELECT nom, prenom, username FROM users WHERE admin_id = %s ORDER BY nom, prenom",
                (admin_id,)
            )
            output_file = f'utilisateurs_{admin_username}.csv'
        else:
            cur.execute(
                """SELECT u.nom, u.prenom, u.username, a.username as admin
                   FROM users u JOIN admins a ON u.admin_id = a.id
                   ORDER BY a.username, u.nom, u.prenom"""
            )
            output_file = 'tous_les_utilisateurs.csv'

        users = cur.fetchall()

        cur.close()
        conn.close()

        if not users:
            print("Aucun utilisateur trouvé.")
            return

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if admin_username:
                fieldnames = ['nom', 'prenom', 'username']
            else:
                fieldnames = ['admin', 'nom', 'prenom', 'username']
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
    if len(sys.argv) > 1:
        export_users(sys.argv[1])
    else:
        print("Usage : python export_users.py [admin_username]")
        print("  Sans argument : exporte tous les utilisateurs de tous les admins")
        print("  Avec argument : exporte les utilisateurs d'un admin spécifique")
        export_users()
