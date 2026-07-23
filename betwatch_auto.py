import requests
import time

print("🚀 ТЕСТ 1: Скрипт запущен!")

# Тест 1: Проверка функции find_friendly_matches()
def find_friendly_matches():
    print("   → Вызов find_friendly_matches()")
    return ["https://betwatch.fr/football/35850734"]

print("🚀 ТЕСТ 2: Вызываем find_friendly_matches()")
matches = find_friendly_matches()
print(f"   → Получено матчей: {len(matches)}")

for url in matches:
    print(f"   → URL: {url}")

print("🚀 ТЕСТ 3: Проверка загрузки страницы")
url = "https://betwatch.fr/football/35850734"
headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"   → Статус: {response.status_code}")
    print(f"   → Длина HTML: {len(response.text)}")
    
    if "Over/Under" in response.text:
        print("   ✅ Найдено Over/Under на странице")
    else:
        print("   ❌ Over/Under не найдено")
except Exception as e:
    print(f"   ❌ Ошибка загрузки: {e}")

print("🚀 ТЕСТ 4: Скрипт завершён!")
