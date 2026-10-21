#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FBI Image Intelligence Terminal - Édition Ultime (une seule page)
Auteur : Assistant CodePal
Description : Interface Tkinter immersive FBI avec authentification, upload,
analyse forensique d'image (EXIF, hash, OCR, visage), recherche inversée
multi-moteurs (Google, Yandex, Bing, TinEye, Baidu) sans clé API, extraction
de contexte depuis les pages web, et rapport JSON.
Avertissement : outil éducatif/démonstration. Respectez les CGU des services tiers.
Le thème FBI est purement cosmétique.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import math
import mimetypes
import os
import random
import re
import ssl
import string
import sys
import tempfile
import threading
import time
import tkinter as tk
import uuid
import webbrowser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import (
    Button,
    Canvas,
    Checkbutton,
    Entry,
    Frame,
    Label,
    PhotoImage,
    Scrollbar,
    StringVar,
    Text,
    Toplevel,
    filedialog,
    messagebox,
    ttk,
)
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote, urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from PIL import ExifTags, Image, ImageFilter, ImageOps, ImageTk
from requests.adapters import HTTPAdapter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# CONFIGURATION GLOBALE
# ---------------------------------------------------------------------------
APP_TITLE = "FBI IMAGE INTELLIGENCE TERMINAL"
DEFAULT_USERNAME = "agent.fbi"
DEFAULT_PASSWORD = "Quantico2024!"
BG_FILENAME = "fbi_seal_bg.jpg"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
BG_PATH = CACHE_DIR / BG_FILENAME
REPORT_DIR = Path(__file__).parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

COLORS = {
    "bg": "#05070a",
    "panel": "#0b1021",
    "panel2": "#111936",
    "accent": "#1f3a93",
    "gold": "#d4af37",
    "fg": "#e8eaf6",
    "ok": "#00c853",
    "warn": "#ffab00",
    "danger": "#ff1744",
    "cyan": "#00bcd4",
}

FONTS = {
    "title": ("Consolas", 22, "bold"),
    "header": ("Consolas", 14, "bold"),
    "body": ("Consolas", 11),
    "mono": ("Courier New", 10),
    "small": ("Consolas", 9),
}

HTTP_TIMEOUT = 35
MAX_WORKERS = 6

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


# ---------------------------------------------------------------------------
# UTILITAIRES RÉSEAU / SÉCURITÉ
# ---------------------------------------------------------------------------
def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(DEFAULT_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    })
    adapter = HTTPAdapter(max_retries=urllib3.util.Retry(total=2, backoff_factor=0.5))
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def clean_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/"):
        return url
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def safe_get_text(soup: BeautifulSoup, selector: str, default: str = "") -> str:
    try:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else default
    except Exception:
        return default


def extract_meta(soup: BeautifulSoup, name: str) -> str:
    for attr in ("name", "property", "itemprop"):
        tag = soup.find("meta", attrs={attr: name})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


# ---------------------------------------------------------------------------
# TRAITEMENT D'IMAGES
# ---------------------------------------------------------------------------
def ensure_background(image_bytes: Optional[bytes] = None) -> Optional[Path]:
    try:
        if image_bytes:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        elif BG_PATH.exists():
            return BG_PATH
        else:
            return None
        # Redimensionnement + flou + overlay sombre FBI
        img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(radius=14))
        overlay = Image.new("RGB", img.size, (8, 12, 22))
        img = Image.blend(img, overlay, alpha=0.78)
        img.save(BG_PATH, "JPEG", quality=92)
        return BG_PATH
    except Exception as exc:
        print(f"[WARN] Arrière-plan impossible: {exc}")
        return None


def load_bg_image(master: tk.Widget, width: int, height: int) -> Optional[PhotoImage]:
    if not BG_PATH.exists():
        return None
    try:
        img = Image.open(BG_PATH).convert("RGB")
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def create_default_background(width: int = 1920, height: int = 1080) -> Image.Image:
    img = Image.new("RGB", (width, height), COLORS["bg"])
    return img


def format_bytes(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PB"


def dhash(image: Image.Image, hash_size: int = 8) -> int:
    image = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    diff = []
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * (hash_size + 1) + col]
            right = pixels[row * (hash_size + 1) + col + 1]
            diff.append(left > right)
    return sum(1 << (i % 8) for i, v in enumerate(diff) if v)


def ahash(image: Image.Image, hash_size: int = 8) -> int:
    image = image.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)
    return sum(1 << i for i, v in enumerate(pixels) if v >= avg)


def phash(image: Image.Image, hash_size: int = 8) -> int:
    try:
        import numpy as np
    except Exception:
        return ahash(image, hash_size)
    size = hash_size * 4
    image = image.convert("L").resize((size, size), Image.Resampling.LANCZOS)
    pixels = np.asarray(image, dtype=np.float32)
    # DCT simplifié
    dct = np.zeros((hash_size, hash_size), dtype=np.float32)
    for u in range(hash_size):
        for v in range(hash_size):
            s = 0.0
            for x in range(size):
                for y in range(size):
                    s += pixels[x, y] * math.cos((2 * x + 1) * u * math.pi / (2 * size)) * \
                         math.cos((2 * y + 1) * v * math.pi / (2 * size))
            dct[u, v] = s
    dctlow = dct[:hash_size, :hash_size]
    avg = (dctlow.sum() - dctlow[0, 0]) / (hash_size * hash_size - 1)
    return sum(1 << i for i, v in enumerate(dctlow.flatten()) if v > avg)


def hamming_distance(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")


def extract_exif(image_path: str) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"Chemin": image_path}
    try:
        img = Image.open(image_path)
        meta["Format"] = img.format
        meta["Mode"] = img.mode
        meta["Dimensions"] = f"{img.width}x{img.height}"
        meta["Taille"] = format_bytes(os.path.getsize(image_path))
        exif = img._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                meta[tag] = str(value)
        else:
            meta["EXIF"] = "Aucune métadonnée EXIF"
    except Exception as exc:
        meta["EXIF_Error"] = str(exc)
    return meta


def try_ocr(image_path: str) -> str:
    try:
        import pytesseract
        img = Image.open(image_path)
        img = ImageOps.grayscale(img)
        return pytesseract.image_to_string(img, lang="eng+fra").strip()
    except Exception as exc:
        return f"[OCR indisponible: {exc}]"


def detect_faces(image_path: str) -> Dict[str, Any]:
    result = {"visages": 0, "details": []}
    try:
        import cv2
        import numpy as np
        img = cv2.imread(image_path)
        if img is None:
            return result
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if not os.path.exists(cascade_path):
            return result
        cascade = cv2.CascadeClassifier(cascade_path)
        faces = cascade.detectMultiScale(gray, 1.1, 4)
        result["visages"] = len(faces)
        for (x, y, w, h) in faces:
            result["details"].append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
    except Exception as exc:
        result["erreur"] = str(exc)
    return result


def extract_frames(video_path: str, count: int = 5) -> List[str]:
    paths: List[str] = []
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            cap.release()
            return paths
        indices = [int(total * i / count) for i in range(1, count + 1)]
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if ok:
                p = CACHE_DIR / f"frame_{uuid.uuid4().hex}.jpg"
                cv2.imwrite(str(p), frame)
                paths.append(str(p))
        cap.release()
    except Exception as exc:
        print(f"[WARN] Extraction vidéo: {exc}")
    return paths


def convert_pdf_page(pdf_path: str, page: int = 0) -> Optional[str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        if page >= len(reader.pages):
            return None
        # On ne peut pas extraire d'image PDF directement sans pdf2image ;
        # on se contente de capturer le texte et on retourne None ici.
        return None
    except Exception:
        return None


def extract_pdf_text(pdf_path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages[:5]):
            text += f"\n--- Page {i+1} ---\n"
            text += page.extract_text() or ""
        return text.strip()
    except Exception as exc:
        return f"[PDF indisponible: {exc}]"


# ---------------------------------------------------------------------------
# STRUCTURES DE DONNÉES
# ---------------------------------------------------------------------------
@dataclass
class Match:
    engine: str
    url: str
    title: str = ""
    source: str = ""
    description: str = ""
    image_url: str = ""
    thumbnail: str = ""
    score: float = 0.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine": self.engine,
            "url": self.url,
            "title": self.title,
            "source": self.source,
            "description": self.description,
            "image_url": self.image_url,
            "thumbnail": self.thumbnail,
            "score": self.score,
            "tags": self.tags,
        }


@dataclass
class AnalysisResult:
    timestamp: str
    file: str
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    hashes: Dict[str, str] = field(default_factory=dict)
    ocr: str = ""
    faces: Dict[str, Any] = field(default_factory=dict)
    matches: List[Match] = field(default_factory=list)
    engines: Dict[str, Any] = field(default_factory=dict)
    pages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "file": self.file,
            "path": self.path,
            "metadata": self.metadata,
            "hashes": self.hashes,
            "ocr": self.ocr,
            "faces": self.faces,
            "matches": [m.to_dict() for m in self.matches],
            "engines": self.engines,
            "pages": self.pages,
        }


# ---------------------------------------------------------------------------
# MOTEUR DE RECHERCHE INVERSÉE
# ---------------------------------------------------------------------------
class ImageSearchEngine:
    def __init__(self, progress_callback: Callable[[float, str], None] = None,
                 log_callback: Callable[[str], None] = None):
        self.progress_callback = progress_callback or (lambda p, msg: None)
        self.log_callback = log_callback or (lambda msg: None)
        self.session = make_session()

    def log(self, message: str) -> None:
        self.log_callback(message)

    def progress(self, value: float, message: str = "") -> None:
        self.progress_callback(value, message)

    def search(self, image_path: str) -> AnalysisResult:
        result = AnalysisResult(
            timestamp=datetime.now().isoformat(),
            file=os.path.basename(image_path),
            path=image_path,
        )

        # 1. Métadonnées
        self.log("[ANALYSE] Extraction des métadonnées EXIF...")
        result.metadata = extract_exif(image_path)
        self.progress(5, "Métadonnées extraites")

        # 2. Hashes
        self.log("[ANALYSE] Calcul des empreintes perceptuelles...")
        img = Image.open(image_path)
        data = open(image_path, "rb").read()
        result.hashes = {
            "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "dhash": str(dhash(img)),
            "ahash": str(ahash(img)),
            "phash": str(phash(img)),
        }
        self.progress(10, "Empreintes calculées")

        # 3. OCR
        self.log("[ANALYSE] Reconnaissance optique de caractères (OCR)...")
        result.ocr = try_ocr(image_path)
        self.progress(15, "OCR terminé")

        # 4. Détection de visages
        self.log("[ANALYSE] Détection de visages...")
        result.faces = detect_faces(image_path)
        self.progress(20, "Analyse faciale terminée")

        # 5. Recherches inversées parallèles
        engines_map = {
            "Google Lens": self.search_google_lens,
            "Yandex Images": self.search_yandex,
            "Bing Visual Search": self.search_bing,
            "TinEye": self.search_tineye,
            "Baidu Images": self.search_baidu,
        }
        base = 20
        span = 70
        step = span / len(engines_map)

        with ThreadPoolExecutor(max_workers=min(len(engines_map), MAX_WORKERS)) as ex:
            futures = {ex.submit(method, image_path): name for name, method in engines_map.items()}
            for idx, future in enumerate(as_completed(futures)):
                name = futures[future]
                self.log(f"[RECHERCHE] Interrogation de {name}...")
                try:
                    engine_res = future.result(timeout=120)
                    result.engines[name] = engine_res
                    if isinstance(engine_res, dict):
                        result.matches.extend(engine_res.get("matches", []))
                except Exception as exc:
                    self.log(f"[ERREUR] {name}: {exc}")
                    result.engines[name] = {"status": "error", "error": str(exc)}
                self.progress(base + (idx + 1) * step, f"{name} terminé")

        # 6. Enrichissement parallèle des pages
        self.log("[INTELLIGENCE] Enrichissement des sources identifiées...")
        result.matches = self.deduplicate_matches(result.matches)
        self.enrich_matches(result.matches)
        self.progress(95, "Sources enrichies")

        # 7. Score / tri
        result.matches.sort(key=lambda m: m.score, reverse=True)
        self.log(f"[TERMINÉ] {len(result.matches)} source(s) potentielle(s) identifiée(s).")
        self.progress(100, "Analyse complète")
        return result

    def deduplicate_matches(self, matches: List[Match]) -> List[Match]:
        seen: set = set()
        unique: List[Match] = []
        for m in matches:
            key = m.url or m.title
            if key and key not in seen:
                seen.add(key)
                unique.append(m)
        return unique

    def enrich_matches(self, matches: List[Match]) -> None:
        def enrich_one(match: Match) -> None:
            if not is_valid_url(match.url):
                return
            try:
                sess = make_session()
                resp = sess.get(match.url, timeout=HTTP_TIMEOUT, verify=False)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                if not match.title:
                    match.title = extract_meta(soup, "og:title") or soup.title.string.strip() if soup.title and soup.title.string else ""
                match.description = extract_meta(soup, "og:description") or extract_meta(soup, "description")
                match.source = urlparse(match.url).netloc
                match.image_url = extract_meta(soup, "og:image")
                if not match.thumbnail:
                    match.thumbnail = extract_meta(soup, "og:image")
                # Tags approximatifs depuis les keywords / catégories
                keywords = extract_meta(soup, "keywords") or extract_meta(soup, "news_keywords")
                if keywords:
                    match.tags = [k.strip() for k in keywords.split(",") if k.strip()][:10]
                # Score heuristique
                score = 50.0
                if match.title:
                    score += 15
                if match.description:
                    score += 15
                if match.tags:
                    score += min(len(match.tags) * 2, 20)
                match.score = min(score, 100.0)
            except Exception as exc:
                self.log(f"[ENRICH] {match.url}: {exc}")
                match.score = 30.0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            list(ex.map(enrich_one, matches[:20]))  # Limiter le nombre d'enrichissements

    # -----------------------------------------------------------------------
    # Google Lens
    # -----------------------------------------------------------------------
    def search_google_lens(self, image_path: str) -> Dict[str, Any]:
        self.log("[GOOGLE] Préparation de l'image...")
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # Endpoint non officiel, expérimental, peut échouer
        url = "https://lens.google.com/upload"
        boundary = "----WebKitFormBoundary" + "".join(random.choices(string.ascii_letters + string.digits, k=16))
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Referer": "https://lens.google.com/",
            "Origin": "https://lens.google.com",
        }
        payload = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="encoded_image"; filename="{os.path.basename(image_path)}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + open(image_path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
        resp = self.session.post(url, headers=headers, data=payload, timeout=HTTP_TIMEOUT, allow_redirects=True)
        matches = self._parse_google_lens_html(resp.text, resp.url)
        return {"status": "ok", "matches": matches, "count": len(matches)}

    def _parse_google_lens_html(self, html: str, base_url: str) -> List[Match]:
        matches: List[Match] = []
        try:
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/url?q=" in href:
                    real = unquote(re.search(r"/url\?q=([^&]+)", href).group(1)) if re.search(r"/url\?q=([^&]+)", href) else href
                else:
                    real = href
                if is_valid_url(real):
                    matches.append(Match(engine="Google Lens", url=real, title=a.get_text(strip=True)[:120]))
            # JSON intégré
            for script in soup.find_all("script"):
                txt = script.string or ""
                for u in re.findall(r'"(https?://[^"]+)"', txt):
                    if is_valid_url(u) and "google" not in urlparse(u).netloc:
                        matches.append(Match(engine="Google Lens", url=u, title="Résultat Google"))
        except Exception as exc:
            self.log(f"[GOOGLE] Parsing: {exc}")
        return self.deduplicate_matches(matches)[:25]

    # -----------------------------------------------------------------------
    # Yandex Images
    # -----------------------------------------------------------------------
    def search_yandex(self, image_path: str) -> Dict[str, Any]:
        self.log("[YANDEX] Upload de l'image...")
        url = "https://yandex.com/images/search"
        with open(image_path, "rb") as f:
            files = {"upfile": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"rpt": "imageview", "format": "json",
                    "request": '{"blocks":[{"block":"b-page_type_search_by_image"}]}'}
            resp = self.session.post(url, files=files, data=data, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        matches: List[Match] = []
        try:
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.select("a.CbirItem"):
                href = a.get("href", "")
                if href:
                    full = urljoin(resp.url, href)
                    title = a.get_text(strip=True) or "Résultat Yandex"
                    matches.append(Match(engine="Yandex Images", url=full, title=title))
            # JSON
            m = re.search(r'"initialState":\s*(\{.*?\})\s*,\s*"config"', resp.text, re.S)
            if m:
                state = json.loads(m.group(1))
                for item in state.get("serpList", {}).get("items", []):
                    snp = item.get("snippet", {})
                    u = snp.get("url", "")
                    if u:
                        matches.append(Match(engine="Yandex Images", url=u, title=snp.get("title", "")))
        except Exception as exc:
            self.log(f"[YANDEX] Parsing: {exc}")
        return {"status": "ok", "matches": self.deduplicate_matches(matches)[:25], "count": len(matches)}

    # -----------------------------------------------------------------------
    # Bing Visual Search
    # -----------------------------------------------------------------------
    def search_bing(self, image_path: str) -> Dict[str, Any]:
        self.log("[BING] Upload de l'image...")
        url = "https://www.bing.com/images/api/custom/knowledge"
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        data = {
            "data": json.dumps({
                "imageInfo": {"url": f"data:image/jpeg;base64,{b64}"},
                "knowledgeRequest": {"invokedSkills": ["ImageByImage"]},
            })
        }
        headers = {"Referer": "https://www.bing.com/images/search"}
        resp = self.session.post(url, data=data, headers=headers, timeout=HTTP_TIMEOUT)
        matches: List[Match] = []
        try:
            js = resp.json()
            for tag in js.get("tags", []):
                for action in tag.get("actions", []):
                    if action.get("actionType") in ("VisualSearch", "ImageByImage"):
                        for r in action.get("data", {}).get("value", []):
                            matches.append(Match(
                                engine="Bing Visual Search",
                                url=r.get("contentUrl", ""),
                                title=r.get("name", "Résultat Bing"),
                                thumbnail=r.get("thumbnailUrl", ""),
                            ))
        except Exception as exc:
            self.log(f"[BING] Parsing: {exc}")
        return {"status": "ok", "matches": self.deduplicate_matches(matches)[:25], "count": len(matches)}

    # -----------------------------------------------------------------------
    # TinEye
    # -----------------------------------------------------------------------
    def search_tineye(self, image_path: str) -> Dict[str, Any]:
        self.log("[TINEYE] Upload de l'image...")
        url = "https://tineye.com/search"
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            resp = self.session.post(url, files=files, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        matches: List[Match] = []
        try:
            soup = BeautifulSoup(resp.text, "lxml")
            for result in soup.select(".match"):
                a = result.select_one("a")
                if not a:
                    continue
                href = a.get("href", "")
                if href:
                    matches.append(Match(engine="TinEye", url=urljoin(resp.url, href), title=a.get_text(strip=True)[:120]))
        except Exception as exc:
            self.log(f"[TINEYE] Parsing: {exc}")
        return {"status": "ok", "matches": self.deduplicate_matches(matches)[:25], "count": len(matches)}

    # -----------------------------------------------------------------------
    # Baidu Images
    # -----------------------------------------------------------------------
    def search_baidu(self, image_path: str) -> Dict[str, Any]:
        self.log("[BAIDU] Upload de l'image...")
        # Baidu requiert un POST multipart sur https://graph.baidu.com/upload
        url = "https://graph.baidu.com/upload"
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            resp = self.session.post(url, files=files, timeout=HTTP_TIMEOUT)
        matches: List[Match] = []
        try:
            js = resp.json()
            data = js.get("data", {})
            for item in data.get("result", []):
                matches.append(Match(
                    engine="Baidu Images",
                    url=item.get("fromPageTitle", ""),
                    title=item.get("fromPageTitle", "Résultat Baidu"),
                    thumbnail=item.get("thumbURL", ""),
                ))
        except Exception as exc:
            self.log(f"[BAIDU] Parsing: {exc}")
        return {"status": "ok", "matches": self.deduplicate_matches(matches)[:25], "count": len(matches)}


# ---------------------------------------------------------------------------
# INTERFACE: FENÊTRE DE CONNEXION
# ---------------------------------------------------------------------------
class LoginWindow(Toplevel):
    def __init__(self, master: tk.Tk, on_success: Callable[[], None]):
        super().__init__(master)
        self.master = master
        self.on_success = on_success
        self.title("FBI Secure Access")
        self.geometry("800x600")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.grab_set()

        self.bg_image = load_bg_image(self, 800, 600)
        self.canvas = Canvas(self, width=800, height=600, highlightthickness=0, bg=COLORS["bg"])
        self.canvas.pack(fill="both", expand=True)
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

    def build_ui(self) -> None:
        frame = Frame(self.canvas, bg=COLORS["panel"], padx=45, pady=45,
                      highlightbackground=COLORS["gold"], highlightthickness=2)
        self.canvas.create_window(400, 300, window=frame)

        Label(frame, text="🔒 FBI INTELLIGENCE TERMINAL", font=FONTS["title"],
              fg=COLORS["gold"], bg=COLORS["panel"]).pack(pady=(0, 8))
        Label(frame, text="SECURE ACCESS REQUIRED", font=FONTS["header"],
              fg=COLORS["fg"], bg=COLORS["panel"]).pack(pady=(0, 25))

        Label(frame, text="Agent ID", font=FONTS["body"], fg=COLORS["fg"], bg=COLORS["panel"]).pack(anchor="w")
        self.entry_user = Entry(frame, font=FONTS["body"], fg=COLORS["fg"], bg=COLORS["bg"],
                                insertbackground=COLORS["gold"], highlightbackground=COLORS["gold"], highlightthickness=1)
        self.entry_user.pack(fill="x", pady=(0, 12))

        Label(frame, text="Passcode", font=FONTS["body"], fg=COLORS["fg"], bg=COLORS["panel"]).pack(anchor="w")
        self.entry_pass = Entry(frame, show="●", font=FONTS["body"], fg=COLORS["fg"], bg=COLORS["bg"],
                                insertbackground=COLORS["gold"], highlightbackground=COLORS["gold"], highlightthickness=1)
        self.entry_pass.pack(fill="x", pady=(0, 18))

        Button(frame, text="AUTHENTICATE", font=FONTS["header"], fg=COLORS["bg"], bg=COLORS["gold"],
               activebackground="#c59b2d", cursor="hand2", command=self.check_login).pack(fill="x", pady=(0, 10))

        self.lbl_status = Label(frame, text="", font=FONTS["body"], fg=COLORS["danger"], bg=COLORS["panel"])
        self.lbl_status.pack()

        self.entry_user.insert(0, DEFAULT_USERNAME)
        self.entry_pass.insert(0, DEFAULT_PASSWORD)

    def check_login(self) -> None:
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()
        if user == DEFAULT_USERNAME and pwd == DEFAULT_PASSWORD:
            self.destroy()
            self.on_success()
        else:
            self.lbl_status.config(text="❌ IDENTIFIANTS INVALIDES")

    def quit_app(self) -> None:
        self.master.destroy()


# ---------------------------------------------------------------------------
# INTERFACE: FENÊTRE PRINCIPALE
# ---------------------------------------------------------------------------
class FBIApp(Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1400x900")
        self.configure(bg=COLORS["bg"])
        self.minsize(1200, 800)

        self.bg_image = load_bg_image(self, 1400, 900)
        self.canvas = Canvas(self, width=1400, height=900, highlightthickness=0, bg=COLORS["bg"])
        self.canvas.pack(fill="both", expand=True)
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.current_image_path: Optional[str] = None
        self.thumb_image: Optional[PhotoImage] = None
        self.results_data: Optional[AnalysisResult] = None
        self.searching = False

        self.build_ui()
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event: tk.Event) -> None:
        if event.widget is self and self.bg_image:
            w, h = event.width, event.height
            try:
                img = Image.open(BG_PATH).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(img)
                self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
                self.canvas.lower("all")
            except Exception:
                pass

    def build_ui(self) -> None:
        container = Frame(self.canvas, bg=COLORS["panel"], padx=20, pady=20,
                          highlightbackground=COLORS["gold"], highlightthickness=2)
        self.canvas.create_window(700, 450, window=container, width=1350, height=850)

        # En-tête
        Label(container, text="🇺🇸 FBI IMAGE INTELLIGENCE TERMINAL",
              font=("Consolas", 22, "bold"), fg=COLORS["gold"], bg=COLORS["panel"]).pack()
        Label(container, text="Système avancé d'analyse forensique et de recherche inverse d'images",
              font=FONTS["body"], fg=COLORS["fg"], bg=COLORS["panel"]).pack(pady=(0, 15))

        # Corps
        body = Frame(container, bg=COLORS["panel"])
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Panneau gauche
        left = Frame(body, bg=COLORS["panel2"], padx=12, pady=12,
                     highlightbackground=COLORS["accent"], highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(4, weight=1)

        Label(left, text="SOURCE IMAGE", font=FONTS["header"], fg=COLORS["gold"], bg=COLORS["panel2"]).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.preview = Label(left, bg=COLORS["bg"], width=42, height=16,
                             highlightbackground=COLORS["accent"], highlightthickness=1)
        self.preview.grid(row=1, column=0, pady=(0, 10))
        self.preview.config(text="[AUCUNE IMAGE]", fg=COLORS["fg"], font=FONTS["body"])

        btn_frame = Frame(left, bg=COLORS["panel2"])
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        Button(btn_frame, text="📁 CHARGER", font=FONTS["body"], fg=COLORS["bg"], bg=COLORS["gold"],
               cursor="hand2", command=self.upload_image).pack(side="left", fill="x", expand=True, padx=(0, 5))
        Button(btn_frame, text="🌐 URL", font=FONTS["body"], fg=COLORS["fg"], bg=COLORS["accent"],
               cursor="hand2", command=self.load_from_url).pack(side="left", fill="x", expand=True)

        self.lbl_meta = Label(left, text="Métadonnées: ---", font=FONTS["mono"], fg=COLORS["fg"],
                              bg=COLORS["panel2"], justify="left", anchor="nw")
        self.lbl_meta.grid(row=3, column=0, sticky="nsew", pady=(0, 10))

        self.btn_search = Button(left, text="🔍 LANCER LA RECHERCHE INVERSE", font=FONTS["header"],
                                 fg=COLORS["bg"], bg=COLORS["accent"], activebackground="#162d73",
                                 cursor="hand2", command=self.start_search)
        self.btn_search.grid(row=5, column=0, sticky="ew")

        # Panneau droit
        right = Frame(body, bg=COLORS["panel2"], padx=12, pady=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(5, weight=1)
        right.grid_columnconfigure(0, weight=1)

        Label(right, text="PROGRESSION DE L'ANALYSE", font=FONTS["header"], fg=COLORS["gold"], bg=COLORS["panel2"]).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.progress_var = StringVar(value="0%")
        self.progress = ttk.Progressbar(right, orient="horizontal", mode="determinate", maximum=100, length=600)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        self.lbl_progress = Label(right, textvariable=self.progress_var, font=FONTS["body"], fg=COLORS["ok"], bg=COLORS["panel2"])
        self.lbl_progress.grid(row=2, column=0, sticky="w", pady=(0, 10))

        # Filtres
        filter_frame = Frame(right, bg=COLORS["panel2"])
        filter_frame.grid(row=3, column=0, sticky="w", pady=(0, 8))
        Label(filter_frame, text="Moteurs:", font=FONTS["body"], fg=COLORS["fg"], bg=COLORS["panel2"]).pack(side="left")
        self.engine_vars: Dict[str, BooleanVar] = {}
        for name in ("Google Lens", "Yandex Images", "Bing Visual Search", "TinEye", "Baidu Images"):
            var = BooleanVar(value=True)
            self.engine_vars[name] = var
            Checkbutton(filter_frame, text=name, variable=var, font=FONTS["small"],
                        fg=COLORS["fg"], bg=COLORS["panel2"], selectcolor=COLORS["bg"]).pack(side="left", padx=(8, 0))

        Button(right, text="💾 EXPORT JSON", font=FONTS["body"], fg=COLORS["bg"], bg=COLORS["gold"],
               cursor="hand2", command=self.export_json).grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # Notebook
        notebook = ttk.Notebook(right)
        notebook.grid(row=5, column=0, sticky="nsew")

        # Onglet résultats
        tab_results = Frame(notebook, bg=COLORS["panel2"])
        notebook.add(tab_results, text="Résultats web")
        cols = ("rank", "engine", "score", "title", "source", "url")
        self.tree = ttk.Treeview(tab_results, columns=cols, show="headings")
        for col, title, width in zip(cols, ("#", "Moteur", "Score", "Titre / Source", "Site", "URL"), (40, 100, 70, 300, 180, 350)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w" if col in ("title", "source", "url") else "center")
        vsb = Scrollbar(tab_results, orient="vertical", command=self.tree.yview)
        hsb = Scrollbar(tab_results, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tab_results.grid_rowconfigure(0, weight=1)
        tab_results.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self.open_url)

        # Onglet détails
        tab_details = Frame(notebook, bg=COLORS["panel2"])
        notebook.add(tab_details, text="Détails source")
        self.txt_details = Text(tab_details, wrap="word", font=FONTS["mono"], bg=COLORS["bg"],
                                fg=COLORS["fg"], insertbackground=COLORS["gold"], state="disabled")
        self.txt_details.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.show_details)

        # Onglet logs
        tab_logs = Frame(notebook, bg=COLORS["panel2"])
        notebook.add(tab_logs, text="Journal technique")
        self.txt_logs = Text(tab_logs, wrap="word", font=FONTS["mono"], bg=COLORS["bg"],
                             fg=COLORS["fg"], insertbackground=COLORS["gold"], state="disabled")
        self.txt_logs.pack(fill="both", expand=True)

        # Onglet JSON
        tab_json = Frame(notebook, bg=COLORS["panel2"])
        notebook.add(tab_json, text="Rapport JSON")
        self.txt_json = Text(tab_json, wrap="word", font=FONTS["mono"], bg=COLORS["bg"],
                             fg=COLORS["fg"], insertbackground=COLORS["gold"], state="disabled")
        self.txt_json.pack(fill="both", expand=True)

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", thickness=22, background=COLORS["gold"], troughcolor=COLORS["bg"],
                        bordercolor=COLORS["accent"], lightcolor=COLORS["gold"], darkcolor=COLORS["gold"])
        style.configure("TNotebook", background=COLORS["panel2"], tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", font=FONTS["body"], background=COLORS["accent"],
                        foreground=COLORS["fg"], padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", COLORS["gold"])],
                  foreground=[("selected", COLORS["bg"])])
        style.configure("Treeview", background=COLORS["bg"], foreground=COLORS["fg"],
                        fieldbackground=COLORS["bg"], font=FONTS["mono"], rowheight=26)
        style.configure("Treeview.Heading", background=COLORS["accent"], foreground=COLORS["fg"], font=FONTS["body"])

    def upload_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Sélectionner un média",
            filetypes=[
                ("Tous médias", "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff *.mp4 *.avi *.mov *.mkv *.pdf"),
                ("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff"),
                ("Vidéos", "*.mp4 *.avi *.mov *.mkv"),
                ("PDF", "*.pdf"),
                ("Tous fichiers", "*.*"),
            ]
        )
        if not path:
            return
        self.process_input(path)

    def load_from_url(self) -> None:
        url = tk.simpledialog.askstring("Image URL", "Entrez l'URL de l'image:")
        if not url:
            return
        try:
            r = requests.get(url, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            ext = mimetypes.guess_extension(r.headers.get("content-type", "").split(";")[0]) or ".jpg"
            p = CACHE_DIR / f"download_{uuid.uuid4().hex}{ext}"
            p.write_bytes(r.content)
            self.process_input(str(p))
        except Exception as exc:
            messagebox.showerror("Erreur", f"Téléchargement impossible: {exc}")

    def process_input(self, path: str) -> None:
        self.current_image_path = path
        self.log(f"Fichier chargé: {path}")

        ext = Path(path).suffix.lower()
        display_path = path
        pages: List[str] = []

        if ext in (".mp4", ".avi", ".mov", ".mkv"):
            self.log("[INFO] Vidéo détectée, extraction des frames clés...")
            pages = extract_frames(path, count=5)
            if pages:
                display_path = pages[0]
                self.current_image_path = display_path
            else:
                messagebox.showwarning("Vidéo", "Impossible d'extraire des frames.")
                return
        elif ext == ".pdf":
            self.log("[INFO] PDF détecté, extraction du texte...")
            txt = extract_pdf_text(path)
            self.log(f"[PDF] Texte extrait ({len(txt)} caractères)")
            pages = []

        # Aperçu
        try:
            img = Image.open(display_path)
            img.thumbnail((360, 280), Image.Resampling.LANCZOS)
            self.thumb_image = ImageTk.PhotoImage(img)
            self.preview.config(image=self.thumb_image, text="")
        except Exception as exc:
            self.preview.config(text=f"Erreur aperçu:\n{exc}")

        # Métadonnées
        meta = extract_exif(display_path)
        lines = [f"{k}: {v}" for k, v in meta.items()]
        self.lbl_meta.config(text="\n".join(lines[:14]))

    def start_search(self) -> None:
        if not self.current_image_path:
            messagebox.showwarning("Avertissement", "Veuillez d'abord charger une image.")
            return
        if self.searching:
            return
        self.searching = True
        self.btn_search.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self.run_search, daemon=True).start()

    def run_search(self) -> None:
        engine = ImageSearchEngine(progress_callback=self.update_progress, log_callback=self.log)
        try:
            self.results_data = engine.search(self.current_image_path)
            self.after(0, self.populate_results, self.results_data)
        except Exception as exc:
            self.log(f"[FATAL] {exc}")
        finally:
            self.searching = False
            self.after(0, lambda: self.btn_search.config(state="normal"))

    def update_progress(self, value: float, message: str = "") -> None:
        def animate(target: float) -> None:
            current = float(self.progress["value"])
            diff = target - current
            if abs(diff) > 0.3:
                self.progress["value"] = current + diff * 0.18
                self.progress_var.set(f"{self.progress['value']:.1f}% - {message}")
                self.after(4, animate, target)
            else:
                self.progress["value"] = target
                self.progress_var.set(f"{target:.1f}% - {message}")
        self.after(0, animate, value)

    def populate_results(self, data: AnalysisResult) -> None:
        for rank, match in enumerate(data.matches, 1):
            self.tree.insert("", "end", iid=str(rank), values=(
                rank,
                match.engine,
                f"{match.score:.0f}",
                (match.title or "")[:80],
                match.source,
                (match.url or "")[:90],
            ))

        # JSON
        self.txt_json.config(state="normal")
        self.txt_json.delete("1.0", "end")
        self.txt_json.insert("1.0", json.dumps(data.to_dict(), indent=2, ensure_ascii=False, default=str))
        self.txt_json.config(state="disabled")

        if not data.matches:
            messagebox.showinfo("Analyse terminée",
                                "Aucune correspondance distante trouvée.\n"
                                "Les moteurs publics sans API peuvent bloquer les requêtes automatisées.")

    def show_details(self, event=None) -> None:
        selection = self.tree.selection()
        if not selection or not self.results_data:
            return
        idx = int(selection[0]) - 1
        if idx < 0 or idx >= len(self.results_data.matches):
            return
        match = self.results_data.matches[idx]
        self.txt_details.config(state="normal")
        self.txt_details.delete("1.0", "end")
        self.txt_details.insert("1.0", f"""
Moteur      : {match.engine}
Score       : {match.score:.1f}/100
Titre       : {match.title}
Site source : {match.source}
URL         : {match.url}
Image       : {match.image_url}
Miniature   : {match.thumbnail}
Tags        : {', '.join(match.tags)}
Description : {match.description}
""")
        self.txt_details.config(state="disabled")

    def export_json(self) -> None:
        if not self.results_data:
            messagebox.showwarning("Export", "Aucun résultat à exporter.")
            return
        path = REPORT_DIR / f"rapport_fbi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(self.results_data.to_dict(), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        messagebox.showinfo("Export", f"Rapport enregistré:\n{path}")

    def log(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] {message}\n"
        self.txt_logs.config(state="normal")
        self.txt_logs.insert("end", line)
        self.txt_logs.see("end")
        self.txt_logs.config(state="disabled")

    def open_url(self, event: tk.Event) -> None:
        item = self.tree.selection()
        if not item:
            return
        url = self.tree.item(item[0], "values")[5]
        if url and url.startswith("http"):
            webbrowser.open(url)


# ---------------------------------------------------------------------------
# POINT D'ENTRÉE
# ---------------------------------------------------------------------------
def main() -> None:
    root = tk.Tk()
    root.withdraw()

    # Si l'utilisateur a fourni l'image en argument, l'utiliser comme fond
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        ensure_background(Path(sys.argv[1]).read_bytes())
    elif not BG_PATH.exists():
        create_default_background().save(BG_PATH, "JPEG", quality=90)

    def show_app() -> None:
        app = FBIApp()
        root.destroy()
        app.mainloop()

    LoginWindow(root, show_app)
    root.mainloop()


if __name__ == "__main__":
    main()
