# Script to generate, auto-translate, and compile translation files
# WITH SUPPORT FOR CUSTOM TRANSLATION OVERRIDES
import os
import subprocess
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import time
import re

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import AVAILABLE_LANGUAGES

# Import our custom translation overrides
try:
    from translation_overrides import get_translation_override, apply_pattern_overrides, TRANSLATION_OVERRIDES
    OVERRIDES_AVAILABLE = True
    print("✅ Custom translation overrides loaded")
except ImportError:
    OVERRIDES_AVAILABLE = False
    print("⚠️  No custom translation overrides found")

# Translation service configuration
TRANSLATION_SERVICE = "googletrans"  # Options: "googletrans", "libretranslate", "manual"
AUTO_TRANSLATE = True  # Set to False to skip auto-translation
APPLY_OVERRIDES = True  # Set to False to disable custom overrides

# Source file patterns
SRC_FILES = [
    "main.py",
    "src/views/*.py",
    "src/controllers/*.py",
    "src/models/*.py",
    "src/utils/*.py"
]

TS_DIR = "translations"
QM_DIR = os.path.join(TS_DIR, "qm")

os.makedirs(TS_DIR, exist_ok=True)
os.makedirs(QM_DIR, exist_ok=True)

def collect_sources():
    sources = []
    for pattern in SRC_FILES:
        if "*" in pattern:
            import glob
            sources.extend(glob.glob(pattern))
        elif os.path.exists(pattern):
            if os.path.isdir(pattern):
                for root, _, files in os.walk(pattern):
                    sources.extend([os.path.join(root, f) for f in files if f.endswith(".py")])
            elif pattern.endswith(".py"):
                sources.append(pattern)
    
    sources = list(set([src for src in sources if os.path.exists(src)]))
    return sources

def generate_ts(lang):
    ts_path = os.path.join(TS_DIR, f"ontime_{lang}.ts")
    sources = collect_sources()
    
    if not sources:
        print(f"No source files found for {lang}")
        return None
    
    try:
        cmd = ["pylupdate6", "--ts", ts_path] + sources
        print(f"   Running: pylupdate6 --ts {ts_path} {len(sources)} files")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if os.path.exists(ts_path):
            file_size = os.path.getsize(ts_path)
            print(f"Created {ts_path} ({file_size} bytes)")
            return ts_path
        else:
            print(f"File was not created: {ts_path}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error running pylupdate6: {e}")
        return None
    except FileNotFoundError:
        print(f"pylupdate6 not found. Install with: pip install PyQt6-tools")
        return None

def install_translation_service():
    """Install the required translation service"""
    if TRANSLATION_SERVICE == "googletrans":
        try:
            import googletrans
            print(f"googletrans already available")
            return True
        except ImportError:
            print(f"Installing googletrans...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "googletrans==4.0.0rc1"], 
                             check=True, capture_output=True)
                print(f"googletrans installed successfully")
                return True
            except Exception as e:
                print(f"Failed to install googletrans: {e}")
                return False
    
    elif TRANSLATION_SERVICE == "libretranslate":
        try:
            import requests
            print(f"requests available for LibreTranslate")
            return True
        except ImportError:
            print(f"Installing requests for LibreTranslate...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "requests"], 
                             check=True, capture_output=True)
                return True
            except Exception as e:
                print(f"Failed to install requests: {e}")
                return False
    
    return False

def translate_with_googletrans(text, target_lang):
    """Translate text using Google Translate (free)"""
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception as e:
        print(f"Google Translate error: {e}")
        return None

def translate_with_libretranslate(text, target_lang):
    """Translate text using LibreTranslate (free, open source)"""
    try:
        import requests
        
        # Using the public LibreTranslate instance (free)
        url = "https://libretranslate.de/translate"
        
        data = {
            "q": text,
            "source": "en",
            "target": target_lang,
            "format": "text"
        }
        
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json()["translatedText"]
        else:
            print(f"LibreTranslate error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"LibreTranslate error: {e}")
        return None

def get_best_translation(source_text, target_language):
    """Get the best translation using override system first, then auto-translation"""
    
    # Step 1: Check for custom override
    if OVERRIDES_AVAILABLE and APPLY_OVERRIDES:
        override = get_translation_override(source_text, target_language)
        if override:
            print(f"   Override: '{source_text}' → '{override}'")
            return override, "override"
    
    # Step 2: Use auto-translation if no override
    if AUTO_TRANSLATE:
        if TRANSLATION_SERVICE == "googletrans":
            translated = translate_with_googletrans(source_text, target_language)
        elif TRANSLATION_SERVICE == "libretranslate":
            translated = translate_with_libretranslate(source_text, target_language)
        else:
            translated = None
        
        if translated:
            # Apply pattern-based overrides to auto-translated text
            if OVERRIDES_AVAILABLE and APPLY_OVERRIDES:
                final_translation = apply_pattern_overrides(translated, target_language)
                if final_translation != translated:
                    print(f"   Pattern override applied: '{translated}' → '{final_translation}'")
                    return final_translation, "pattern_override"
            
            return translated, "auto"
    
    return None, "failed"

def auto_translate_ts_file(ts_file_path, target_language):
    """Auto-translate a Qt TS file with custom overrides"""
    if not AUTO_TRANSLATE and not (OVERRIDES_AVAILABLE and APPLY_OVERRIDES):
        print(f"Auto-translation and overrides both disabled")
        return True
    
    print(f"Processing translations for {target_language}")
    if OVERRIDES_AVAILABLE and APPLY_OVERRIDES:
        override_count = len(TRANSLATION_OVERRIDES.get(target_language, {}))
        print(f"   {override_count} custom overrides available")
    
    # Language mapping for auto-translation services
    lang_mapping = {
        'fr': 'fr',
        'it': 'it', 
        'de': 'de',
        'es': 'es',
        'pt': 'pt'
    }
    
    if target_language not in lang_mapping and AUTO_TRANSLATE:
        print(f"Unsupported language for auto-translation: {target_language}")
        if not (OVERRIDES_AVAILABLE and APPLY_OVERRIDES):
            return False
    
    # Install translation service if needed and auto-translate is enabled
    if AUTO_TRANSLATE and not install_translation_service():
        print(f"Could not install translation service")
        if not (OVERRIDES_AVAILABLE and APPLY_OVERRIDES):
            return False
    
    # Load and parse the TS file
    try:
        tree = ET.parse(ts_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing TS file: {e}")
        return False
    
    # Process translations
    override_count = 0
    auto_translated_count = 0
    pattern_override_count = 0
    skipped_count = 0
    failed_count = 0
    
    for context in root.findall('context'):
        context_name = context.find('name').text if context.find('name') is not None else "Unknown"
        
        for message in context.findall('message'):
            source = message.find('source')
            translation = message.find('translation')
            
            if source is None or translation is None:
                continue
                
            source_text = source.text if source.text else ""
            
            # Skip if already translated (unless we have an override)
            if translation.get('type') != 'unfinished' and translation.text:
                # Check if we have an override for this already-translated text
                if OVERRIDES_AVAILABLE and APPLY_OVERRIDES:
                    override = get_translation_override(source_text, target_language)
                    if override and override != translation.text:
                        print(f"    Updating existing: '{source_text}' → '{override}'")
                        translation.text = override
                        if translation.get('type') == 'unfinished':
                            translation.set('type', 'finished')
                        override_count += 1
                        continue
                
                skipped_count += 1
                continue
            
            # Skip empty or very short strings
            if not source_text or len(source_text.strip()) < 2:
                skipped_count += 1
                continue
                
            # Skip strings that are mostly symbols, keep them as-is
            if source_text.strip() in ['&', '...', ':', '-', '+', '😅', '⌛', 'OnTime', 'OK', 'Cancel']:
                translation.text = source_text
                if translation.get('type') == 'unfinished':
                    translation.set('type', 'finished')
                skipped_count += 1
                continue
            
            # Skip file paths and technical strings
            if '/' in source_text or (source_text.startswith('&') and len(source_text) < 10):
                translation.text = source_text
                if translation.get('type') == 'unfinished':
                    translation.set('type', 'finished')
                skipped_count += 1
                continue
            
            # Get the best translation (override or auto-translate)
            try:
                translated_text, method = get_best_translation(source_text, target_language)
                
                if translated_text:
                    translation.text = translated_text
                    if translation.get('type') == 'unfinished':
                        translation.set('type', 'finished')
                    
                    if method == "override":
                        override_count += 1
                    elif method == "pattern_override":
                        pattern_override_count += 1
                    elif method == "auto":
                        auto_translated_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting for auto-translation
                if method == "auto":
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Translation failed for '{source_text}': {e}")
                failed_count += 1
                continue
    
    # Save the updated file
    try:
        tree.write(ts_file_path, encoding='utf-8', xml_declaration=True)
        print(f"   Overrides: {override_count}")
        print(f"   Pattern overrides: {pattern_override_count}")  
        print(f"   Auto-translated: {auto_translated_count}")
        print(f"    Skipped: {skipped_count}")
        if failed_count > 0:
            print(f"   Failed: {failed_count}")
        return True
        
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

def compile_qm(ts_file):
    if not ts_file or not os.path.exists(ts_file):
        print(f"TS file does not exist: {ts_file}")
        return None
        
    qm_file = os.path.join(QM_DIR, Path(ts_file).with_suffix(".qm").name)
    try:
        result = subprocess.run(["lrelease", ts_file, "-qm", qm_file], 
                              capture_output=True, text=True, check=True)
        
        if os.path.exists(qm_file):
            file_size = os.path.getsize(qm_file)
            print(f"Compiled {qm_file} ({file_size} bytes)")
            return qm_file
        else:
            print(f"QM file was not created: {qm_file}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error running lrelease: {e}")
        return None
    except FileNotFoundError:
        print(f"lrelease not found. Make sure Qt tools are installed.")
        return None

def show_override_summary():
    """Show summary of available overrides"""
    if not OVERRIDES_AVAILABLE:
        return
    
    print("\n Custom Translation Overrides Available:")
    for lang, overrides in TRANSLATION_OVERRIDES.items():
        if overrides:
            print(f"   {lang.upper()}: {len(overrides)} overrides")
            # Show a few examples
            examples = list(overrides.items())[:3]
            for src, tgt in examples:
                print(f"      '{src}' → '{tgt}'")
            if len(overrides) > 3:
                print(f"      ... and {len(overrides) - 3} more")

if __name__ == "__main__":
    print("OnTime Translation Generator with Custom Overrides")
    print("=" * 65)
    
    if OVERRIDES_AVAILABLE and APPLY_OVERRIDES:
        print(f"Custom overrides: ENABLED")
        show_override_summary()
    else:
        print(f" Custom overrides: DISABLED")
    
    if AUTO_TRANSLATE:
        print(f" Auto-translation: ENABLED ({TRANSLATION_SERVICE})")
    else:
        print(f" Auto-translation: DISABLED")
    
    # Collect and analyze source files
    sources = collect_sources()
    print(f"\n Found {len(sources)} source files")
    
    # Check for translation strings
    translation_patterns = ['.tr(', 'QCoreApplication.translate(']
    total_count = 0
    
    for src in sources[:3]:  # Check first 3 files
        try:
            with open(src, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in translation_patterns:
                    total_count += content.count(pattern)
        except Exception:
            pass
    
    print(f" Found ~{total_count} translation strings")
    
    if total_count == 0:
        print(" No translation strings found! Make sure you're using self.tr() or QCoreApplication.translate()")
    
    # Process each language
    success_count = 0
    for lang_code in AVAILABLE_LANGUAGES:
        if lang_code == 'en':  # Skip English
            continue
            
        print(f"\n Processing {lang_code.upper()}:")
        
        # Generate TS file
        ts_path = generate_ts(lang_code)
        if not ts_path:
            print(f"Failed to generate TS file")
            continue
        
        # Apply translations (overrides + auto-translate)
        if not auto_translate_ts_file(ts_path, lang_code):
            print(f" Translation processing failed")
            # Continue anyway - we can still compile what we have
        
        # Compile QM file
        qm_path = compile_qm(ts_path)
        if qm_path:
            success_count += 1
            print(f"Success!")
        else:
            print(f" Failed to compile QM file")
    
    print(f"\n Translation processing complete!")
    print(f" Successfully processed {success_count}/{len(AVAILABLE_LANGUAGES)-1} languages")
    
    if success_count > 0:
        print(f"\n Next steps:")
        if OVERRIDES_AVAILABLE:
            print(f"   1. Review translations with: linguist translations/ontime_*.ts")
            print(f"   2. Add more overrides to translation_overrides.py as needed")
            print(f"   3. Test translations in your application")
            print(f"   4. Re-run this script to update after code changes")
        else:
            print(f"   1. Create translation_overrides.py for custom translations")
            print(f"   2. Review translations with: linguist translations/ontime_*.ts") 
            print(f"   3. Test translations in your application")