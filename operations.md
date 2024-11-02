# Dev
- Run:
```
docker compose -f docker-compose.yml -f docker-compose.override.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.override.dev.yml up -d 
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