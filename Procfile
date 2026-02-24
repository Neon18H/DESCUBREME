release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn descubriendo.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --log-file -
