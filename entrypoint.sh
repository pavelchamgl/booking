python3 config/manage.py collectstatic --no-input;
python3 config/manage.py migrate;
python3 config/manage.py loaddata config/fixtures.json;
python3 config/manage.py runserver 0.0.0.0:8000;