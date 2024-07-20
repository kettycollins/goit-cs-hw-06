# Використовуємо базовий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо файли з нашого проєкту в контейнер
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Копіюємо основні файли додатку
COPY main.py main.py
COPY style.css style.css
COPY logo.png logo.png
COPY index.html index.html
COPY message.html message.html
COPY error.html error.html

# Копіюємо дані з директорії storage
COPY storage/data.json storage/data.json

# Відкриваємо порти для HTTP і Socket серверів
EXPOSE 3000
EXPOSE 5000

# Команда для запуску додатку
CMD ["python", "main.py"]
