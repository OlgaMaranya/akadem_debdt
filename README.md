# IrGUPS Academic Debts Microservice

## Структура проекта

```
app/
├── main.py              # Основной файл приложения FastAPI
├── requirements.txt     # Python зависимости
├── Dockerfile          # Docker конфигурация
└── README.md           # Документация
```

## Быстрый старт

### 1. Установка зависимостей

```bash
cd app
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Проверка работы

Откройте в браузере:
- API документация: http://localhost:8000/docs
- Корневой endpoint: http://localhost:8000/

## Использование через Docker

```bash
# Сборка образа
docker build -t irgups-debts-api .

# Запуск контейнера
docker run -p 8000:8000 irgups-debts-api
```

## Основные возможности

✅ **Получение общей статистики** по академическим долгам
✅ **Аналитика по кафедрам, курсам, предметам**
✅ **Гибкая фильтрация** (по кафедре, курсу, семестру, форме обучения и т.д.)
✅ **Поиск по студенту или группе**
✅ **Данные для построения графиков**
✅ **Пагинация результатов**

## Примеры запросов

```bash
# Общая статистика
curl http://localhost:8000/api/summary

# Долги по кафедрам
curl http://localhost:8000/api/debts/by-faculty

# Список долгов с фильтрами
curl "http://localhost:8000/api/debts/list?course=1&form_of_study=бакалавриат%20(очное)"

# Долги конкретного студента
curl "http://localhost:8000/api/student/Иванов/debts"

# Данные для графиков
curl http://localhost:8000/api/charts/overview
```

## Требования к базе данных

Микросервис подключается к PostgreSQL базе данных `eis_irgups` и ожидает таблицу `academic_debts`:

```sql
CREATE TABLE academic_debts (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    group_name VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    faculty VARCHAR(255),
    teacher VARCHAR(255),
    course INTEGER,
    semester INTEGER,
    subject_type VARCHAR(50),
    form_of_study VARCHAR(100),
    basis_of_study VARCHAR(50)
);
```

## Конфигурация подключения

По умолчанию используется подключение:
- Host: hq-srv-eis-new.irgups.ru
- Database: eis_irgups
- User: maranya

Для изменения настроек отредактируйте `DB_CONFIG` в файле `main.py` или используйте переменные окружения.
