# FECOOPSE - Formulario de Evaluación Digital

Sistema de evaluación digital para actividades de capacitación de FECOOPSE.
Formulario multi-paso minimalista con dashboard de resultados en tiempo real.

## Stack
- Django 5 + Django REST Framework
- SQLite (base de datos)
- TailwindCSS + Alpine.js + Chart.js
- Gunicorn + WhiteNoise
- Docker + Easypanel

## Desarrollo local

```bash
# 1. Clonar el repositorio
git clone https://github.com/jonaquirozh-boop/proyecto-fecoopse.git
cd proyecto-fecoopse

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 4. Migrar base de datos y cargar datos iniciales
python manage.py migrate
python manage.py loaddata evaluacion/fixtures/preguntas_iniciales.json
python manage.py loaddata evaluacion/fixtures/actividad_demo.json

# 5. Crear superusuario (opcional)
python manage.py createsuperuser

# 6. Iniciar servidor
python manage.py runserver
```

## URLs principales

| URL | Descripción |
|-----|-------------|
| `/formulario/` | Formulario público de evaluación |
| `/gracias/` | Pantalla de confirmación post-envío |
| `/resultados/<clave>/` | Dashboard de resultados (URL secreta) |
| `/admin/` | Panel administrativo Django |
| `/api/evaluacion/` | API POST para enviar evaluaciones |
| `/api/resultados/<clave>/` | API GET de resultados en JSON |

## Dashboard de resultados

URL del dashboard de demo:
`/resultados/fecoopse-resultados-2026/`

## Variables de entorno (.env)

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com
DATABASE_PATH=/app/data/db.sqlite3
```

## Despliegue en Easypanel

1. Crear nuevo servicio tipo "App" en Easypanel.
2. Conectar repositorio GitHub: `jonaquirozh-boop/proyecto-fecoopse`.
3. Branch: `main`.
4. Build method: `Dockerfile`.
5. Puerto: `8000`.
6. Agregar volumen persistente: `/app/data`.
7. Configurar variables de entorno (ver sección anterior).
8. Deploy.

## Admin

URL: `/admin/`

Usuario por defecto: `admin`

Contraseña por defecto: `FecoopseAdmin2026`

⚠️ Cambiar la contraseña en producción desde el admin.
