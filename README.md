# Search Engine - Interface Tkinter Avancée

Moteur de recherche universel multi-sources avec interface desktop blanche minimaliste développée en Python/Tkinter.

## Fonctionnalités

- 🔍 Recherche simultanée sur **38 sources publiques** sans clé API
- 🖼️ Affichage des résultats sous forme de tableau avec vignettes automatiques
- 👤 Gestion des profils utilisateurs (JSON/CSV)
- 📊 Résumé automatique des résultats par catégorie et source
- 📁 Export CSV des résultats
- 📜 Historique des recherches
- 🎨 Thème blanc minimaliste avec titre noir
- ⌨️ Raccourcis clavier
- 🌐 Ouverture des liens dans le navigateur

## Sources intégrées

### Académique
Google Scholar, Semantic Scholar, PubMed, arXiv, CORE, BASE, OpenAlex, Crossref, DOAJ, ERIC, JSTOR

### Code
GitHub Code Search, Sourcegraph, grep.app, GitLab, Stack Overflow, npm, PyPI, crates.io, Docker Hub, Hugging Face

### Images
Google Images, Bing Images, Flickr, Unsplash, Pexels

### Vidéos
YouTube, Vimeo, Dailymotion

### Archives
Internet Archive

### Cartes
Google Maps, OpenStreetMap, Apple Maps, Bing Maps, HERE WeGo, MapQuest, Yandex Maps, Baidu Maps

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python search_engine.py
```

## Utilisation

1. Entrez un mot-clé dans la barre de recherche centrale
2. Sélectionnez une catégorie (All, Academic, Code, Images, Videos, Maps, Archives)
3. Cliquez sur **Rechercher** ou appuyez sur `Entrée`
4. Les résultats s'affichent dans le tableau avec image, titre, description et source
5. Le profil actif est affiché à droite avec le résumé de la recherche

## Raccourcis clavier

- `Ctrl + R` : Lancer la recherche
- `Ctrl + E` : Exporter les résultats en CSV
- `Ctrl + H` : Afficher l'historique
- `Ctrl + Q` : Quitter
- `Échap` : Effacer les résultats

## Profils

Le fichier [`profiles.json`](profiles.json) contient des profils exemples. Vous pouvez ajouter vos propres profils avec les champs suivants :

```json
{
  "id": 1,
  "name": "Agent Alpha",
  "role": "Analyste OSINT",
  "avatar": "https://example.com/avatar.jpg",
  "email": "alpha@example.com",
  "bio": "Description du profil",
  "tags": ["osint", "web"],
  "active": true
}
```

## Fichiers

- [`search_engine.py`](search_engine.py) : Application principale
- [`profiles.json`](profiles.json) : Fichier de profils exemple
- [`requirements.txt`](requirements.txt) : Dépendances Python
- [`README.md`](README.md) : Documentation

## Dépendances

- Python 3.8+
- requests
- Pillow
- urllib3
- beautifulsoup4
- lxml
- feedparser
- python-dateutil
- packaging
- markdown

## Avertissement

Cet outil est fourni à des fins éducatives et de recherche. Respectez les conditions d'utilisation des services interrogés.
