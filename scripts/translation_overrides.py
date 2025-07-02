"""
Translation overrides configuration for OnTime Meeting Timer.
This module provides a way to define custom translations for specific terms and phrases
used in the application, allowing for flexibility in localization.
"""

# Translation overrides by language and source text
TRANSLATION_OVERRIDES = {
    'it': {
        # Generic terms
        'meeting': 'adunanza',
        'meetings': 'adunanze', 
        'Meeting': 'Adunanza',
        'Meetings': 'Adunanze',
        'MEETING': 'ADUNANZA',
        'MEETINGS': 'ADUNANZE',
        
        # Specific phrases
        'No Meeting Selected': 'Nessuna Adunanza Selezionata',
        'Current Meeting': 'Adunanza Corrente',
        'Start Meeting': 'Inizia Adunanza',
        'Stop Meeting': 'Termina',
        'Meeting starts in': 'L\'adunanza inizia tra',
        'Meeting starts now!': 'L\'adunanza inizia ora!',
        'Meeting Ended': 'Adunanza Terminata',
        'Meeting Completed': 'Adunanza Completata',
        'Meeting Overtime': 'Adunanza in Ritardo',
        
        # Meeting types
        'Midweek Meeting': 'Adunanza Infrasettimanale',
        'Weekend Meeting': 'Adunanza del Fine Settimana',
        'Public Talk and Watchtower Study': 'Discorso Pubblico e Torre di Guardia',
        
        # Parts and sections
        'Opening Comments': 'Commenti introduttivi',
        'Concluding Comments': 'Commenti conclusivi',
        'Song and Prayer': 'Cantico e preghiera',
        'Public Talk': 'Discorso pubblico',
        'Watchtower Study': 'Torre di Guardia',
        
        # UI Elements
        'Settings': 'Impostazioni',
        'Language': 'Lingua',
        'Theme': 'Tema',
        'Display': 'Visualizzazione',
        'Network Display': 'Display di Rete',
        'Secondary Display': 'Display Secondario',
        
        # Time related
        'minutes': 'minuti',
        'seconds': 'secondi',
        'hours': 'ore',
        'Duration': 'Durata',
        'Time': 'Ora',
        
        # Actions
        'Start': 'Inizia',
        'Stop': 'Termina', 
        'Pause': 'Pausa',
        'Resume': 'Riprendi',
        'Next': 'Successivo',
        'Previous': 'Precedente',
        'Edit': 'Modifica',
        'Save': 'Salva',
        'Cancel': 'Annulla',
        'Delete': 'Elimina',
        'Add': 'Aggiungi',
        'Remove': 'Rimuovi',
        
        # Status
        'Active': 'Attivo',
        'Inactive': 'Inattivo',
        'Running': 'In esecuzione',
        'Stopped': 'Terminato',
        'Paused': 'In pausa',
        'Completed': 'Completato',
        'Pending': 'In attesa',
        'Current': 'Corrente',
        
        # Common UI
        'OK': 'OK',
        'Yes': 'Sì',
        'No': 'No',
        'Close': 'Chiudi',
        'Apply': 'Applica',
        'Help': 'Aiuto',
        'About': 'Informazioni',
        'File': 'File',
        'View': 'Visualizza',
        'Tools': 'Strumenti',
        'Options': 'Opzioni',
    },
    
    'fr': {
        # Generic terms
        'meeting': 'réunion',
        'meetings': 'réunions',
        'Meeting': 'Réunion', 
        'Meetings': 'Réunions',
        'MEETING': 'RÉUNION',
        'MEETINGS': 'RÉUNIONS',
        'No Meeting Selected': 'Aucune Réunion Sélectionnée',
        'Current Meeting': 'Réunion Courante',
        
        # Specific phrases
        'Start Meeting': 'Commencer la Réunion',
        'Stop Meeting': 'Arrêter'
    },
    
    'es': {
        # Add Spanish overrides here
        'meeting': 'reunión',
        'meetings': 'reuniones',
        # Add more Spanish overrides as needed
    },
    
    'de': {
        # Add German overrides here
        'meeting': 'Versammlung',
        'meetings': 'Versammlungen',
        # Add more German overrides as needed
    },
    
    'pt': {
        # Add Portuguese overrides here
        'meeting': 'reunião',
        'meetings': 'reuniões',
        # Add more Portuguese overrides as needed
    }
}

# Case-insensitive patterns for more flexible matching
PATTERN_OVERRIDES = {
    'it': {
        # These will match regardless of case and apply the override
        r'\briunione\b': 'adunanza',
        r'\briunioni\b': 'adunanze',
        r'\bincontra\b': 'adunanza',
        r'\bincontri\b': 'adunanze',
        # Add more patterns as needed
    }
}

def get_translation_override(source_text: str, target_language: str) -> str:
    """
    Get custom translation override if one exists for the given source text and language.
    
    Args:
        source_text: The source text to translate
        target_language: Target language code (e.g., 'it', 'fr', 'es')
    
    Returns:
        Custom translation if override exists, otherwise None
    """
    if target_language not in TRANSLATION_OVERRIDES:
        return None
    
    overrides = TRANSLATION_OVERRIDES[target_language]
    
    # First try exact match
    if source_text in overrides:
        return overrides[source_text]
    
    # Then try case-insensitive match
    for key, value in overrides.items():
        if key.lower() == source_text.lower():
            # Preserve original case pattern
            if source_text.isupper():
                return value.upper()
            elif source_text.istitle():
                return value.title()
            else:
                return value
    
    return None

def apply_pattern_overrides(translated_text: str, target_language: str) -> str:
    """
    Apply pattern-based overrides to already translated text.
    
    Args:
        translated_text: The translated text to process
        target_language: Target language code
    
    Returns:
        Text with pattern overrides applied
    """
    import re
    
    if target_language not in PATTERN_OVERRIDES:
        return translated_text
    
    patterns = PATTERN_OVERRIDES[target_language]
    result = translated_text
    
    for pattern, replacement in patterns.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result