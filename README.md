# ChatAi

Веб-приложение для чата с ИИ, построенное на FastAPI с поддержкой различных моделей ИИ (OpenAI, DeepSeek).

## Особенности

- 🤖 Поддержка множественных ИИ моделей (OpenAI GPT, DeepSeek)
- 🔐 Система аутентификации с JWT токенами
- 💬 Сохранение истории чатов
- 🚀 WebSocket поддержка для реального времени
- 📊 Интеграция с Redis для кэширования
- 🐳 Docker готовая конфигурация
- 🗄️ PostgreSQL база данных с миграциями Alembic

## Технологический стек

- **Backend**: FastAPI
- **База данных**: PostgreSQL с SQLAlchemy ORM
- **Кэш**: Redis
- **Аутентификация**: JWT с python-jose
- **Миграции**: Alembic
- **Контейнеризация**: Docker & Docker Compose
- **Шаблоны**: Jinja2

## Структура проекта

```
ChatAi/
├── app/                    # Основное приложение
│   ├── models/            # Модели базы данных
│   ├── routers/           # API роутеры
│   ├── services/          # Бизнес логика
│   ├── templates/         # HTML шаблоны
│   └── utils/             # Утилиты
├── auth/                  # Модуль аутентификации
├── dao/                   # Data Access Objects
├── database/              # Конфигурация БД
├── migration/             # Миграции Alembic
├── docker-compose.yml     # Docker конфигурация
├── requirements.txt       # Python зависимости
└── settings.py           # Настройки приложения
```

## Быстрый старт

### Предварительные требования

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (если запуск без Docker)
- Redis (если запуск без Docker)

### Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd ChatAi
```

2. Создайте файл `.env` в корневой директории:
```env
# API ключи
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Redis
REDIS_URL=redis://localhost:6379

# База данных
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatai

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
```

3. Запуск с Docker Compose (рекомендуется):
```bash
docker-compose up --build
```

4. Или установка для разработки:
```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

## API Эндпоинты

### Основные роутеры:
- `/` - Главная страница чата
- `/auth/` - Аутентификация (логин, регистрация)
- `/config/` - Конфигурация параметров ИИ
- `/history/` - История чатов

### WebSocket:
- `/ws` - WebSocket соединение для чата в реальном времени

## Конфигурация

Приложение использует переменные окружения для конфигурации. Все настройки определены в `settings.py` с использованием Pydantic Settings.

### Основные настройки:
- `OPENAI_API_KEY` - API ключ для OpenAI
- `DEEPSEEK_API_KEY` - API ключ для DeepSeek
- `REDIS_URL` - URL подключения к Redis
- База данных PostgreSQL настройки
- JWT секретный ключ и алгоритм

## База данных

Приложение использует PostgreSQL с SQLAlchemy ORM. Миграции управляются через Alembic.

### Команды миграций:
```bash
# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

## Разработка

### Структура роутеров:
- `index.py` - Главная страница и WebSocket
- `conf_param_ai.py` - Конфигурация ИИ
- `history.py` - История чатов
- `auth_routher.py` - Аутентификация

### Сервисы:
- `get_ai.py` - Получение клиентов ИИ
- `gpt.py` - Обработка сообщений
- `get_token.py` - Работа с JWT токенами
- `history_view.py` - Просмотр истории
- `save_history_from_redis.py` - Сохранение истории

## Docker

Проект включает готовую конфигурацию Docker с:
- Веб-приложение на порту 8000
- Redis на порту 6379
- Автоматическая перезагрузка при изменениях
- Volumes для персистентности данных

## Лицензия

[Укажите вашу лицензию]

## Вклад в проект

1. Форкните проект
2. Создайте feature ветку (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request
