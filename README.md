# FBI Image Intelligence Interface

Application de bureau Python avancée avec interface `tkinter` permettant :

- Authentification par nom d'utilisateur / mot de passe
- Fond d'écran FBI flou téléchargé automatiquement
- Upload d'une image locale
- Recherche inversée d'image et extraction d'informations (sources, dates, contexte)
- Barre de progression ultra-rapide (1000+ itérations par seconde)
- Interface unique en plein écran

## Installation

```bash
cd fbi_image_search
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Identifiants par défaut

- **Utilisateur** : `admin`
- **Mot de passe** : `fbi123`

> Changez ces identifiants dans [`src/config.py`](src/config.py) avant toute utilisation réelle.

## Utilisation

1. Connectez-vous avec les identifiants par défaut.
2. Cliquez sur **"📁 Charger une image"** pour sélectionner un fichier.
3. Cliquez sur **"🔍 Lancer l'analyse FBI"**.
4. Patientez pendant le scan ultra-rapide.
5. Consultez les résultats : sources web, dates détectées, contexte textuel.

## Avertissement

Cet outil effectue du scraping web et des requêtes vers des moteurs de recherche publics.
Respectez les conditions d'utilisation des sites consultés. L'utilisation est à des fins éducatives.

## Structure

```
fbi_image_search/
├── main.py
├── requirements.txt
├── README.md
└── src/
    ├── __init__.py
    ├── app.py
    ├── config.py
    ├── auth.py
    ├── ui_components.py
    ├── background.py
    ├── image_search.py
    └── utils.py
```
