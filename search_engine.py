#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Search Engine - Interface Tkinter Avancée
Auteur  : CodePal
Version : 1.0.0
Fichier : search_engine.py

Description :
    Interface desktop blanche minimaliste permettant de lancer des recherches
    simultanées sur plus de 30 sources publiques (académique, code, images,
    vidéos, cartes, archives, réseaux sociaux). Les résultats s'affichent dans
    un tableau avec images automatiques, résumé et profil utilisateur sélectionné.

Fonctionnalités :
    - Recherche multi-sources sans clé API (sources ouvertes)
    - Affichage de résultats sous forme de tableau avec vignettes
    - Sélection de profil utilisateur depuis un fichier JSON
    - Thème blanc minimaliste avec titre noir "Search Engine"
    - Résumé automatique des résultats trouvés
    - Onglets par catégorie : Academic, Code, Images, Videos, Maps, Archives
    - Export CSV des résultats
    - Historique des recherches
    - Prévisualisation d'images et détails
    - Barre de recherche centrale avec raccourcis clavier

Sources intégrées :
    1. Google Scholar          20. Docker Hub
    2. Semantic Scholar        21. Hugging Face
    3. PubMed                  22. Google Images
    4. arXiv                   23. Bing Images
    5. CORE                    24. Flickr
    6. BASE                    25. Unsplash
    7. OpenAlex                26. Pexels
    8. Crossref                27. YouTube
    9. DOAJ                    28. Vimeo
   10. ERIC                    29. Dailymotion
   11. JSTOR                   30. Internet Archive
   12. GitHub Code Search      31. Google Maps
   13. Sourcegraph             32. OpenStreetMap
   14. grep.app                33. Apple Maps
   15. GitLab                  34. Bing Maps
   16. Stack Overflow          35. HERE WeGo
   17. npm                     36. MapQuest
   18. PyPI                    37. Yandex Maps
   19. crates.io               38. Baidu Maps
"""

import os
import sys
import json
import csv
import time
import re
import io
import threading
from datetime import datetime
from tkinter import (
    Tk, Toplevel, Frame, Label, Entry, Button, Text, Listbox,
    Scrollbar, Canvas, StringVar, Menu, messagebox, filedialog, ttk
)
from tkinter.font import Font

import requests
from PIL import Image, ImageTk, ImageDraw, ImageFont

from utils import (
    COLOR_BG, COLOR_FG, COLOR_FG_SECONDARY, COLOR_ACCENT, COLOR_BORDER,
    COLOR_ROW_ODD, COLOR_ROW_EVEN, COLOR_HIGHLIGHT, APP_NAME, APP_VERSION,
    APP_AUTHOR, DEFAULT_PROFILE_FILE, HISTORY_FILE, EXPORT_DIR, CACHE_DIR,
    CATEGORIES, safe_url_open, truncate_text, get_current_timestamp,
    slugify, load_json_file, save_json_file, download_image,
    create_placeholder_image, fetch_image_from_url
)
from search_sources import SOURCES
from search_engine_core import SearchEngine


# ---------------------------------------------------------------------------
# CARTE DE PROFIL
# ---------------------------------------------------------------------------
class ProfileCard(Frame):
    """Carte affichant le profil utilisateur actif."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, highlightbackground=COLOR_BORDER,
                         highlightthickness=1, **kwargs)
        self.image_label = Label(self, bg=COLOR_BG)
        self.image_label.pack(pady=(15, 10))
        self.name_label = Label(self, text="Invité", bg=COLOR_BG, fg=COLOR_FG,
                                font=("Segoe UI", 14, "bold"))
        self.name_label.pack()
        self.role_label = Label(self, text="Visiteur", bg=COLOR_BG, fg=COLOR_FG_SECONDARY,
                                font=("Segoe UI", 10))
        self.role_label.pack()
        self.bio_label = Label(self, text="", bg=COLOR_BG, fg=COLOR_FG_SECONDARY,
                               font=("Segoe UI", 9), wraplength=220, justify="center")
        self.bio_label.pack(pady=(10, 15))
        self.current_image = None

    def set_profile(self, profile: dict):
        self.name_label.config(text=profile.get("name", "Invité"))
        self.role_label.config(text=profile.get("role", "Visiteur"))
        self.bio_label.config(text=profile.get("bio", ""))
        avatar_url = profile.get("avatar", "")
        self.current_image = fetch_image_from_url(avatar_url)
        self.image_label.config(image=self.current_image)
        self.image_label.image = self.current_image


# ---------------------------------------------------------------------------
# TABLEAU DE RÉSULTATS
# ---------------------------------------------------------------------------
class ResultsTable(Frame):
    """Tableau scrollable affichant les résultats de recherche."""

    def __init__(self, parent, on_select=None, on_open=None, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self.on_select = on_select
        self.on_open = on_open
        self.rows = []
        self.image_cache = {}

        self.canvas = Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg=COLOR_BG)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        for row in self.rows:
            row.destroy()
        self.rows = []
        self.image_cache = {}
        self.canvas.yview_moveto(0)

    def add_result(self, result: dict):
        bg_color = COLOR_ROW_EVEN if len(self.rows) % 2 == 0 else COLOR_ROW_ODD
        row_frame = Frame(self.scrollable_frame, bg=bg_color, highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        row_frame.pack(fill="x", pady=2, padx=2)

        image_key = result.get("source", "") + str(len(self.rows))
        image_label = Label(row_frame, bg=bg_color)
        image_label.pack(side="left", padx=8, pady=8)

        image_url = result.get("image")
        if image_url:
            self.image_cache[image_key] = download_image(image_url, size=(64, 64))
        if not self.image_cache.get(image_key):
            self.image_cache[image_key] = create_placeholder_image((64, 64), result.get("source", "")[:1])
        image_label.config(image=self.image_cache[image_key])
        image_label.image = self.image_cache[image_key]

        content_frame = Frame(row_frame, bg=bg_color)
        content_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        title_text = result.get("title", "Sans titre")
        title_lbl = Label(content_frame, text=title_text, bg=bg_color, fg=COLOR_FG,
                          font=("Segoe UI", 11, "bold"), anchor="w", justify="left", wraplength=500)
        title_lbl.pack(fill="x")

        snippet_lbl = Label(content_frame, text=result.get("snippet", ""), bg=bg_color, fg=COLOR_FG_SECONDARY,
                            font=("Segoe UI", 9), anchor="w", justify="left", wraplength=500)
        snippet_lbl.pack(fill="x", pady=(2, 0))

        meta_lbl = Label(content_frame, text=f"{result.get('source', '')} • {result.get('meta', '')}",
                         bg=bg_color, fg=COLOR_ACCENT, font=("Segoe UI", 8), anchor="w")
        meta_lbl.pack(fill="x", pady=(2, 0))

        btn_frame = Frame(row_frame, bg=bg_color)
        btn_frame.pack(side="right", padx=8, pady=8)

        open_btn = Button(btn_frame, text="Ouvrir", bg=COLOR_ACCENT, fg="white", relief="flat",
                          font=("Segoe UI", 9), cursor="hand2",
                          command=lambda r=result: self._open_result(r))
        open_btn.pack(pady=2)

        detail_btn = Button(btn_frame, text="Détails", bg=COLOR_BG, fg=COLOR_FG, relief="flat",
                            font=("Segoe UI", 9), cursor="hand2",
                            command=lambda r=result: self._show_details(r))
        detail_btn.pack(pady=2)

        row_frame.bind("<Button-1>", lambda e, r=result: self._select_result(r))
        for child in row_frame.winfo_children():
            child.bind("<Button-1>", lambda e, r=result: self._select_result(r))

        self.rows.append(row_frame)

    def _select_result(self, result):
        if self.on_select:
            self.on_select(result)

    def _open_result(self, result):
        url = result.get("url", "")
        if url:
            safe_url_open(url)
        if self.on_open:
            self.on_open(result)

    def _show_details(self, result):
        window = Toplevel(self)
        window.title("Détails du résultat")
        window.geometry("600x500")
        window.configure(bg=COLOR_BG)

        title = Label(window, text=result.get("title", "Sans titre"), bg=COLOR_BG, fg=COLOR_FG,
                      font=("Segoe UI", 14, "bold"), wraplength=560, justify="left")
        title.pack(padx=20, pady=(20, 10), anchor="w")

        source_lbl = Label(window, text=f"Source : {result.get('source', '')} {result.get('icon', '')}",
                           bg=COLOR_BG, fg=COLOR_ACCENT, font=("Segoe UI", 10))
        source_lbl.pack(padx=20, pady=2, anchor="w")

        meta_lbl = Label(window, text=f"Métadonnées : {result.get('meta', '')}", bg=COLOR_BG,
                         fg=COLOR_FG_SECONDARY, font=("Segoe UI", 10))
        meta_lbl.pack(padx=20, pady=2, anchor="w")

        url_lbl = Label(window, text=f"URL : {result.get('url', '')}", bg=COLOR_BG, fg=COLOR_FG_SECONDARY,
                        font=("Segoe UI", 9), wraplength=560, justify="left")
        url_lbl.pack(padx=20, pady=2, anchor="w")

        snippet = Text(window, wrap="word", bg=COLOR_ROW_ODD, fg=COLOR_FG, font=("Segoe UI", 10),
                       relief="flat", padx=10, pady=10, height=12)
        snippet.pack(fill="both", expand=True, padx=20, pady=10)
        snippet.insert("1.0", result.get("snippet", "Pas de description."))
        snippet.config(state="disabled")

        btn_frame = Frame(window, bg=COLOR_BG)
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        open_btn = Button(btn_frame, text="Ouvrir dans le navigateur", bg=COLOR_ACCENT, fg="white",
                          relief="flat", font=("Segoe UI", 10), cursor="hand2",
                          command=lambda: safe_url_open(result.get("url", "")))
        open_btn.pack(side="left", padx=(0, 10))

        close_btn = Button(btn_frame, text="Fermer", bg=COLOR_BG, fg=COLOR_FG, relief="flat",
                           font=("Segoe UI", 10), cursor="hand2", command=window.destroy)
        close_btn.pack(side="left")


# ---------------------------------------------------------------------------
# BARRE DE PROGRESSION
# ---------------------------------------------------------------------------
class ProgressBar(Frame):
    """Barre de progression simple avec texte."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self.canvas = Canvas(self, bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER, height=20)
        self.canvas.pack(fill="x", expand=True)
        self.rect = self.canvas.create_rectangle(0, 0, 0, 20, fill=COLOR_ACCENT, outline="")
        self.text = self.canvas.create_text(10, 10, anchor="w", text="Prêt", fill=COLOR_FG, font=("Segoe UI", 9))

    def set_progress(self, value: float, text: str = ""):
        width = self.canvas.winfo_width()
        fill_width = max(0, min(width, width * (value / 100.0)))
        self.canvas.coords(self.rect, 0, 0, fill_width, 20)
        self.canvas.itemconfig(self.text, text=text)


# ---------------------------------------------------------------------------
# FENÊTRE PRINCIPALE
# ---------------------------------------------------------------------------
class SearchEngineApp:
    """Application principale de moteur de recherche universel."""

    def __init__(self, root: Tk):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(1100, 700)

        self.engine = SearchEngine()
        self.current_results = []
        self.current_query = ""
        self.profiles = []
        self.current_profile = None
        self.search_history = load_json_file(HISTORY_FILE, [])

        self._build_menu()
        self._build_header()
        self._build_main_layout()
        self._build_footer()
        self._load_profiles(DEFAULT_PROFILE_FILE)
        self._bind_shortcuts()

    def _build_menu(self):
        menubar = Menu(self.root, bg=COLOR_BG, fg=COLOR_FG, relief="flat")
        file_menu = Menu(menubar, tearoff=0, bg=COLOR_BG, fg=COLOR_FG)
        file_menu.add_command(label="Exporter les résultats (CSV)", command=self._export_csv)
        file_menu.add_command(label="Charger des profils...", command=self._load_profiles_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        search_menu = Menu(menubar, tearoff=0, bg=COLOR_BG, fg=COLOR_FG)
        search_menu.add_command(label="Lancer la recherche", command=self._start_search)
        search_menu.add_command(label="Effacer les résultats", command=self._clear_results)
        search_menu.add_command(label="Historique", command=self._show_history)
        menubar.add_cascade(label="Recherche", menu=search_menu)

        help_menu = Menu(menubar, tearoff=0, bg=COLOR_BG, fg=COLOR_FG)
        help_menu.add_command(label="À propos", command=self._show_about)
        help_menu.add_command(label="Sources disponibles", command=self._show_sources)
        menubar.add_cascade(label="Aide", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_header(self):
        self.header = Frame(self.root, bg=COLOR_BG)
        self.header.pack(fill="x", padx=40, pady=(30, 10))

        title = Label(self.header, text=APP_NAME, bg=COLOR_BG, fg=COLOR_FG,
                      font=("Segoe UI", 36, "bold"))
        title.pack()

        subtitle = Label(self.header, text="Moteur de recherche universel multi-sources",
                         bg=COLOR_BG, fg=COLOR_FG_SECONDARY, font=("Segoe UI", 12))
        subtitle.pack(pady=(5, 20))

        search_frame = Frame(self.header, bg=COLOR_BG)
        search_frame.pack(fill="x", pady=10)
        search_frame.columnconfigure(0, weight=1)

        self.search_var = StringVar()
        self.search_entry = Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 14),
                                  bg=COLOR_BG, fg=COLOR_FG, relief="solid", bd=1,
                                  insertbackground=COLOR_FG, highlightbackground=COLOR_BORDER,
                                  highlightcolor=COLOR_ACCENT, highlightthickness=1)
        self.search_entry.grid(row=0, column=0, sticky="ew", ipady=10, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._start_search())

        search_btn = Button(search_frame, text="Rechercher", bg=COLOR_ACCENT, fg="white",
                            relief="flat", font=("Segoe UI", 12, "bold"), cursor="hand2",
                            command=self._start_search)
        search_btn.grid(row=0, column=1, ipady=6, ipadx=20)

        self.category_var = StringVar(value="All")
        category_frame = Frame(self.header, bg=COLOR_BG)
        category_frame.pack(fill="x", pady=(10, 0))
        Label(category_frame, text="Catégorie :", bg=COLOR_BG, fg=COLOR_FG_SECONDARY,
              font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        for cat in CATEGORIES:
            rb = ttk.Radiobutton(category_frame, text=cat, variable=self.category_var, value=cat)
            rb.pack(side="left", padx=8)

    def _build_main_layout(self):
        self.main_frame = Frame(self.root, bg=COLOR_BG)
        self.main_frame.pack(fill="both", expand=True, padx=40, pady=10)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        self.progress = ProgressBar(self.main_frame)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        content_frame = Frame(self.main_frame, bg=COLOR_BG)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        results_frame = Frame(content_frame, bg=COLOR_BG, highlightbackground=COLOR_BORDER, highlightthickness=1)
        results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        results_frame.rowconfigure(1, weight=1)

        results_header = Frame(results_frame, bg=COLOR_BG)
        results_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.results_count_label = Label(results_header, text="Aucun résultat", bg=COLOR_BG, fg=COLOR_FG,
                                         font=("Segoe UI", 12, "bold"), anchor="w")
        self.results_count_label.pack(side="left")

        self.table = ResultsTable(results_frame, on_select=self._on_result_select)
        self.table.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        sidebar = Frame(content_frame, bg=COLOR_BG)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.rowconfigure(2, weight=1)

        profile_label = Label(sidebar, text="Profil actif", bg=COLOR_BG, fg=COLOR_FG,
                              font=("Segoe UI", 12, "bold"), anchor="w")
        profile_label.pack(fill="x", pady=(0, 10))

        self.profile_card = ProfileCard(sidebar)
        self.profile_card.pack(fill="x", pady=(0, 20))

        switch_btn = Button(sidebar, text="Changer de profil", bg=COLOR_BG, fg=COLOR_FG,
                            relief="flat", font=("Segoe UI", 10), cursor="hand2",
                            command=self._show_profile_selector)
        switch_btn.pack(fill="x", pady=(0, 20))

        summary_label = Label(sidebar, text="Résumé de la recherche", bg=COLOR_BG, fg=COLOR_FG,
                              font=("Segoe UI", 12, "bold"), anchor="w")
        summary_label.pack(fill="x", pady=(0, 10))

        self.summary_text = Text(sidebar, wrap="word", bg=COLOR_ROW_ODD, fg=COLOR_FG,
                                 font=("Segoe UI", 10), relief="flat", padx=10, pady=10, height=10)
        self.summary_text.pack(fill="both", expand=True)
        self.summary_text.insert("1.0", "Lancez une recherche pour obtenir un résumé.")
        self.summary_text.config(state="disabled")

        self.bottom_notebook = ttk.Notebook(self.main_frame)
        self.bottom_notebook.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        sources_tab = Frame(self.bottom_notebook, bg=COLOR_BG)
        self.bottom_notebook.add(sources_tab, text="Sources actives")

        self.sources_text = Text(sources_tab, wrap="word", bg=COLOR_BG, fg=COLOR_FG_SECONDARY,
                                 font=("Segoe UI", 9), relief="flat", height=6, padx=10, pady=10)
        self.sources_text.pack(fill="both", expand=True)
        self._update_sources_text()

        details_tab = Frame(self.bottom_notebook, bg=COLOR_BG)
        self.bottom_notebook.add(details_tab, text="Dernier résultat sélectionné")

        self.detail_preview = Text(details_tab, wrap="word", bg=COLOR_BG, fg=COLOR_FG,
                                   font=("Segoe UI", 10), relief="flat", height=6, padx=10, pady=10)
        self.detail_preview.pack(fill="both", expand=True)
        self.detail_preview.insert("1.0", "Sélectionnez un résultat pour voir les détails.")
        self.detail_preview.config(state="disabled")

    def _build_footer(self):
        footer = Frame(self.root, bg=COLOR_BG)
        footer.pack(fill="x", padx=40, pady=(10, 20))

        self.status_label = Label(footer, text="Prêt", bg=COLOR_BG, fg=COLOR_FG_SECONDARY,
                                  font=("Segoe UI", 9), anchor="w")
        self.status_label.pack(side="left")

        version_label = Label(footer, text=f"v{APP_VERSION}", bg=COLOR_BG, fg=COLOR_FG_SECONDARY,
                              font=("Segoe UI", 9))
        version_label.pack(side="right")

    def _bind_shortcuts(self):
        self.root.bind("<Control-r>", lambda e: self._start_search())
        self.root.bind("<Control-e>", lambda e: self._export_csv())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-h>", lambda e: self._show_history())
        self.root.bind("<Escape>", lambda e: self._clear_results())

    def _load_profiles(self, path: str):
        self.profiles = load_json_file(path, [])
        if not self.profiles:
            self.profiles = [{
                "id": 0,
                "name": "Invité",
                "role": "Visiteur",
                "avatar": "",
                "email": "",
                "bio": "Aucun profil chargé. Utilisez Fichier > Charger des profils.",
                "tags": [],
                "active": True
            }]
        active = next((p for p in self.profiles if p.get("active")), self.profiles[0])
        self._set_profile(active)

    def _load_profiles_dialog(self):
        path = filedialog.askopenfilename(title="Charger un fichier de profils",
                                          filetypes=[("JSON", "*.json"), ("CSV", "*.csv"), ("Tous", "*.*")])
        if path:
            if path.lower().endswith(".csv"):
                self._load_profiles_csv(path)
            else:
                self._load_profiles(path)
            messagebox.showinfo("Profils", f"{len(self.profiles)} profil(s) chargé(s).")

    def _load_profiles_csv(self, path: str):
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
            messagebox.showerror("Erreur", f"Impossible de lire le CSV :\n{exc}")
            return
        self.profiles = profiles if profiles else self.profiles
        active = next((p for p in self.profiles if p.get("active")), self.profiles[0])
        self._set_profile(active)

    def _set_profile(self, profile: dict):
        self.current_profile = profile
        for p in self.profiles:
            p["active"] = (p.get("id") == profile.get("id"))
        self.profile_card.set_profile(profile)
        if hasattr(self, "profile_window") and self.profile_window.winfo_exists():
            self.profile_window.destroy()

    def _show_profile_selector(self):
        window = Toplevel(self.root)
        window.title("Sélectionner un profil")
        window.geometry("500x500")
        window.configure(bg=COLOR_BG)
        self.profile_window = window

        Label(window, text="Choisissez un profil", bg=COLOR_BG, fg=COLOR_FG,
              font=("Segoe UI", 16, "bold")).pack(pady=20)

        listbox = Listbox(window, bg=COLOR_BG, fg=COLOR_FG, font=("Segoe UI", 12),
                          selectbackground=COLOR_HIGHLIGHT, selectforeground=COLOR_FG,
                          relief="flat", highlightbackground=COLOR_BORDER, highlightthickness=1)
        listbox.pack(fill="both", expand=True, padx=20, pady=10)

        for idx, p in enumerate(self.profiles):
            active_marker = "✓ " if p.get("active") else "   "
            listbox.insert("end", f"{active_marker}{p.get('name', 'Profil')} - {p.get('role', '')}")

        def confirm():
            selection = listbox.curselection()
            if selection:
                self._set_profile(self.profiles[selection[0]])
            window.destroy()

        Button(window, text="Sélectionner", bg=COLOR_ACCENT, fg="white", relief="flat",
               font=("Segoe UI", 11), cursor="hand2", command=confirm).pack(pady=15)

    def _start_search(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Recherche vide", "Veuillez entrer un mot-clé.")
            return
        self.current_query = query
        self.current_results = []
        self.table.clear()
        self.progress.set_progress(0, "Initialisation...")
        self.status_label.config(text=f"Recherche en cours : {query}")

        category = self.category_var.get()
        self.search_history.insert(0, {"query": query, "category": category, "time": get_current_timestamp()})
        self.search_history = self.search_history[:50]
        save_json_file(HISTORY_FILE, self.search_history)

        thread = threading.Thread(target=self._search_worker, args=(query, category), daemon=True)
        thread.start()

    def _search_worker(self, query: str, category: str):
        def progress(current, total, source):
            pct = int((current / max(total, 1)) * 100)
            self.root.after(0, lambda: self.progress.set_progress(pct, f"{source} ({current}/{total})"))

        results = self.engine.search(query, source_name=category, limit=5, progress_callback=progress)
        self.current_results = results
        self.root.after(0, lambda: self._display_results(results))

    def _display_results(self, results: list):
        self.table.clear()
        if not results:
            self.results_count_label.config(text="Aucun résultat trouvé")
            self.progress.set_progress(0, "Aucun résultat")
            self.status_label.config(text="Aucun résultat")
            self._update_summary(results)
            return

        for result in results:
            self.table.add_result(result)

        self.results_count_label.config(text=f"{len(results)} résultat(s) trouvé(s)")
        self.progress.set_progress(100, "Terminé")
        self.status_label.config(text=f"Recherche terminée : {len(results)} résultat(s)")
        self._update_summary(results)

    def _clear_results(self):
        self.current_results = []
        self.table.clear()
        self.results_count_label.config(text="Aucun résultat")
        self.progress.set_progress(0, "Prêt")
        self.status_label.config(text="Résultats effacés")
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "Lancez une recherche pour obtenir un résumé.")
        self.summary_text.config(state="disabled")

    def _update_summary(self, results: list):
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")

        if not results:
            self.summary_text.insert("1.0", "Aucun résultat à résumer.")
            self.summary_text.config(state="disabled")
            return

        categories = {}
        sources = {}
        for r in results:
            cat = r.get("category", "Autre")
            src = r.get("source", "Inconnu")
            categories[cat] = categories.get(cat, 0) + 1
            sources[src] = sources.get(src, 0) + 1

        lines = [f"Recherche : {self.current_query}", f"Total : {len(results)} résultat(s)", ""]
        lines.append("Répartition par catégorie :")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            lines.append(f"  • {cat} : {count}")
        lines.append("")
        lines.append("Top sources :")
        for src, count in sorted(sources.items(), key=lambda x: -x[1])[:8]:
            lines.append(f"  • {src} : {count}")
        lines.append("")
        lines.append("Profil actif :")
        profile = self.current_profile or {}
        lines.append(f"  • {profile.get('name', 'Invité')} ({profile.get('role', '')})")

        self.summary_text.insert("1.0", "\n".join(lines))
        self.summary_text.config(state="disabled")

    def _on_result_select(self, result: dict):
        self.detail_preview.config(state="normal")
        self.detail_preview.delete("1.0", "end")
        lines = [
            f"Titre : {result.get('title', '')}",
            f"Source : {result.get('source', '')} {result.get('icon', '')}",
            f"Catégorie : {result.get('category', '')}",
            f"Métadonnées : {result.get('meta', '')}",
            f"URL : {result.get('url', '')}",
            "",
            result.get("snippet", ""),
        ]
        self.detail_preview.insert("1.0", "\n".join(lines))
        self.detail_preview.config(state="disabled")

    def _export_csv(self):
        if not self.current_results:
            messagebox.showwarning("Export", "Aucun résultat à exporter.")
            return
        filename = f"search_export_{slugify(self.current_query)}_{int(time.time())}.csv"
        path = os.path.join(EXPORT_DIR, filename)
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.DictWriter(fh, fieldnames=["source", "category", "title", "url", "snippet", "meta", "timestamp"])
                writer.writeheader()
                for r in self.current_results:
                    writer.writerow({
                        "source": r.get("source", ""),
                        "category": r.get("category", ""),
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("snippet", ""),
                        "meta": r.get("meta", ""),
                        "timestamp": r.get("timestamp", ""),
                    })
            messagebox.showinfo("Export", f"Résultats exportés dans :\n{path}")
            self.status_label.config(text=f"Export CSV : {path}")
        except Exception as exc:
            messagebox.showerror("Erreur", f"Export impossible :\n{exc}")

    def _show_history(self):
        window = Toplevel(self.root)
        window.title("Historique des recherches")
        window.geometry("600x500")
        window.configure(bg=COLOR_BG)

        Label(window, text="Historique des recherches", bg=COLOR_BG, fg=COLOR_FG,
              font=("Segoe UI", 16, "bold")).pack(pady=20)

        listbox = Listbox(window, bg=COLOR_BG, fg=COLOR_FG, font=("Segoe UI", 11),
                          selectbackground=COLOR_HIGHLIGHT, relief="flat",
                          highlightbackground=COLOR_BORDER, highlightthickness=1)
        listbox.pack(fill="both", expand=True, padx=20, pady=10)

        for item in self.search_history:
            listbox.insert("end", f"{item.get('time', '')} | [{item.get('category', '')}] {item.get('query', '')}")

        def reuse():
            selection = listbox.curselection()
            if selection:
                query = self.search_history[selection[0]].get("query", "")
                self.search_var.set(query)
                window.destroy()
                self._start_search()

        Button(window, text="Réutiliser cette recherche", bg=COLOR_ACCENT, fg="white",
               relief="flat", font=("Segoe UI", 11), cursor="hand2", command=reuse).pack(pady=15)

    def _update_sources_text(self):
        self.sources_text.delete("1.0", "end")
        lines = []
        for name, meta in SOURCES.items():
            mode = "API publique" if meta["api"] else "Lien web"
            lines.append(f"{meta['icon']} {name} ({meta['category']}) - {mode}")
            lines.append(f"    {meta['description']}")
        self.sources_text.insert("1.0", "\n".join(lines))
        self.sources_text.config(state="disabled")

    def _show_sources(self):
        self.bottom_notebook.select(0)

    def _show_about(self):
        messagebox.showinfo("À propos", f"{APP_NAME} v{APP_VERSION}\nAuteur : {APP_AUTHOR}\n\n"
                            "Moteur de recherche universel sur sources ouvertes.")


# ---------------------------------------------------------------------------
# STYLES TTK
# ---------------------------------------------------------------------------
def configure_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
    style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=(12, 8), background=COLOR_BG, foreground=COLOR_FG)
    style.map("TNotebook.Tab", background=[("selected", COLOR_HIGHLIGHT)], foreground=[("selected", COLOR_FG)])
    style.configure("TRadiobutton", background=COLOR_BG, foreground=COLOR_FG, font=("Segoe UI", 10))


# ---------------------------------------------------------------------------
# POINT D'ENTRÉE
# ---------------------------------------------------------------------------
def main():
    configure_styles()
    root = Tk()
    app = SearchEngineApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
