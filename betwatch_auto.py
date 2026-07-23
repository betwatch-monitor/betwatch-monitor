import requests
import re
import json
import time
from datetime import datetime

# ===== НАСТРОЙКИ =====
TELEGRAM_TOKEN = "8913782012:AAHgCpW3pDvMGVci00IYeaO6U4GCUQ0oPog"
CHAT_ID = "768631559"
CHECK_INTERVAL = 30

# ===== API КЛЮЧ ScrapingBee (БЕСПЛАТНО) =====
# Зарегистрируйся на https://www.scrapingbee.com/ и получи ключ
SCRAPINGBEE_API_KEY = "ТВОЙ_КЛЮЧ_SCRAPINGBEE"  # Замени на свой

RULES = [
    {"markets": ["Over/Under 1.5 Goals", "Over/Under 2.5 Goals", "Over/Under 3.5 Goals"], "window_minutes": 5, "threshold": 5000, "period": "full"},
    {"markets": ["First Half Goals 0.5", "First Half Goals 1.5", "First Half Goals 2.5"], "window_minutes": 4, "threshold": 5000, "period": "first_half"}
]

history = {}
tracked = {}

# ===== ФУНКЦИИ =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def fetch_html_via_scrapingbee(url):
    """Получает HTML через ScrapingBee (обходит блокировку)"""
    api_url = f"https://app.scrapingbee.com/api/v1/?api_key={SCRAPINGBEE_API_KEY}&url={url}&render_js=false"
    try:
        response = requests.get(api_url, timeout=30)
        print(f"   → ScrapingBee статус: {response.status_code}")
        if response.status_code == 200:
            return response.text
        else:
            print(f"   → Ошибка ScrapingBee: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка ScrapingBee: {e}")
        return None

def find_friendly_matches():
    # ВРЕМЕННО: добавляем матч вручную для теста
    return ["https://betwatch.fr/football/35850734"]

def get_match_data(url):
    html = fetch_html_via_scrapingbee(url)
    if not html:
        return None
    
    game_match = re.search(r'game = ({.*?});', html, re.DOTALL)
    if not game_match:
        print("   → game JSON не найден")
        return None
    
    game_data = json.loads(game_match.group(1))
    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    match_name = title_match.group(1).strip() if title_match else "Unknown Match"
    is_live = game_data.get('l', False)
    live_info = game_data.get('live_info', {})
    minute = None
    score = None
    if live_info:
        for info in live_info.values():
            if len(info) >= 2:
                minute = info[0]
                score = info[1]
                break
    return {
        "match_name": match_name,
        "is_live": is_live,
        "minute": minute,
        "score": score,
        "game": game_data,
        "url": url
    }

def check_rules(match_data):
    if not match_data:
        return
    minute = match_data.get("minute")
    match_name = match_data["match_name"]
    score = match_data.get("score")
    url = match_data["url"]
    game_data = match_data["game"]
    for uuid, market in game_data.get('i', {}).items():
        market_name = market.get('name', '')
        for rule in RULES:
            if any(m in market_name for m in rule["markets"]):
                if rule["period"] == "first_half" and minute and int(minute) > 45:
                    continue
                for runner in market.get('runners', []):
                    if runner.get('name') == 'Over':
                        volume = runner.get('volume', 0)
                        odd = runner.get('odd', 0)
                        key = f"{uuid}_{market_name}_Over"
                        if key in history:
                            prev = history[key]
                            growth = volume - prev['volume']
                            time_diff = (datetime.now() - prev['time']).total_seconds() / 60
                            if growth >= rule["threshold"] and time_diff <= rule["window_minutes"]:
                                match_info = f"{match_name}"
                                score_info = f"{score or ''} {minute or ''}'" if minute else "До начала матча (прематч)"
                                msg = (
                                    f"🔥 <b>СИГНАЛ!</b>\n"
                                    f"{match_info}\n"
                                    f"{score_info}\n"
                                    f"Рынок: {market_name}\n"
                                    f"Over: +{growth} € (за {time_diff:.1f} мин)\n"
                                    f"Объём: {volume} € | Кэф: {odd}\n"
                                    f"{url}"
                                )
                                send_telegram(msg)
                                history[key]['volume'] = volume
                                history[key]['time'] = datetime.now()
                        else:
                            history[key] = {'volume': volume, 'time': datetime.now()}

def main():
    print("🚀 Скрипт запущен! Ищем товарищеские матчи...")
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Проверка...")
        matches = find_friendly_matches()
        if matches:
            for url in matches:
                if url not in tracked:
                    tracked[url] = datetime.now()
                    print(f"Добавлен матч: {url}")
                data = get_match_data(url)
                if data:
                    check_rules(data)
        else:
            print("Матчи не найдены")
        print(f"Отслеживается {len(tracked)} матчей")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
