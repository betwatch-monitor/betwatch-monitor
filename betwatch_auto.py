import requests
import json
import time
from datetime import datetime

# ===== НАСТРОЙКИ =====
TELEGRAM_TOKEN = "8913782012:AAHgCpW3pDvMGVci00IYeaO6U4GCUQ0oPog"
CHAT_ID = "768631559"
CHECK_INTERVAL = 30

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

def fetch_match_data(match_id):
    """Получает данные матча через API Betwatch"""
    url = f"https://betwatch.fr/api/football/match/{match_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   → API статус: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"   → Ошибка API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка API: {e}")
        return None

def find_friendly_matches():
    # ВРЕМЕННО: добавляем ID матча вручную для теста
    return ["35850734"]  # Venezia — Pesaro

def get_match_data(match_id):
    data = fetch_match_data(match_id)
    if not data:
        return None
    
    # Парсим ответ API
    match_name = f"{data.get('home_team', '')} — {data.get('away_team', '')}"
    is_live = data.get('live', False)
    minute = data.get('minute', None)
    score = f"{data.get('home_score', 0)}:{data.get('away_score', 0)}"
    
    # Преобразуем рынки в формат, совместимый со скриптом
    game_data = {'i': {}}
    for market in data.get('markets', []):
        market_id = f"market_{market.get('id', '')}"
        game_data['i'][market_id] = {
            'name': market.get('name', ''),
            'total_volume': market.get('total_volume', 0),
            'runners': [
                {'name': runner.get('name', ''), 'volume': runner.get('volume', 0), 'odd': runner.get('odd', '0')}
                for runner in market.get('runners', [])
            ]
        }
    
    return {
        "match_name": match_name,
        "is_live": is_live,
        "minute": minute,
        "score": score,
        "game": game_data,
        "url": f"https://betwatch.fr/football/{match_id}"
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
            for match_id in matches:
                if match_id not in tracked:
                    tracked[match_id] = datetime.now()
                    print(f"Добавлен матч: {match_id}")
                data = get_match_data(match_id)
                if data:
                    check_rules(data)
        else:
            print("Матчи не найдены")
        print(f"Отслеживается {len(tracked)} матчей")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
