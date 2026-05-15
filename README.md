# Guide d'installation d'Exopy

Exopy est une plateforme d'apprentissage Python avec tutorat IA.
Ce guide permet d'installer l'application sur n'importe quel serveur Linux via Docker.

---

## Prérequis

- Un serveur Linux (Debian, Ubuntu, Rocky Linux…) avec accès SSH
- Droits `sudo` sur le serveur
- Une clé API [OpenRouter](https://openrouter.ai) (pour le tutorat IA)

---

## Étape 1 — Installer Docker sur le serveur

Connectez-vous à votre serveur via SSH, puis exécutez :

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
exit
```

Reconnectez-vous en SSH, puis vérifiez que Docker fonctionne :

```bash
docker --version
docker compose version
```

---

## Étape 2 — Récupérer le code source

```bash
git clone <URL_DU_DEPOT> exopy
cd exopy
```

Ou copier les fichiers depuis votre machine locale :

```bash
scp -r exopy/ utilisateur@serveur:~/
cd exopy
```

---

## Étape 3 — Configurer l'application

Copiez le fichier de configuration exemple et éditez-le :

```bash
cp .env.example .env
nano .env
```

Voici les variables à renseigner :

| Variable | Description | Exemple |
|---|---|---|
| `FRONTEND_PORT` | Port du site web (80 par défaut) | `80` |
| `POSTGRES_PASSWORD` | Mot de passe de la base de données | `MonMotDePasse123!` |
| `SECRET_KEY` | Clé secrète pour les tokens de connexion | *(voir ci-dessous)* |
| `ADMIN_USERNAME` | Identifiant du compte administrateur | `admin` |
| `ADMIN_PASSWORD` | Mot de passe du compte administrateur | `MonAdminPass!` |
| `OPENROUTER_API_KEY` | Clé API OpenRouter pour l'IA | `sk-or-...` |
| `CORS_ORIGINS` | Origines autorisées pour l'API (optionnel, laisser vide) | |

**Générer une `SECRET_KEY` robuste :**
```bash
openssl rand -hex 32
```

> **Important :** Ne partagez jamais votre fichier `.env`. Il est ignoré par git.

---

## Étape 4 — Lancer l'application

```bash
docker compose up -d --build
```

Cette commande va :
1. Télécharger les images Docker nécessaires (PostgreSQL, nginx, Python)
2. Compiler l'application Vue.js
3. Démarrer les trois services : base de données, API, site web

Le premier lancement prend quelques minutes. Suivez la progression :

```bash
docker compose logs -f
```

Appuyez sur `Ctrl+C` pour quitter l'affichage des logs (les services continuent de tourner).

---

## Étape 5 — Vérifier que tout fonctionne

```bash
docker compose ps
```

Vous devez voir trois services avec le statut `running` (healthy) :
```
NAME                STATUS
exopy-postgres-1    running (healthy)
exopy-backend-1     running (healthy)
exopy-frontend-1    running (healthy)
```

Ouvrez un navigateur et accédez à :
- **Site web :** `http://VOTRE_IP` (ou `http://VOTRE_IP:FRONTEND_PORT` si vous avez changé le port)
- **Documentation API :** `http://VOTRE_IP/api/docs`

Connectez-vous avec le compte admin défini dans votre `.env`.

---

## Utilisation quotidienne

### Démarrer / arrêter l'application

```bash
docker compose stop
docker compose start
docker compose restart
```

### Voir les logs

```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

### Mettre à jour l'application

```bash
git pull
docker compose up -d --build
```

---

## Sauvegarder la base de données

```bash
docker compose exec postgres pg_dump -U exopy exopy > sauvegarde_$(date +%Y%m%d).sql
```

Pour restaurer :
```bash
cat sauvegarde_20241201.sql | docker compose exec -T postgres psql -U exopy exopy
```

