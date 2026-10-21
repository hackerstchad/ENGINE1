# -*- coding: utf-8 -*-
"""Application principale FBI Image Intelligence Interface."""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from PIL import Image, ImageTk

from auth import verify_credentials
from background import BackgroundManager
from config import (
    APP_HEIGHT,
    APP_TITLE,
    APP_WIDTH,
    FBI_BLUE,
    FBI_GOLD,
    FBI_RED,
    FBI_WHITE,
    HEADER_FONT,
    TEXT_FONT,
    TITLE_FONT,
)
from image_search import ImageSearchEngine
from ui_components import create_button, create_entry, create_label, style_tree
from utils import now_str


class FBIApp:
    """Classe principale de l'application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.configure(bg=FBI_BLUE)
        self.root.state("zoomed")
        self.root.minsize(1000, 700)

        self.bg_manager = BackgroundManager(self.root)
        self.bg_photo: Optional[ImageTk.PhotoImage] = None
        self.current_image_path: Optional[str] = None
        self.thumbnail_photo: Optional[ImageTk.PhotoImage] = None
        self.search_engine = ImageSearchEngine()
        self._progress_queue: queue.Queue = queue.Queue()
        self._pending_progress = 0

        self._build_login_screen()
        self._poll_progress_queue()

    def run(self) -> None:
        """Lance la boucle principale Tkinter."""
        self.root.mainloop()

    # ------------------------------------------------------------------
    # Écran de connexion
    # ------------------------------------------------------------------
    def _build_login_screen(self) -> None:
        """Construit l'écran de connexion."""
        self._clear_window()
        self._set_background()

        frame = tk.Frame(self.root, bg=FBI_BLUE, bd=2, relief=tk.RIDGE)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Titre FBI
        title = create_label(
            frame,
            "🔒 FBI SECURE ACCESS",
            font=TITLE_FONT,
            fg=FBI_GOLD,
            pady=20,
        )
        title.pack()

        # Sous-titre
        create_label(
            frame,
            "Authentification requise - Niveau 5",
            font=HEADER_FONT,
            fg=FBI_WHITE,
            pady=5,
        ).pack()

        # Formulaire
        form = tk.Frame(frame, bg=FBI_BLUE, padx=40, pady=20)
        form.pack()

        create_label(form, "UTILISATEUR :", font=HEADER_FONT).grid(row=0, column=0, sticky="w", pady=8)
        self.username_entry = create_entry(form)
        self.username_entry.grid(row=0, column=1, pady=8, padx=10, ipadx=5, ipady=3)

        create_label(form, "MOT DE PASSE :", font=HEADER_FONT).grid(row=1, column=0, sticky="w", pady=8)
        self.password_entry = create_entry(form, show="•")
        self.password_entry.grid(row=1, column=1, pady=8, padx=10, ipadx=5, ipady=3)

        # Bouton connexion
        btn_frame = tk.Frame(frame, bg=FBI_BLUE, pady=15)
        btn_frame.pack()
        create_button(
            btn_frame,
            "🔑 ACCÉDER AU SYSTÈME",
            self._handle_login,
            bg=FBI_RED,
            fg=FBI_WHITE,
        ).pack()

        # Bind touches
        self.root.bind("<Return>", lambda _: self._handle_login())

    def _handle_login(self) -> None:
        """Vérifie les identifiants et passe à l'interface principale."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if verify_credentials(username, password):
            self._build_main_interface()
        else:
            messagebox.showerror("ACCES REFUSE", "Identifiants invalides. Alert logged.")

    # ------------------------------------------------------------------
    # Interface principale
    # ------------------------------------------------------------------
    def _build_main_interface(self) -> None:
        """Construit l'interface d'analyse d'image."""
        self._clear_window()
        self._set_background()

        # Header
        header = tk.Frame(self.root, bg=FBI_BLUE, height=80)
        header.pack(fill=tk.X, padx=20, pady=10)
        header.pack_propagate(False)

        create_label(
            header,
            "🛡️ FBI IMAGE INTELLIGENCE",
            font=TITLE_FONT,
            fg=FBI_GOLD,
            bg=FBI_BLUE,
        ).pack(side=tk.LEFT, padx=10)

        create_button(
            header,
            "🔒 Déconnexion",
            self._build_login_screen,
            font=HEADER_FONT,
        ).pack(side=tk.RIGHT, padx=10)

        # Corps
        body = tk.Frame(self.root, bg=FBI_BLUE)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Panneau gauche : image + contrôles
        left_panel = tk.Frame(body, bg=FBI_BLUE, width=380)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        left_panel.pack_propagate(False)

        # Aperçu image
        preview_frame = tk.LabelFrame(
            left_panel,
            text=" APERÇU DE L'IMAGE ",
            fg=FBI_GOLD,
            bg=FBI_BLUE,
            font=HEADER_FONT,
            bd=2,
            relief=tk.GROOVE,
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.preview_label = create_label(
            preview_frame,
            "Aucune image chargée",
            font=HEADER_FONT,
            fg="#888888",
        )
        self.preview_label.pack(expand=True)

        # Boutons
        controls = tk.Frame(left_panel, bg=FBI_BLUE, pady=10)
        controls.pack(fill=tk.X)

        create_button(
            controls,
            "📁 Charger une image",
            self._load_image,
        ).pack(fill=tk.X, pady=5)

        create_button(
            controls,
            "🔍 Lancer l'analyse FBI",
            self._start_analysis,
            bg=FBI_RED,
            fg=FBI_WHITE,
        ).pack(fill=tk.X, pady=5)

        # Barre de progression
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            left_panel,
            variable=self.progress_var,
            maximum=1000,
            mode="determinate",
            length=340,
        )
        self.progress.pack(fill=tk.X, pady=10)

        self.progress_label = create_label(
            left_panel,
            "Statut : EN ATTENTE",
            font=HEADER_FONT,
            fg=FBI_GOLD,
        )
        self.progress_label.pack()

        # Panneau droit : résultats
        right_panel = tk.LabelFrame(
            body,
            text=" RÉSULTATS DE L'ANALYSE ",
            fg=FBI_GOLD,
            bg=FBI_BLUE,
            font=HEADER_FONT,
            bd=2,
            relief=tk.GROOVE,
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # Informations générales
        self.info_text = tk.Text(
            right_panel,
            height=6,
            bg="#142744",
            fg=FBI_WHITE,
            font=TEXT_FONT,
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.info_text.pack(fill=tk.X, padx=10, pady=10)

        # Treeview des résultats
        columns = ("source", "title", "url", "dates")
        self.tree = ttk.Treeview(
            right_panel,
            columns=columns,
            show="headings",
            height=16,
        )
        style_tree(self.tree)

        self.tree.heading("source", text="Source")
        self.tree.heading("title", text="Titre / Description")
        self.tree.heading("url", text="URL")
        self.tree.heading("dates", text="Dates détectées")

        self.tree.column("source", width=130, anchor="w")
        self.tree.column("title", width=300, anchor="w")
        self.tree.column("url", width=350, anchor="w")
        self.tree.column("dates", width=150, anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Log de statut
        self._log_info(f"Session démarrée à {now_str()}. Chargez une image pour commencer.")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _load_image(self) -> None:
        """Ouvre un dialogue pour choisir une image."""
        path = filedialog.askopenfilename(
            title="Sélectionner une image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("Tous fichiers", "*.*"),
            ],
        )
        if not path:
            return

        self.current_image_path = path
        self._display_thumbnail(path)
        self._log_info(f"Image chargée : {os.path.basename(path)}\nChemin : {path}")
        self.progress_var.set(0)
        self.progress_label.config(text="Statut : IMAGE CHARGÉE", fg=FBI_GOLD)

    def _display_thumbnail(self, path: str) -> None:
        """Affiche une miniature de l'image dans le panneau de gauche."""
        try:
            img = Image.open(path)
            img.thumbnail((350, 350), Image.LANCZOS)
            self.thumbnail_photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.thumbnail_photo, text="", fg=FBI_WHITE)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible d'afficher l'image : {exc}")

    def _start_analysis(self) -> None:
        """Lance la recherche inversée dans un thread séparé."""
        if not self.current_image_path:
            messagebox.showwarning("Attention", "Veuillez d'abord charger une image.")
            return

        self.progress_var.set(0)
        self.progress_label.config(text="Statut : ANALYSE EN COURS...", fg=FBI_RED)
        self.tree.delete(*self.tree.get_children())
        self._log_info("Analyse lancée. Initialisation du moteur de recherche...")

        thread = threading.Thread(
            target=self._analysis_worker,
            args=(self.current_image_path,),
            daemon=True,
        )
        thread.start()

    def _poll_progress_queue(self) -> None:
        """Boucle de traitement des mises à jour de progression."""
        try:
            while True:
                self._progress_queue.get_nowait()
                self._pending_progress += 1
        except queue.Empty:
            pass

        if self._pending_progress > 0:
            current = self.progress_var.get()
            increment = min(self._pending_progress, 1000 - current)
            self.progress_var.set(current + increment)
            self._pending_progress = 0

        self.root.after(20, self._poll_progress_queue)

    def _analysis_worker(self, image_path: str) -> None:
        """Travailleur de recherche exécuté en arrière-plan."""
        try:

            def step():
                """Pousse un événement de progression dans la file."""
                self._progress_queue.put(1)

            results = self.search_engine.search(image_path, progress_callback=step)
            self.root.after(0, self._display_results, results)
        except Exception as exc:
            self.root.after(0, self._log_info, f"ERREUR FATALE : {exc}")
            self.root.after(0, self.progress_label.config, {"text": "Statut : ERREUR", "fg": FBI_RED})

    def _display_results(self, results) -> None:
        """Affiche les résultats dans le tableau."""
        self.tree.delete(*self.tree.get_children())

        if not results:
            self._log_info("Aucun résultat trouvé. Vérifiez votre connexion ou essayez une autre image.")
            self.progress_label.config(text="Statut : AUCUN RÉSULTAT", fg=FBI_GOLD)
            self.progress_var.set(1000)
            return

        for r in results:
            self.tree.insert(
                "",
                tk.END,
                values=(r.source, r.title, r.url, ", ".join(r.dates) or "N/A"),
            )

        summary = (
            f"Analyse terminée à {now_str()}\n"
            f"• Image analysée : {os.path.basename(self.current_image_path)}\n"
            f"• Résultats trouvés : {len(results)}\n"
            f"• Sources : {', '.join(sorted(set(r.source for r in results)))}"
        )
        self._log_info(summary)
        self.progress_var.set(1000)
        self.progress_label.config(text="Statut : ANALYSE TERMINÉE", fg=FBI_GOLD)

    # ------------------------------------------------------------------
    # Utilitaires UI
    # ------------------------------------------------------------------
    def _set_background(self) -> None:
        """Définit le fond d'écran flou."""
        self.bg_photo = self.bg_manager.get_background()
        if self.bg_photo:
            bg_label = tk.Label(self.root, image=self.bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()

    def _clear_window(self) -> None:
        """Supprime tous les widgets de la fenêtre."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def _log_info(self, message: str) -> None:
        """Écrit un message dans la zone d'informations."""
        if not hasattr(self, "info_text"):
            return
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, message)
        self.info_text.config(state=tk.DISABLED)
