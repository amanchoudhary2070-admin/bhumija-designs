release: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py bootstrap
web: gunicorn config.wsgi --log-file -
