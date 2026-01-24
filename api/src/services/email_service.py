import os
import csv
import requests
from datetime import datetime
from flask import current_app

NEVERBOUNCE_API_KEY = "private_d44ab3dcaebf54b11ff87f94ae22709b"
NEVERBOUNCE_TIMEOUT = 30  # Increased timeout for slower email hosts

def validate_and_store_email(email: str) -> dict:
    """Validate email with NeverBounce and store if valid.
    
    Returns:
        dict: {'valid': bool, 'message': str, 'status': str}
    """
    try:
        response = requests.get(
            'https://api.neverbounce.com/v4/single/check',
            params={'key': NEVERBOUNCE_API_KEY, 'email': email},
            timeout=NEVERBOUNCE_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        status = result.get('result')
        flags = result.get('flags', [])
        
        # Log for debugging
        if current_app:
            current_app.logger.info(f"NeverBounce result for {email}: status={status}, flags={flags}")
        
        # Valid statuses: 'valid', 'catchall' (often corporate), 'unknown' (allow through per docs)
        if status not in ['valid', 'catchall', 'unknown']:
            return {
                'valid': False,
                'message': f"Le statut de l'email est {status}. Veuillez fournir une adresse email valide.",
                'status': status
            }

        if 'free_email_host' in flags:
            return {
                'valid': False,
                'message': 'Veuillez utiliser une adresse email professionnelle.',
                'status': status
            }
            
        # Store email
        _store_email(email, status, flags)
        
        return {'valid': True, 'message': 'Email validé avec succès', 'status': status}

    except requests.exceptions.Timeout:
        # Per NeverBounce docs: treat timeouts as "unknown" and allow through
        if current_app:
            current_app.logger.warning(f"NeverBounce timeout for {email}, treating as unknown")
        _store_email(email, 'timeout', [])
        return {'valid': True, 'message': 'Email validé avec succès', 'status': 'timeout'}
    
    except requests.exceptions.RequestException as e:
        if current_app:
            current_app.logger.error(f"NeverBounce request error: {str(e)}")
        return {'valid': False, 'message': "Service de validation d'email indisponible", 'status': 'error'}
    
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Email validation error: {str(e)}")
        return {'valid': False, 'message': "Service de validation d'email indisponible", 'status': 'error'}

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
