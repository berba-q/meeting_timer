# src/utils/translator.py

import os
from PyQt6.QtCore import QTranslator

def load_translation(app, lang_code):
    """Load and install the translation file for the given language code."""
    if lang_code == "en":
        print("[Translator] English is the default language, no translation file needed.")
        return True

    translator = QTranslator()
    qm_path = os.path.join("translations", "qm", f"ontime_{lang_code}.qm")

    if os.path.exists(qm_path) and translator.load(qm_path):
        app.installTranslator(translator)
        print(f"[Translator] Loaded translation for '{lang_code}'")
        return True
    else:
        print(f"[Translator] No translation file found for '{lang_code}' at {qm_path}")
        return False