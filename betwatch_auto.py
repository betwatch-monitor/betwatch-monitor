import requests
import re
import json
from datetime import datetime

print("🚀 ТЕСТОВЫЙ СКРИПТ ЗАПУЩЕН!")

# Функция для загрузки страницы
def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Статус загрузки {url}: {response.status_code}")
        return response.text if response.status_code == 200 else None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

# Страница матча Venezia — Pesaro
url = "https://betwatch.fr/football/35850734"
print(f"Загружаем страницу: {url}")

html = fetch_html(url)

if html:
    print(f"✅ Страница загружена, длина HTML: {len(html)} символов")
    
    # Проверяем, есть ли game JSON
    game_match = re.search(r'game = ({.*?});', html, re.DOTALL)
    if game_match:
        print("✅ game JSON найден!")
        try:
            game_data = json.loads(game_match.group(1))
            print("✅ game JSON успешно распарсен!")
            
            # Проверяем, есть ли рынки
            markets = game_data.get('i', {})
            print(f"Найдено рынков: {len(markets)}")
            for uuid, market in markets.items():
                print(f"  - {market.get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
    else:
        print("❌ game JSON НЕ НАЙДЕН!")
        # Выводим первые 500 символов HTML для проверки
        print("Первые 500 символов HTML:")
        print(html[:500])
else:
    print("❌ Страница не загружена!")
