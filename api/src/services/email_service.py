import os
import csv
import re
from datetime import datetime
from flask import current_app

# Common free/personal email providers to reject
FREE_EMAIL_PROVIDERS = {
    'gmail.com', 'googlemail.com',
    'yahoo.com', 'yahoo.fr', 'yahoo.co.uk', 'ymail.com',
    'hotmail.com', 'hotmail.fr', 'hotmail.co.uk',
    'outlook.com', 'outlook.fr', 'live.com', 'live.fr', 'msn.com',
    'aol.com', 'aol.fr',
    'icloud.com', 'me.com', 'mac.com',
    'protonmail.com', 'proton.me',
    'mail.com', 'email.com',
    'gmx.com', 'gmx.fr', 'gmx.net',
    'zoho.com',
    'yandex.com', 'yandex.ru',
    'tutanota.com', 'tutamail.com',
    'fastmail.com',
    'inbox.com',
    'laposte.net', 'orange.fr', 'wanadoo.fr', 'free.fr', 'sfr.fr', 'bbox.fr',
}

# Basic email regex pattern
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def validate_and_store_email(email: str) -> dict:
    """Validate email format and ensure it's a professional email.
    
    Returns:
        dict: {'valid': bool, 'message': str, 'status': str}
    """
    try:
        email = email.strip().lower()
        
        # Check email format
        if not EMAIL_PATTERN.match(email):
            return {
                'valid': False,
                'message': "Format d'email invalide. Veuillez fournir une adresse email valide.",
                'status': 'invalid_format'
            }
        
        # Extract domain
        domain = email.split('@')[1]
        
        # Check if it's a free/personal email provider
        if domain in FREE_EMAIL_PROVIDERS:
            return {
                'valid': False,
                'message': 'Veuillez utiliser une adresse email professionnelle.',
                'status': 'free_email'
            }
        
        # Store email
        _store_email(email, 'valid', [])
        
        return {'valid': True, 'message': 'Email validé avec succès', 'status': 'valid'}

    except Exception as e:
        if current_app:
            current_app.logger.error(f"Email validation error: {str(e)}")
        return {'valid': False, 'message': "Erreur lors de la validation de l'email", 'status': 'error'}

def _store_email(email, status, flags):
    try:
        # Try to locate data directory relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        output_file = os.path.join(base_dir, 'data', 'emails.csv')
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        file_exists = os.path.isfile(output_file)

        with open(output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['email', 'timestamp', 'status', 'flags'])
            
            writer.writerow([email, datetime.now().isoformat(), status, ','.join(flags)])
            
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Failed to save email: {str(e)}")
