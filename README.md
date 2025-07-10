# Recipe API

A robust, production-ready RESTful API for managing recipes, ingredients, and tags, built with Django and Django REST Framework.

[![Tests](https://github.com/shafayetsadi/recipe-app-api/actions/workflows/checks.yaml/badge.svg)](https://github.com/shafayetsadi/recipe-app-api/actions)

## Features

- User registration and authentication (token-based)
- CRUD operations for recipes, tags, and ingredients
- Image upload for recipes
- Filtering recipes by tags and ingredients
- API documentation with OpenAPI/Swagger (via drf-spectacular)
- Dockerized for easy local development and deployment

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

### Quickstart

Clone the repository:

```sh
git clone https://github.com/yourusername/recipe-app-api.git
cd recipe-app-api
```

Build and start the services:

```sh
docker compose up
```

Apply migrations and create a superuser:

```sh
docker compose run --rm app sh -c "uv run python manage.py wait_for_db && uv run python manage.py migrate"
docker compose run --rm app sh -c "uv run python manage.py createsuperuser"
```

Run tests:

```sh
docker compose run --rm app sh -c "uv run python manage.py test"
```

### API Documentation

Once running, access the API docs at:

- Swagger UI: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- OpenAPI schema: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

## Project Structure

```text
core/       # Core app: models, admin, management commands
users/      # User registration, authentication, and profile
recipes/    # Recipes, tags, ingredients, and related endpoints
project/    # Django project settings and URLs
```

## Environment Variables

The following environment variables are used (see `docker-compose.yml`):

- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`

## Static & Media Files

- Static files are collected to `/app/staticfiles`
- Media uploads (e.g., recipe images) are stored in `/app/media`
- These are mapped to Docker volumes for persistence

## Contributing

Contributions are welcome! Please open issues and pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a pull request to the `dev` branch

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- [Pillow](https://python-pillow.org/)

---
