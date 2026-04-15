"""
Микросервис для анализа академических долгов IrGUPS
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import date, datetime
import json

app = FastAPI(
    title="IrGUPS Academic Debts API",
    description="Микросервис для расчета и анализа академических долгов в университете",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация базы данных
DB_CONFIG = {
    "user": "maranya",
    "password": "1A@hVIna$3",
    "host": "hq-srv-eis-new.irgups.ru",
    "database": "eis_irgups"
}


def get_db_connection():
    """Получение подключения к базе данных"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к БД: {str(e)}")


# ==================== Pydantic модели ====================

class DebtSummary(BaseModel):
    """Сводка по долгам"""
    total_debts: int
    total_students: int
    date: str


class DebtByFaculty(BaseModel):
    """Долги по факультетам/кафедрам"""
    faculty: str
    debt_count: int
    student_count: int


class DebtBySubject(BaseModel):
    """Долги по предметам"""
    subject: str
    debt_count: int
    subject_type: str


class StudentDebt(BaseModel):
    """Информация о долге студента"""
    student_name: str
    group: str
    subject: str
    faculty: str
    teacher: str
    course: int
    semester: int
    subject_type: str
    form_of_study: str
    basis_of_study: str


class FilterParams(BaseModel):
    """Параметры фильтрации"""
    faculty: Optional[str] = None
    course: Optional[int] = None
    semester: Optional[int] = None
    form_of_study: Optional[str] = None
    basis_of_study: Optional[str] = None
    subject_type: Optional[str] = None


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "IrGUPS Academic Debts API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/api/summary", response_model=DebtSummary)
async def get_summary(
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить общую сводку по академическим долгам
    
    - **include_practice**: Учитывать учебную и производственную практику
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Запрос общей статистики
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    WHERE subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            query = f"""
                SELECT 
                    COUNT(*) as total_debts,
                    COUNT(DISTINCT student_name) as total_students
                FROM academic_debts
                {practice_filter}
            """
            cur.execute(query)
            result = cur.fetchone()
            
            return DebtSummary(
                total_debts=result['total_debts'] or 0,
                total_students=result['total_students'] or 0,
                date=date.today().isoformat()
            )
    finally:
        conn.close()


@app.get("/api/debts/by-faculty")
async def get_debts_by_faculty(
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить распределение долгов по кафедрам
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    WHERE subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            query = f"""
                SELECT 
                    COALESCE(faculty, 'Кафедра не указана') as faculty,
                    COUNT(*) as debt_count,
                    COUNT(DISTINCT student_name) as student_count
                FROM academic_debts
                {practice_filter}
                GROUP BY faculty
                ORDER BY debt_count DESC
            """
            cur.execute(query)
            results = cur.fetchall()
            
            return [dict(row) for row in results]
    finally:
        conn.close()


@app.get("/api/debts/by-subject")
async def get_debts_by_subject(
    limit: int = Query(50, description="Максимальное количество записей"),
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить топ предметов по количеству долгов
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    WHERE subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            query = f"""
                SELECT 
                    subject,
                    subject_type,
                    COUNT(*) as debt_count
                FROM academic_debts
                {practice_filter}
                GROUP BY subject, subject_type
                ORDER BY debt_count DESC
                LIMIT %s
            """
            cur.execute(query, (limit,))
            results = cur.fetchall()
            
            return [dict(row) for row in results]
    finally:
        conn.close()


@app.get("/api/debts/by-course")
async def get_debts_by_course(
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить распределение долгов по курсам
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    WHERE subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            query = f"""
                SELECT 
                    course,
                    COUNT(*) as debt_count,
                    COUNT(DISTINCT student_name) as student_count
                FROM academic_debts
                {practice_filter}
                GROUP BY course
                ORDER BY course
            """
            cur.execute(query)
            results = cur.fetchall()
            
            return [dict(row) for row in results]
    finally:
        conn.close()


@app.get("/api/debts/by-form")
async def get_debts_by_form_of_study(
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить распределение долгов по формам обучения
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    WHERE subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            query = f"""
                SELECT 
                    form_of_study,
                    COUNT(*) as debt_count,
                    COUNT(DISTINCT student_name) as student_count
                FROM academic_debts
                {practice_filter}
                GROUP BY form_of_study
                ORDER BY debt_count DESC
            """
            cur.execute(query)
            results = cur.fetchall()
            
            return [dict(row) for row in results]
    finally:
        conn.close()


@app.get("/api/debts/list")
async def get_debts_list(
    faculty: Optional[str] = Query(None, description="Кафедра"),
    course: Optional[int] = Query(None, description="Курс"),
    semester: Optional[int] = Query(None, description="Семестр"),
    form_of_study: Optional[str] = Query(None, description="Форма обучения"),
    basis_of_study: Optional[str] = Query(None, description="Основа обучения"),
    subject_type: Optional[str] = Query(None, description="Тип предмета"),
    student_name: Optional[str] = Query(None, description="ФИО студента"),
    group: Optional[str] = Query(None, description="Группа"),
    include_practice: bool = Query(False, description="Учитывать практику"),
    limit: int = Query(100, description="Максимальное количество записей"),
    offset: int = Query(0, description="Смещение")
):
    """
    Получить список долгов с фильтрацией
    
    Параметры фильтров необязательны. Можно комбинировать любые фильтры.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Построение динамического запроса
            conditions = []
            params = {}
            
            if not include_practice:
                conditions.append("subject NOT LIKE %(practice1)s")
                conditions.append("subject NOT LIKE %(practice2)s")
                params['practice1'] = 'Учебная%'
                params['practice2'] = 'Производственная%'
            
            if faculty:
                conditions.append("faculty = %(faculty)s")
                params['faculty'] = faculty
            
            if course:
                conditions.append("course = %(course)s")
                params['course'] = course
            
            if semester:
                conditions.append("semester = %(semester)s")
                params['semester'] = semester
            
            if form_of_study:
                conditions.append("form_of_study = %(form_of_study)s")
                params['form_of_study'] = form_of_study
            
            if basis_of_study:
                conditions.append("basis_of_study = %(basis_of_study)s")
                params['basis_of_study'] = basis_of_study
            
            if subject_type:
                conditions.append("subject_type = %(subject_type)s")
                params['subject_type'] = subject_type
            
            if student_name:
                conditions.append("student_name ILIKE %(student_name)s")
                params['student_name'] = f"%{student_name}%"
            
            if group:
                conditions.append("group_name ILIKE %(group)s")
                params['group'] = f"%{group}%"
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT 
                    student_name,
                    group_name as group,
                    subject,
                    faculty,
                    teacher,
                    course,
                    semester,
                    subject_type,
                    form_of_study,
                    basis_of_study
                FROM academic_debts
                {where_clause}
                ORDER BY student_name, group_name, subject
                LIMIT %(limit)s OFFSET %(offset)s
            """
            
            params['limit'] = limit
            params['offset'] = offset
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # Получение общего количества для пагинации
            count_query = f"""
                SELECT COUNT(*) as total
                FROM academic_debts
                {where_clause}
            """
            cur.execute(count_query, params)
            total = cur.fetchone()['total']
            
            return {
                "items": [dict(row) for row in results],
                "total": total,
                "limit": limit,
                "offset": offset
            }
    finally:
        conn.close()


@app.get("/api/filters/options")
async def get_filter_options():
    """
    Получить доступные значения для фильтров
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Кафедры
            cur.execute("""
                SELECT DISTINCT COALESCE(faculty, 'Кафедра не указана') as faculty
                FROM academic_debts
                ORDER BY faculty
            """)
            faculties = [row['faculty'] for row in cur.fetchall()]
            
            # Курсы
            cur.execute("SELECT DISTINCT course FROM academic_debts ORDER BY course")
            courses = [row['course'] for row in cur.fetchall()]
            
            # Семестры
            cur.execute("SELECT DISTINCT semester FROM academic_debts ORDER BY semester")
            semesters = [row['semester'] for row in cur.fetchall()]
            
            # Формы обучения
            cur.execute("SELECT DISTINCT form_of_study FROM academic_debts ORDER BY form_of_study")
            forms = [row['form_of_study'] for row in cur.fetchall()]
            
            # Основы обучения
            cur.execute("SELECT DISTINCT basis_of_study FROM academic_debts ORDER BY basis_of_study")
            bases = [row['basis_of_study'] for row in cur.fetchall()]
            
            # Типы предметов
            cur.execute("SELECT DISTINCT subject_type FROM academic_debts ORDER BY subject_type")
            types = [row['subject_type'] for row in cur.fetchall()]
            
            return {
                "faculties": faculties,
                "courses": courses,
                "semesters": semesters,
                "forms_of_study": forms,
                "bases_of_study": bases,
                "subject_types": types
            }
    finally:
        conn.close()


@app.get("/api/student/{student_name}/debts")
async def get_student_debts(
    student_name: str,
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить все долги конкретного студента
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    AND subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            query = f"""
                SELECT 
                    student_name,
                    group_name as group,
                    subject,
                    faculty,
                    teacher,
                    course,
                    semester,
                    subject_type,
                    form_of_study,
                    basis_of_study
                FROM academic_debts
                WHERE student_name ILIKE %(student_name)s
                {practice_filter}
                ORDER BY course, semester, subject
            """
            
            cur.execute(query, {"student_name": f"%{student_name}%"})
            results = cur.fetchall()
            
            return {
                "student_name": student_name,
                "total_debts": len(results),
                "debts": [dict(row) for row in results]
            }
    finally:
        conn.close()


@app.get("/api/group/{group_name}/debts")
async def get_group_debts(
    group_name: str,
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить все долги группы
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    WHERE subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            query = f"""
                SELECT 
                    student_name,
                    group_name as group,
                    subject,
                    faculty,
                    teacher,
                    course,
                    semester,
                    subject_type,
                    form_of_study,
                    basis_of_study
                FROM academic_debts
                {practice_filter}
                {"AND " if practice_filter else "WHERE "} group_name ILIKE %(group_name)s
                ORDER BY student_name, subject
            """
            
            cur.execute(query, {"group_name": f"%{group_name}%"})
            results = cur.fetchall()
            
            # Группировка по студентам
            students = {}
            for row in results:
                name = row['student_name']
                if name not in students:
                    students[name] = {
                        "student_name": name,
                        "group": row['group'],
                        "debt_count": 0,
                        "debts": []
                    }
                students[name]['debt_count'] += 1
                students[name]['debts'].append({
                    "subject": row['subject'],
                    "faculty": row['faculty'],
                    "teacher": row['teacher'],
                    "course": row['course'],
                    "semester": row['semester'],
                    "subject_type": row['subject_type']
                })
            
            return {
                "group_name": group_name,
                "total_students": len(students),
                "students": list(students.values())
            }
    finally:
        conn.close()


@app.get("/api/charts/overview")
async def get_chart_overview_data(
    include_practice: bool = Query(False, description="Учитывать практику")
):
    """
    Получить данные для построения обзорных графиков
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            practice_filter = ""
            if not include_practice:
                practice_filter = """
                    WHERE subject NOT LIKE 'Учебная%' 
                    AND subject NOT LIKE 'Производственная%'
                """
            
            # Долги по курсам
            cur.execute(f"""
                SELECT course, COUNT(*) as count
                FROM academic_debts
                {practice_filter}
                GROUP BY course
                ORDER BY course
            """)
            by_course = {row['course']: row['count'] for row in cur.fetchall()}
            
            # Долги по типам предметов
            cur.execute(f"""
                SELECT subject_type, COUNT(*) as count
                FROM academic_debts
                {practice_filter}
                GROUP BY subject_type
                ORDER BY count DESC
            """)
            by_type = {row['subject_type']: row['count'] for row in cur.fetchall()}
            
            # Долги по основам обучения
            cur.execute(f"""
                SELECT basis_of_study, COUNT(*) as count
                FROM academic_debts
                {practice_filter}
                GROUP BY basis_of_study
                ORDER BY count DESC
            """)
            by_basis = {row['basis_of_study']: row['count'] for row in cur.fetchall()}
            
            return {
                "by_course": by_course,
                "by_subject_type": by_type,
                "by_basis_of_study": by_basis
            }
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
