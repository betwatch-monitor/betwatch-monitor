import requests

print("🚀 ТЕСТОВЫЙ СКРИПТ ЗАПУЩЕН!")

url = "https://betwatch.fr/football/35850734"
headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Статус: {response.status_code}")
    print(f"Длина HTML: {len(response.text)}")
    
    if "Over/Under" in response.text:
        print("✅ Найдено Over/Under на странице")
    else:
        print("❌ Over/Under не найдено")
except Exception as e:
    print(f"Ошибка: {e}")
