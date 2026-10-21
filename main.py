#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FBI Image Intelligence Interface
Application Tkinter avancée : authentification, fond FBI flou,
analyse d'image et recherche inversée sans clé API.
"""

import sys
from pathlib import Path

# Ajout du dossier src au path
SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app import FBIApp


def main():
    app = FBIApp()
    app.run()


if __name__ == "__main__":
    main()
