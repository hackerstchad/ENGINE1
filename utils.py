# -*- coding: utf-8 -*-
"""Utilitaires divers pour l'application."""

import re
from datetime import datetime
from typing import List


def extract_dates(text: str) -> List[str]:
    """Extrait les dates potentielles d'un texte (formats variés)."""
    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b",
    ]
    found = []
    for pat in patterns:
        found.extend(re.findall(pat, text, flags=re.IGNORECASE))
    return list(dict.fromkeys(found))[:10]


def extract_context(text: str) -> str:
    """Extrait un extrait contextuel pertinent autour de mots-clés."""
    keywords = ["fbi", "arrest", "investigation", "photo", "image", "source", "taken", "captured"]
    lower = text.lower()
    for kw in keywords:
        idx = lower.find(kw)
        if idx != -1:
            start = max(0, idx - 120)
            end = min(len(text), idx + 220)
            snippet = text[start:end].replace("\n", " ").strip()
            return f"...{snippet}..."
    return text[:300].replace("\n", " ").strip() + "..."


def now_str() -> str:
    """Retourne la date/heure actuelle formatée."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
