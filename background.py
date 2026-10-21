# -*- coding: utf-8 -*-
"""Gestion du fond d'écran FBI flou."""

import io
from pathlib import Path

import requests
from PIL import Image, ImageFilter, ImageTk

from config import ASSETS_DIR, FBI_BACKGROUND_URL, USER_AGENT


class BackgroundManager:
    """Télécharge, floute et met en cache le fond d'écran FBI."""

    def __init__(self, master):
        self.master = master
        self.blurred_path = ASSETS_DIR / "fbi_background_blurred.png"
        self.photo = None

    def get_background(self) -> ImageTk.PhotoImage | None:
        """Retourne l'image de fond floue sous forme utilisable par Tkinter."""
        if not self.blurred_path.exists():
            self._download_and_blur()

        if self.blurred_path.exists():
            try:
                img = Image.open(self.blurred_path)
                self.photo = ImageTk.PhotoImage(img)
                return self.photo
            except Exception as exc:
                print(f"[Background] Erreur chargement fond : {exc}")
                return None
        return None

    def _download_and_blur(self) -> None:
        """Télécharge l'image FBI et applique un flou gaussien."""
        try:
            print(f"[Background] Téléchargement de {FBI_BACKGROUND_URL}")
            response = requests.get(
                FBI_BACKGROUND_URL,
                headers={"User-Agent": USER_AGENT},
                timeout=20,
            )
            response.raise_for_status()

            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            # Redimensionner à la résolution de l'écran principale
            screen_w = self.master.winfo_screenwidth()
            screen_h = self.master.winfo_screenheight()
            image = image.resize((screen_w, screen_h), Image.LANCZOS)

            # Appliquer un flou prononcé
            blurred = image.filter(ImageFilter.GaussianBlur(radius=12))

            # Overlay bleu foncé semi-transparent pour l'ambiance FBI
            overlay = Image.new("RGBA", blurred.size, (11, 31, 58, 140))
            blurred_rgba = blurred.convert("RGBA")
            blended = Image.alpha_composite(blurred_rgba, overlay)

            blended.convert("RGB").save(self.blurred_path, "PNG")
            print(f"[Background] Fond sauvegardé : {self.blurred_path}")
        except Exception as exc:
            print(f"[Background] Échec téléchargement : {exc}")
            self._generate_fallback()

    def _generate_fallback(self) -> None:
        """Génère un fond de secours en cas d'échec de téléchargement."""
        screen_w = self.master.winfo_screenwidth()
        screen_h = self.master.winfo_screenheight()
        image = Image.new("RGB", (screen_w, screen_h), "#0B1F3A")
        image.save(self.blurred_path, "PNG")
