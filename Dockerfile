FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 6000

# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6000"]