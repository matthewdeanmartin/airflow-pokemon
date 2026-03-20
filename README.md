# airflow pokemon

Move data from the wikipedia page to sqlitedb.


## Notes

- airflow will refuse to run on Windows
- airflow really wants to run as a large collection of specialized servers
- auth is disabled

## Steps

```bash
# builds docker container
make build
# runs docker container & starts webserver
make run
# shows logs... it can be a long wait before the server starts up
make logs
```