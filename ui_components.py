# -*- coding: utf-8 -*-
"""Composants d'interface réutilisables."""

import tkinter as tk
from tkinter import ttk

from config import FBI_BLUE, FBI_GOLD, FBI_RED, FBI_WHITE, HEADER_FONT, TEXT_FONT, TITLE_FONT


def style_tree(tree: ttk.Treeview) -> None:
    """Applique un style sombre FBI à un Treeview."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Custom.Treeview",
        background=FBI_BLUE,
        foreground=FBI_WHITE,
        fieldbackground=FBI_BLUE,
        rowheight=28,
        font=TEXT_FONT,
    )
    style.configure(
        "Custom.Treeview.Heading",
        background="#142744",
        foreground=FBI_GOLD,
        font=HEADER_FONT,
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", FBI_RED)],
        foreground=[("selected", FBI_WHITE)],
    )
    tree.configure(style="Custom.Treeview")


def create_label(parent, text: str, *, font=None, fg=FBI_WHITE, bg=FBI_BLUE, **kwargs) -> tk.Label:
    """Crée un label stylisé."""
    return tk.Label(
        parent,
        text=text,
        font=font or TEXT_FONT,
        fg=fg,
        bg=bg,
        **kwargs,
    )


def create_button(parent, text: str, command, *, font=None, bg=FBI_GOLD, fg=FBI_BLUE) -> tk.Button:
    """Crée un bouton stylisé."""
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=font or HEADER_FONT,
        bg=bg,
        fg=fg,
        activebackground=FBI_WHITE,
        activeforeground=FBI_BLUE,
        relief=tk.FLAT,
        cursor="hand2",
        padx=20,
        pady=8,
    )


def create_entry(parent, *, show: str = "", font=None) -> tk.Entry:
    """Crée un champ de saisie stylisé."""
    return tk.Entry(
        parent,
        show=show,
        font=font or TEXT_FONT,
        bg="#142744",
        fg=FBI_WHITE,
        insertbackground=FBI_GOLD,
        relief=tk.FLAT,
        highlightthickness=2,
        highlightcolor=FBI_GOLD,
        highlightbackground="#142744",
    )
