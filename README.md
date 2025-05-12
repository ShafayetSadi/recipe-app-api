# recipe-app-api

Recipe API Project

- `docker-compose up` to run the project

```sh
docker compose run --rm app sh -c "uv run python manage.py wait_for_db && uv run python manage.py migrate"
```
