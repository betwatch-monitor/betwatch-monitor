import time
from datetime import datetime

print("🚀 Тестовый скрипт запущен!", flush=True)

for i in range(10):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Шаг {i+1}/10", flush=True)
    time.sleep(10)

print("✅ Тестовый скрипт завершён", flush=True)
    
