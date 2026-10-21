# -*- coding: utf-8 -*-
"""Configuration globale de l'application FBI Image Intelligence."""

from pathlib import Path

# Dossiers
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

# Identifiants par défaut (à modifier en production)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "fbi123"

# URL du logo / sceau FBI utilisé comme fond d'écran flou
FBI_BACKGROUND_URL = (
    "https://www.politico.com/dims4/default/resize/888/quality/90/format/webp"
    "?url=https%3A%2F%2Fstatic.politico.com%2F3b%2Faa%2F6242dbe44c659210425c94618b83"
    "%2F190115-fbi-seal-ap-773.jpg"
)

# Paramètres UI
APP_TITLE = "FBI IMAGE INTELLIGENCE INTERFACE"
APP_WIDTH = 1280
APP_HEIGHT = 800
FBI_BLUE = "#0B1F3A"
FBI_GOLD = "#F4C430"
FBI_RED = "#B22234"
FBI_WHITE = "#F0F0F0"
TEXT_FONT = ("Consolas", 11)
TITLE_FONT = ("Impact", 32)
HEADER_FONT = ("Consolas", 14, "bold")

# Recherche
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
SEARCH_TIMEOUT = 15
MAX_RESULTS = 12
