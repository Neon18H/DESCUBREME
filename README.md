# descubriendo (MVP)

Aplicación web Django + PostgreSQL que recomienda lugares y genera planes por bloques (tarde/noche) según mood, tiempo, presupuesto y preferencias.

## Stack
- Django 4.x
- PostgreSQL
- Bootstrap 5 + CSS/JS vanilla
- Google Places API
- OpenRouter API

## 1) Requisitos
- Python 3.10+
- PostgreSQL 14+
- pip + venv

## 2) Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 3) Configurar PostgreSQL
Crear DB y usuario (ejemplo):
```sql
CREATE DATABASE descubriendo;
CREATE USER descubriendo_user WITH PASSWORD 'segura123';
GRANT ALL PRIVILEGES ON DATABASE descubriendo TO descubriendo_user;
```

En `.env`:
```env
DATABASE_URL=postgres://descubriendo_user:segura123@localhost:5432/descubriendo
```

## 4) Variables de entorno
Completar en `.env`:
- `SECRET_KEY`
- `DEBUG=True`
- `DATABASE_URL`
- `GOOGLE_PLACES_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` (por defecto free-tier)
- `OPENROUTER_BASE_URL`
- `APP_REFERER`

## 5) Ejecutar migraciones y servidor
```bash
python manage.py migrate
python manage.py runserver
```

Abrir: http://127.0.0.1:8000/

## Flujo MVP
1. Landing con CTA.
2. Formulario para ciudad/mood/horarios/budget/grupo/transporte/intereses/radio.
3. Backend consulta Google Places y luego OpenRouter para estructurar JSON.
4. Se valida JSON estricto y se guarda en PostgreSQL (`Plan`, `PlanStep`).
5. Vistas de resultados, guardados, detalle y eliminar.

## Estructura principal
- `descubriendo/settings.py`: configuración env, DB, APIs.
- `core/services/google_places.py`: Text Search + Place Details.
- `core/services/openrouter_ai.py`: cliente OpenRouter + retry para JSON.
- `core/services/planner.py`: orquestación y validación del plan.
- `core/templates/`: landing, generar, resultados, guardados, detalle.
