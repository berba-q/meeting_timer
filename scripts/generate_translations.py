# Enhanced script to generate, auto-translate, and compile translation files
import os
import subprocess
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import AVAILABLE_LANGUAGES

# Translation service configuration
TRANSLATION_SERVICE = "googletrans"  # Options: "googletrans", "libretranslate", "manual"
AUTO_TRANSLATE = True  # Set to False to skip auto-translation

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

def auto_translate_ts_file(ts_file_path, target_language):
    """Auto-translate a Qt TS file"""
    if not AUTO_TRANSLATE:
        print(f"Auto-translation disabled")
        return True
    
    print(f"Auto-translating to {target_language}")
    
    # Language mapping
    lang_mapping = {
        'fr': 'fr',
        'it': 'it', 
        'de': 'de',
        'es': 'es',
        'pt': 'pt'
    }
    
    if target_language not in lang_mapping:
        print(f"Unsupported language: {target_language}")
        return False
    
    # Install translation service if needed
    if not install_translation_service():
        print(f"Could not install translation service")
        return False
    
    # Load and parse the TS file
    try:
        tree = ET.parse(ts_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing TS file: {e}")
        return False
    
    # Find all unfinished messages
    translated_count = 0
    skipped_count = 0
    
    for context in root.findall('context'):
        context_name = context.find('name').text
        
        for message in context.findall('message'):
            source = message.find('source')
            translation = message.find('translation')
            
            if source is None or translation is None:
                continue
                
            source_text = source.text
            
            # Skip if already translated
            if translation.get('type') != 'unfinished' and translation.text:
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
            if '/' in source_text or source_text.startswith('&') and len(source_text) < 10:
                translation.text = source_text
                if translation.get('type') == 'unfinished':
                    translation.set('type', 'finished')
                skipped_count += 1
                continue
            
            try:
                # Choose translation method
                if TRANSLATION_SERVICE == "googletrans":
                    translated_text = translate_with_googletrans(source_text, target_language)
                elif TRANSLATION_SERVICE == "libretranslate":
                    translated_text = translate_with_libretranslate(source_text, target_language)
                else:
                    translated_text = None
                
                if translated_text:
                    translation.text = translated_text
                    if translation.get('type') == 'unfinished':
                        translation.set('type', 'finished')
                    translated_count += 1
                else:
                    skipped_count += 1
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Translation failed for '{source_text}': {e}")
                skipped_count += 1
                continue
    
    # Save the updated file
    try:
        tree.write(ts_file_path, encoding='utf-8', xml_declaration=True)
        print(f"Translated: {translated_count}, Skipped: {skipped_count}")
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

if __name__ == "__main__":
    print("Enhanced OnTime Translation Generator")
    print("=" * 50)
    
    if AUTO_TRANSLATE:
        print(f"Auto-translation: ENABLED ({TRANSLATION_SERVICE})")
    else:
        print(f"Auto-translation: DISABLED (manual only)")
    
    # Collect and analyze source files
    sources = collect_sources()
    print(f"Found {len(sources)} source files")
    
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
    
    print(f"🔍 Found ~{total_count} translation strings")
    
    if total_count == 0:
        print("No translation strings found! Make sure you're using self.tr() or QCoreApplication.translate()")
    
    # Process each language
    success_count = 0
    for lang_code in AVAILABLE_LANGUAGES:
        if lang_code == 'en':  # Skip English
            continue
            
        print(f"Processing {lang_code.upper()}:")
        
        # Generate TS file
        ts_path = generate_ts(lang_code)
        if not ts_path:
            print(f"Failed to generate TS file")
            continue
        
        # Auto-translate if enabled
        if AUTO_TRANSLATE:
            if not auto_translate_ts_file(ts_path, lang_code):
                print(f"Auto-translation failed")
                # Continue anyway - we can still compile what we have
        
        # Compile QM file
        qm_path = compile_qm(ts_path)
        if qm_path:
            success_count += 1
        else:
            print(f"Failed to compile QM file")
    
    print(f"Translation processing complete!")
    print(f"Successfully processed {success_count}/{len(AVAILABLE_LANGUAGES)-1} languages")
    
    if AUTO_TRANSLATE and success_count > 0:
        print(f" Next steps:")
        print(f"   1. Review translations with: linguist translations/ontime_*.ts")
        print(f"   2. Test translations in your application")
        print(f"   3. Re-run this script to update after code changes")
    elif success_count > 0:
        print(f" Next steps:")
        print(f"   1. Add translations to TS files manually or with Qt Linguist")
        print(f"   2. Re-run this script to compile updated translations")