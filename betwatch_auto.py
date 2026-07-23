import requests
import re
import json
import time
from datetime import datetime

# ===== НАСТРОЙКИ =====
TELEGRAM_TOKEN = "8913782012:AAHgCpW3pDvMGVci00IYeaO6U4GCUQ0oPog"
CHAT_ID = "768631559"
CHECK_INTERVAL = 30  # секунд

RULES = [
    {"markets": ["Over/Under 3.5 Goals", "Over/Under 2.5 Goals", "Over/Under 1.5 Goals"], "window_minutes": 5, "threshold": 5000},
    {"markets": ["Over/Under 0.5 Goals", "Over/Under 1.5 Goals", "Over/Under 2.5 Goals"], "window_minutes": 4, "threshold": 5000}
]

history = {}

# ===== ФУНКЦИИ =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.text if response.status_code == 200 else None
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
        return None

def find_friendly_matches():
    """Ищет ссылки на товарищеские матчи через поиск по странице /money"""
    html = fetch_html("https://betwatch.fr/money")
    if not html:
        return []
    
    # Ищем все ссылки /football/число
    links = re.findall(r'href="(/football/\d+)"', html)
    if not links:
        # Если ссылок нет, возможно, страница динамическая — пробуем искать в JSON
        json_data = re.search(r'"events":\s*(\[.*?\])', html, re.DOTALL)
        if json_data:
            try:
                events = json.loads(json_data.group(1))
                for event in events:
                    if "Friendly" in event.get("league_name", "") or "International" in event.get("league_name", ""):
                        return [f"https://betwatch.fr/football/{event['id']}"]
            except:
                pass
        return []
    
    # Фильтруем только товарищеские (проверяем каждую страницу)
    friendly = []
    for link in set(links):
        full_url = "https://betwatch.fr" + link
        match_html = fetch_html(full_url)
        if match_html and ("Friendly" in match_html or "International" in match_html):
            friendly.append(full_url)
            print(f"✅ Найден товарищеский матч: {full_url}")
        time.sleep(0.5)  # пауза, чтобы не нагружать сайт
    return friendly

def get_match_data(url):
    html = fetch_html(url)
    if not html:
        return None
    
    # Извлекаем game JSON
    game_match = re.search(r'game = ({.*?});', html, re.DOTALL)
    if not game_match:
        return None
    
    game_data = json.loads(game_match.group(1))
    
    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    match_name = title_match.group(1).strip() if title_match else "Unknown Match"
    
    is_live = game_data.get('l', False)
    live_info = game_data.get('live_info', {})
    minute = None
    score = None
    if is_live and live_info:
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
    if not match_data or not match_data["is_live"]:
        return
    
    minute = match_data["minute"]
    if minute and int(minute) > 45:
        return
    
    game_data = match_data["game"]
    match_name = match_data["match_name"]
    score = match_data["score"]
    url = match_data["url"]
    
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
                                msg = (
                                    f"🔥 <b>СИГНАЛ!</b>\n"
                                    f"{match_name}\n"
                                    f"{score or ''} {minute or ''}'\n"
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
    tracked = []
    
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Проверка...")
        matches = find_friendly_matches()
        
        if matches:
            for url in matches:
                if url not in tracked:
                    tracked.append(url)
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