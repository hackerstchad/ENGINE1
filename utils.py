#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Search Engine - Utilitaires partagés
"""
import os
import re
import io
import json
import csv
import webbrowser
from datetime import datetime

import requests
from PIL import Image, ImageTk, ImageDraw, ImageFont


# Palette - Thème Blanc Minimaliste
COLOR_BG = "#FFFFFF"
COLOR_FG = "#111111"
COLOR_FG_SECONDARY = "#555555"
COLOR_ACCENT = "#2563EB"
COLOR_ACCENT_HOVER = "#1D4ED8"
COLOR_BORDER = "#E5E7EB"
COLOR_ROW_ODD = "#FAFAFA"
COLOR_ROW_EVEN = "#FFFFFF"
COLOR_HIGHLIGHT = "#DBEAFE"
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_ERROR = "#EF4444"


def safe_url_open(url: str) -> None:
    """Ouvre une URL dans le navigateur par défaut."""
    try:
        webbrowser.open(url)
    except Exception as exc:
        print(f"Impossible d'ouvrir l'URL : {exc}")


def format_number(value) -> str:
    """Formate un nombre entier avec des séparateurs de milliers."""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (ValueError, TypeError):
        return "0"


def truncate_text(text: str, max_length: int = 140) -> str:
    """Tronque un texte avec suspension de points."""
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) > max_length:
        return text[: max_length - 3].strip() + "..."
    return text


def clean_html(raw: str) -> str:
    """Supprime les balises HTML basiques d'une chaîne."""
    if not raw:
        return ""
    clean = re.sub(r"<[^>]+>", "", raw)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def get_current_timestamp() -> str:
    """Retourne un horodatage lisible."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def slugify(text: str) -> str:
    """Transforme une chaîne en nom de fichier sûr."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "_", text)
    return text[:80]


def load_json_file(path: str, default=None):
    """Charge un fichier JSON avec valeur par défaut."""
    if default is None:
        default = []
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def save_json_file(path: str, data) -> bool:
    """Sauvegarde des données dans un fichier JSON."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        return True
    except Exception as exc:
        print(f"Impossible de sauvegarder {path} : {exc}")
        return False


def http_get(url: str, params=None, headers=None, timeout=15):
    """Effectue une requête GET et retourne la réponse JSON ou texte."""
    if headers is None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text
    except requests.exceptions.Timeout:
        return {"error": "Timeout"}
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc)}


def download_image(url: str, size: tuple = (80, 80)):
    """Télécharge une image et la redimensionne pour Tkinter."""
    if not url:
        return None
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        image = image.convert("RGB")
        image.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception:
        return None


def create_placeholder_image(size: tuple = (80, 80), text: str = "?"):
    """Crée une image de placeholder colorée."""
    image = Image.new("RGB", size, "#E5E7EB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", size[0] // 2)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    draw.text((x, y), text, fill="#6B7280", font=font)
    return ImageTk.PhotoImage(image)


def fetch_image_from_url(url: str):
    """Télécharge une image ou retourne un placeholder."""
    img = download_image(url, size=(80, 80))
    if img:
        return img
    return create_placeholder_image((80, 80), "img")


def load_profiles_csv(path: str):
    """Charge des profils depuis un fichier CSV."""
    profiles = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=1):
                profiles.append({
                    "id": idx,
                    "name": row.get("name", "Profil " + str(idx)),
                    "role": row.get("role", "Utilisateur"),
                    "avatar": row.get("avatar", ""),
                    "email": row.get("email", ""),
                    "bio": row.get("bio", ""),
                    "tags": [t.strip() for t in row.get("tags", "").split(",") if t.strip()],
                    "active": idx == 1
                })
    except Exception as exc:
        print(f"Impossible de lire le CSV : {exc}")
    return profiles
