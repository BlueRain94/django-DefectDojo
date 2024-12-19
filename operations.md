# Dev
- Run:
```
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d 
```

- Note:
```
Log Dedubg at django-defectdojo-uwsgi-1 container
Form prossess at django-DefectDojo\dojo\forms.py
```

# Prod
```
git clone https://github.com/BlueRain94/django-DefectDojo.git
cd django-DefectDojo
./dc-build.sh
./dc-up-d.sh
```

# Upgrade
```
git pull
dc-down.sh
dc-build.sh
dc-up-d.sh
```
# Backup Postgres
```
docker exec -t django-defectdojo-postgres-1 pg_dumpall -c -U defectdojo > dump_`date +%Y-%m-%d"_"%H_%M_%S`.sql
```

# Restore
cat your_dump.sql | docker exec -i django-defectdojo-postgres-1 psql -U defectdojo

# Trouble shooting
Error:
```
/usr/bin/env: ‘bash\r’: No such file or directory
```
When run on windows.

```
Change all end character to LF in .sh file in folder docker
Rebuild all image and up
```

Recreate admin user
```
docker compose exec uwsgi /bin/bash -c 'python manage.py createsuperuser'
```