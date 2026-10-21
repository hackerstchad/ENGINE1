# -*- coding: utf-8 -*-
"""
Moteur de recherche universel - Cœur de l'application.
Coordonne les recherches sur toutes les sources disponibles.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from search_sources import SOURCES, SEARCH_FUNCTIONS, build_web_result


class SearchEngine:
    """Moteur de recherche multi-sources."""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers

    def search(self, query: str, source_name: str = "All", limit: int = 5,
               progress_callback=None):
        """Lance une recherche sur les sources filtrées."""
        if source_name == "All" or source_name not in SOURCES:
            selected = list(SOURCES.keys())
        else:
            selected = [source_name]

        results = []
        total = len(selected)
        completed = 0
        lock = threading.Lock()

        def worker(name):
            nonlocal completed
            meta = SOURCES[name]
            func = SEARCH_FUNCTIONS.get(name)
            local_results = []
            try:
                if func:
                    raw = func(query, limit)
                else:
                    raw = [build_web_result(name, query)]
                for item in raw:
                    item["source"] = name
                    item["category"] = meta.get("category", "Autre")
                    item["icon"] = meta.get("icon", "")
                    item["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    local_results.append(item)
            except Exception:
                pass
            with lock:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, name)
            return local_results

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(worker, name): name for name in selected}
            for future in as_completed(futures):
                try:
                    results.extend(future.result())
                except Exception:
                    pass

        return results
