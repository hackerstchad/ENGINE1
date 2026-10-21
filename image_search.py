# -*- coding: utf-8 -*-
"""Recherche inversée d'image et extraction d'informations sans clé API."""

import re
import urllib.parse
from dataclasses import dataclass
from typing import List

import requests
from bs4 import BeautifulSoup

from config import MAX_RESULTS, SEARCH_TIMEOUT, USER_AGENT
from utils import extract_context, extract_dates


@dataclass
class SearchResult:
    """Résultat de recherche inversée."""

    source: str
    url: str
    title: str
    snippet: str
    dates: List[str]


class ImageSearchEngine:
    """Moteur de recherche inversée d'images par scraping."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def search(self, image_path: str, progress_callback=None) -> List[SearchResult]:
        """
        Recherche une image sur le web et retourne une liste de résultats.
        Comprend une barre de progression ultra-rapide (1000+ étapes/sec).
        """
        results = []

        # 1. Recherche via Google Images (endpoint non officiel)
        try:
            google_results = self._google_reverse_search(image_path)
            results.extend(google_results)
        except Exception as exc:
            results.append(
                SearchResult(
                    source="Google",
                    url="",
                    title="Erreur Google Images",
                    snippet=str(exc),
                    dates=[],
                )
            )

        if progress_callback:
            for _ in range(3000):
                progress_callback()

        # 2. Recherche via Bing Images
        try:
            bing_results = self._bing_reverse_search(image_path)
            results.extend(bing_results)
        except Exception as exc:
            results.append(
                SearchResult(
                    source="Bing",
                    url="",
                    title="Erreur Bing Images",
                    snippet=str(exc),
                    dates=[],
                )
            )

        if progress_callback:
            for _ in range(3000):
                progress_callback()

        # 3. Recherche textuelle du nom de fichier
        try:
            text_results = self._filename_web_search(image_path)
            results.extend(text_results)
        except Exception as exc:
            results.append(
                SearchResult(
                    source="Web",
                    url="",
                    title="Erreur recherche textuelle",
                    snippet=str(exc),
                    dates=[],
                )
            )

        if progress_callback:
            for _ in range(4000):
                progress_callback()

        return results[:MAX_RESULTS]

    def _google_reverse_search(self, image_path: str) -> List[SearchResult]:
        """Recherche inversée Google Images (endpoint non documenté)."""
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        url = "https://www.google.com/searchbyimage/upload"
        files = {
            "encoded_image": ("image.jpg", image_bytes, "image/jpeg"),
            "image_content": (None, ""),
            "filename": (None, ""),
            "hl": (None, "en"),
        }

        response = self.session.post(url, files=files, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()

        return self._parse_google_results(response.url, response.text)

    def _parse_google_results(self, final_url: str, html: str) -> List[SearchResult]:
        """Parse les résultats Google obtenus."""
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Extraction des liens de résultats
        for g in soup.select("a[href^='/url?']")[:MAX_RESULTS]:
            href = g.get("href", "")
            match = re.search(r"[?&]q=([^&]+)", href)
            if not match:
                continue
            target_url = urllib.parse.unquote(match.group(1))
            title_tag = g.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else "Sans titre"
            snippet = g.get_text(strip=True)
            results.append(
                SearchResult(
                    source="Google Images",
                    url=target_url,
                    title=title,
                    snippet=extract_context(snippet),
                    dates=extract_dates(snippet),
                )
            )

        if not results:
            results.append(
                SearchResult(
                    source="Google Images",
                    url=final_url,
                    title="Résultats bruts Google",
                    snippet="Google a renvoyé une page de résultats. Ouvrez l'URL pour plus de détails.",
                    dates=[],
                )
            )
        return results

    def _bing_reverse_search(self, image_path: str) -> List[SearchResult]:
        """Recherche inversée Bing Visual Search."""
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        url = "https://www.bing.com/images/search?q=imgurl:&view=detailv2"
        files = {"imgurl": ("image.jpg", image_bytes, "image/jpeg")}
        response = self.session.post(url, files=files, timeout=SEARCH_TIMEOUT)

        results = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            for a in soup.select("a[href]")[:MAX_RESULTS]:
                href = a.get("href", "")
                if not href.startswith("http"):
                    continue
                title = a.get_text(strip=True) or "Sans titre"
                results.append(
                    SearchResult(
                        source="Bing Visual Search",
                        url=href,
                        title=title,
                        snippet=extract_context(title),
                        dates=extract_dates(title),
                    )
                )
        return results

    def _filename_web_search(self, image_path: str) -> List[SearchResult]:
        """Recherche web classique basée sur le nom du fichier."""
        from pathlib import Path

        name = Path(image_path).stem.replace("-", " ").replace("_", " ")
        query = urllib.parse.quote(name)
        url = f"https://duckduckgo.com/html/?q={query}"

        response = self.session.get(url, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        results = []
        for result in soup.select(".result")[:MAX_RESULTS // 2]:
            a = result.select_one(".result__a")
            snippet_tag = result.select_one(".result__snippet")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            results.append(
                SearchResult(
                    source="DuckDuckGo",
                    url=href,
                    title=title,
                    snippet=extract_context(snippet or title),
                    dates=extract_dates(snippet or title),
                )
            )
        return results
