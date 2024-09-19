SELECT * FROM pg_catalog.pg_tables;

SELECT datname FROM pg_database;

SELECT table_schema,table_name
FROM information_schema.tables
WHERE table_name ~* 'burp'
ORDER BY table_schema,table_name;

select * from dojo_burprawrequestresponse;
