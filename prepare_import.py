import csv
import random
import unicodedata
import os
import sys

def notify_install():
    print("\nCe script nécessite la bibliothèque 'fpdf2' pour générer le PDF.")
    print("Veuillez l'installer avec la commande suivante :")
    print("pip install fpdf2\n")

try:
    from fpdf import FPDF
except ImportError:
    notify_install()
    # On continue quand même pour le CSV si possible, mais on prévient.
    FPDF = None

def remove_accents(input_str):
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def generate_login(nom, prenom, existing_logins):
    nom_clean = remove_accents(nom).lower().replace(" ", "").replace("-", "")
    prenom_clean = remove_accents(prenom).lower().replace(" ", "").replace("-", "")
    
    base_login = (nom_clean[:6] + prenom_clean[0]) if prenom_clean else nom_clean[:7]
    
    login = base_login
    counter = 1
    while login in existing_logins:
        login = f"{base_login}{counter}"
        counter += 1
    
    existing_logins.add(login)
    return login

def generate_pronounceable_password(length=6):
    consonants = "bcdfghjklmnprstvw"
    vowels = "aeiouy"
    
    password = ""
    for i in range(length // 2):
        password += random.choice(consonants)
        password += random.choice(vowels)
    return password

def create_labels_pdf(users, output_path):
    if FPDF is None:
        print("Saut de la génération PDF (fpdf2 non installée).")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    
    # Paramètres des étiquettes (A4 avec marges)
    col_width = 60
    row_height = 30
    margin = 10
    cols = 3
    
    x_start = margin
    y_start = margin
    
    for i, user in enumerate(users):
        row = i // cols
        col = i % cols
        
        # Saut de page si nécessaire
        if row > 0 and i % (cols * 8) == 0:
            pdf.add_page()
            row = 0
            
        x = x_start + (col * col_width)
        y = y_start + (row % 8 * row_height)
        
        # Dessiner le cadre de l'étiquette
        pdf.rect(x, y, col_width, row_height)
        
        # Contenu
        pdf.set_xy(x + 2, y + 5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5, f"{user['prenom']} {user['nom']}", ln=True)
        
        pdf.set_xy(x + 2, y + 12)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f"Login : {user['login']}", ln=True)
        
        pdf.set_xy(x + 2, y + 18)
        pdf.cell(0, 5, f"MDP : {user['password']}", ln=True)


    pdf.output(output_path)
    print(f"PDF des étiquettes généré : {output_path}")

def main(input_csv):
    if not os.path.exists(input_csv):
        print(f"Erreur : Le fichier {input_csv} n'existe pas.")
        return

    output_csv = "users_to_import.csv"
    output_pdf = "etiquettes_eleves.pdf"
    
    users = []
    existing_logins = set()
    
    try:
        with open(input_csv, mode='r', encoding='utf-8') as f:
            # Essayer de détecter le délimiteur
            sample = f.read(1024)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.reader(f, dialect)
            
            # Gestion du header
            header = next(reader, None)
            # Si le header ne contient pas de mots clés, on le traite comme une donnée
            if header and not any(h.lower() in ['nom', 'prénom', 'prenom', 'name'] for h in header):
                f.seek(0)
                # On ne réinitialise pas reader ici, on traite juste header ensuite
            elif header:
                # C'était un vrai header, on continue avec reader
                pass
            else:
                return

            for row in reader:
                if not row or len(row) < 2:
                    continue
                
                # On assume Col 0 = Nom, Col 1 = Prénom (ou vice versa si détecté)
                nom = row[0].strip()
                prenom = row[1].strip()
                
                if not nom or not prenom:
                    continue
                    
                login = generate_login(nom, prenom, existing_logins)
                password = generate_pronounceable_password()
                
                users.append({
                    "nom": nom,
                    "prenom": prenom,
                    "login": login,
                    "password": password
                })
    except Exception as e:
        print(f"Erreur lors de la lecture du CSV : {e}")
        return

    # Écriture du CSV de sortie
    with open(output_csv, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['nom', 'prenom', 'login', 'password'])
        for u in users:
            writer.writerow([u['nom'], u['prenom'], u['login'], u['password']])
    
    print(f"CSV prêt pour l'import généré : {output_csv}")
    
    # Génération du PDF
    create_labels_pdf(users, output_pdf)
    
    print("\nTerminé !")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python prepare_import.py [fichier_entree.csv]")
    else:
        main(sys.argv[1])
