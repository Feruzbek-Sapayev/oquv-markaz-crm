import requests
from django.conf import settings

def send_telegram_message(telegram_id, message):
    """
    Sends a message to a Telegram user using the bot token from settings.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token or not telegram_id:
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram sending error: {e}")
        return False
