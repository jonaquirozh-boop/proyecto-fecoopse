#!/bin/bash
set -e

echo "=== FECOOPSE Evaluaciones ==="
echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Cargando datos iniciales..."
python manage.py loaddata evaluacion/fixtures/preguntas_iniciales.json || echo "Preguntas ya existen, omitiendo."
python manage.py loaddata evaluacion/fixtures/actividad_demo.json || echo "Actividad demo ya existe, omitiendo."

echo "Iniciando servidor Gunicorn..."
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
