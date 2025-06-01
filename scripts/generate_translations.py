# Script to generate and compile translation files for the OnTime application.
# This script uses `pylupdate6` to generate TS files from Python source files
# and `lrelease` to compile them into QM files.
# Ensure you have the necessary tools installed:
# - PyQt6 (for pylupdate6)
# - Qt Linguist (for lrelease)      

import os
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import AVAILABLE_LANGUAGES

from PyQt6.QtCore import QCoreApplication

_ = QCoreApplication.translate

SRC_FILES = [
    "src/views"
    #"src/controllers",
    #"src/models",
    #"src/utils",
   # "src/main.py"
]

TS_DIR = "translations"
QM_DIR = os.path.join(TS_DIR, "qm")

os.makedirs(QM_DIR, exist_ok=True)

def collect_sources():
    sources = []
    for path in SRC_FILES:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                sources += [os.path.join(root, f) for f in files if f.endswith(".py")]
        elif path.endswith(".py"):
            sources.append(path)
    print(f"Collected source files: {sources}")
    return sources

def generate_ts(lang):
    ts_path = os.path.join(TS_DIR, f"ontime_{lang}.ts")
    sources = collect_sources()
    print(f"📄 Files to scan for translations in {lang}:")
    for src in sources:
        print(f"   - {src}")
    py_files = [src for src in sources if src.endswith(".py")]
    subprocess.run(["pylupdate6", *py_files, "-ts", ts_path], check=True)
    return ts_path

def compile_qm(ts_file):
    qm_file = os.path.join(QM_DIR, Path(ts_file).with_suffix(".qm").name)
    subprocess.run(["lrelease", ts_file, "-qm", qm_file], check=True)
    return qm_file

if __name__ == "__main__":
    print("🔁 Generating translations...")
    for lang_code in AVAILABLE_LANGUAGES:
        ts_file = os.path.join(TS_DIR, f"ontime_{lang_code}.ts")
        if not os.path.exists(ts_file):
            print(f"🆕 Creating new TS file for {lang_code}")
        else:
            print(f"🔄 Updating TS file for {lang_code}")
        ts_path = generate_ts(lang_code)
        qm_path = compile_qm(ts_path)
        print(f"✅ Compiled {qm_path}")
    print("Translation files updated successfully.")