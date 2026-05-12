"""
Telegram notification utilities
"""
import os
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

async def send_violation_notification(
    camera_name: str,
    missing_apd: dict,
    confidence_score: float,
    snapshot_url: Optional[str] = None,
    violation_timestamp: Optional[str] = None
) -> bool:
    """
    Kirim notifikasi pelanggaran ke Telegram
    
    Args:
        camera_name: Nama kamera
        missing_apd: Dict dengan APD yang hilang {"helmet": True, "vest": False}
        confidence_score: Score confidence (0-1)
        snapshot_url: URL ke file snapshot (optional)
        violation_timestamp: Timestamp pelanggaran (optional)
    
    Returns:
        True jika berhasil, False jika gagal
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured")
        return False
    
    try:
        # Format pesan
        missing_items = []
        for item, is_missing in missing_apd.items():
            if is_missing:
                missing_items.append(f"❌ {item.upper()}")
        
        missing_text = "\n".join(missing_items) if missing_items else "✅ All items present"
        
        message = f"""
🚨 **PELANGGARAN APD TERDETEKSI**

📹 Kamera: {camera_name}
🕐 Waktu: {violation_timestamp or 'N/A'}
⚠️ APD Hilang:
{missing_text}

📊 Confidence Score: {confidence_score:.1%}

🔗 Lihat detail di dashboard untuk verifikasi.
        """
        
        # Send text message
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Telegram notification sent successfully")
            
            # Send photo jika snapshot_url tersedia
            if snapshot_url:
                try:
                    photo_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                    photo_data = {
                        "chat_id": TELEGRAM_CHAT_ID,
                        "photo": snapshot_url,
                        "caption": "📸 Snapshot Pelanggaran"
                    }
                    requests.post(photo_url, json=photo_data, timeout=10)
                except Exception as e:
                    logger.warning(f"Failed to send photo: {str(e)}")
            
            return True
        else:
            logger.error(f"Telegram API error: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending telegram notification: {str(e)}")
        return False


async def send_verification_notification(
    camera_name: str,
    status: str,
    verified_by: str,
    notes: Optional[str] = None
) -> bool:
    """
    Kirim notifikasi status verifikasi ke Telegram
    
    Args:
        camera_name: Nama kamera
        status: Status verifikasi (Verified / False_Positive)
        verified_by: Username yang verifikasi
        notes: Catatan verifikasi (optional)
    
    Returns:
        True jika berhasil, False jika gagal
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        status_emoji = "✅" if status == "Verified" else "⛔"
        status_text = "TERVERIFIKASI" if status == "Verified" else "BUKAN PELANGGARAN"
        
        message = f"""
{status_emoji} **PELANGGARAN {status_text}**

📹 Kamera: {camera_name}
👤 Diverifikasi oleh: {verified_by}
📝 Catatan: {notes or '-'}
        """
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Error sending verification notification: {str(e)}")
        return False
