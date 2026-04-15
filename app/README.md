# Микросервис анализа академических долгов IrGUPS

## Описание

Микросервис предоставляет API для получения информации об академических долгах студентов университета IrGUPS. 
Данные берутся из базы данных PostgreSQL и предоставляются через REST API с возможностью фильтрации.

## Установка

### Требования
- Python 3.8+
- PostgreSQL база данных
- Доступ к базе данных `eis_irgups` на сервере `hq-srv-eis-new.irgups.ru`

### Установка зависимостей

```bash
cd app
pip install -r requirements.txt
```

## Запуск

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

После запуска документация API будет доступна по адресу: http://localhost:8000/docs

## Структура базы данных

Микросервис ожидает таблицу `academic_debts` со следующей структурой:

| Поле | Тип | Описание |
|------|-----|----------|
| student_name | VARCHAR | ФИО студента |
| group_name | VARCHAR | Название группы |
| subject | VARCHAR | Название предмета |
| faculty | VARCHAR | Кафедра |
| teacher | VARCHAR | Преподаватель |
| course | INTEGER | Курс |
| semester | INTEGER | Семестр |
| subject_type | VARCHAR | Тип предмета (зачет/экзамен/диф.зачет) |
| form_of_study | VARCHAR | Форма обучения |
| basis_of_study | VARCHAR | Основа обучения (бюджет/внебюджет/целевой) |

## API Endpoints

### Общая информация

#### `GET /`
Корневой endpoint с информацией о сервисе.

#### `GET /api/summary`
Общая сводка по долгам.

**Параметры:**
- `include_practice` (bool, default=False) - учитывать учебную и производственную практику

**Ответ:**
```json
{
  "total_debts": 15278,
  "total_students": 1566,
  "date": "2024-12-11"
}
```

### Аналитика

#### `GET /api/debts/by-faculty`
Распределение долгов по кафедрам.

**Параметры:**
- `include_practice` (bool, default=False)

**Ответ:**
```json
[
  {
    "faculty": "Иностранные языки",
    "debt_count": 2500,
    "student_count": 450
  }
]
```

#### `GET /api/debts/by-subject`
Топ предметов по количеству долгов.

**Параметры:**
- `limit` (int, default=50) - максимальное количество записей
- `include_practice` (bool, default=False)

#### `GET /api/debts/by-course`
Распределение долгов по курсам.

#### `GET /api/debts/by-form`
Распределение долгов по формам обучения.

### Списки долгов

#### `GET /api/debts/list`
Получение списка долгов с фильтрацией.

**Параметры фильтрации (все необязательные):**
- `faculty` - кафедра
- `course` - курс
- `semester` - семестр
- `form_of_study` - форма обучения
- `basis_of_study` - основа обучения
- `subject_type` - тип предмета
- `student_name` - ФИО студента (частичное совпадение)
- `group` - группа (частичное совпадение)
- `include_practice` (bool, default=False)
- `limit` (int, default=100)
- `offset` (int, default=0)

**Ответ:**
```json
{
  "items": [...],
  "total": 15278,
  "limit": 100,
  "offset": 0
}
```

#### `GET /api/filters/options`
Получение доступных значений для фильтров.

**Ответ:**
```json
{
  "faculties": ["Иностранные языки", "Высшая математика", ...],
  "courses": [1, 2, 3, 4, 5],
  "semesters": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "forms_of_study": ["бакалавриат (очное)", "бакалавриат (заочное)", ...],
  "bases_of_study": ["бюджет", "внебюджет", "целевой"],
  "subject_types": ["зачет", "экзамен", "диф.зачет"]
}
```

### Детальная информация

#### `GET /api/student/{student_name}/debts`
Все долги конкретного студента.

**Параметры:**
- `student_name` - ФИО студента (частичное совпадение)
- `include_practice` (bool, default=False)

**Ответ:**
```json
{
  "student_name": "Иванов Иван",
  "total_debts": 5,
  "debts": [...]
}
```

#### `GET /api/group/{group_name}/debts`
Все долги группы.

**Параметры:**
- `group_name` - название группы (частичное совпадение)
- `include_practice` (bool, default=False)

**Ответ:**
```json
{
  "group_name": "ИС.1-23-2",
  "total_students": 25,
  "students": [
    {
      "student_name": "Иванов Иван",
      "group": "ИС.1-23-2(И,О)",
      "debt_count": 3,
      "debts": [...]
    }
  ]
}
```

### Графики

#### `GET /api/charts/overview`
Данные для построения обзорных графиков.

**Параметры:**
- `include_practice` (bool, default=False)

**Ответ:**
```json
{
  "by_course": {"1": 5000, "2": 4000, "3": 3000},
  "by_subject_type": {"зачет": 8000, "экзамен": 5000, "диф.зачет": 2278},
  "by_basis_of_study": {"бюджет": 6000, "внебюджет": 7000, "целевой": 2278}
}
```

## Примеры использования

### Получить общую статистику
```bash
curl http://localhost:8000/api/summary
```

### Получить долги по кафедре "Иностранные языки"
```bash
curl "http://localhost:8000/api/debts/list?faculty=Иностранные%20языки&limit=50"
```

### Получить долги студента
```bash
curl "http://localhost:8000/api/student/Иванов/debts"
```

### Получить данные для графиков
```bash
curl "http://localhost:8000/api/charts/overview"
```

## Конфигурация подключения к БД

Конфигурация находится в файле `main.py`:

```python
DB_CONFIG = {
    "user": "maranya",
    "password": "1A@hVIna$3",
    "host": "hq-srv-eis-new.irgups.ru",
    "database": "eis_irgups"
}
```

**Внимание:** Для продакшена рекомендуется выносить чувствительные данные в переменные окружения!

## Переменные окружения (рекомендуется для продакшена)

```bash
export DB_USER=maranya
export DB_PASSWORD=1A@hVIna$3
export DB_HOST=hq-srv-eis-new.irgups.ru
export DB_NAME=eis_irgups
```

## Docker (опционально)

Создайте `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Запуск:
```bash
docker build -t irgups-debts-api .
docker run -p 8000:8000 irgups-debts-api
```
