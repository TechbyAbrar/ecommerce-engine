# Backend project structure

This document reflects the current backend layout in the repository.

## Root backend layout

backend/
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── .python-version
├── Dockerfile
├── README.md
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── alembic/
├── app/
├── cli/
├── docker/
├── docs/
└── logs/

## Application package

backend/app/
├── __init__.py
├── main.py
├── alembic/
├── auth/
│   ├── __init__.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── models.py
│   ├── otp_service.py
│   ├── repository.py
│   ├── router.py
│   ├── schemas.py
│   ├── security.py
│   ├── service.py
│   └── tasks.py
├── categories/
│   ├── __init__.py
│   ├── cache.py
│   ├── dfs.py
│   ├── models.py
│   ├── repository.py
│   ├── router.py
│   ├── schemas.py
│   └── service.py
├── common/
│   ├── __init__.py
│   ├── enums.py
│   ├── pagination.py
│   ├── responses.py
│   ├── utils.py
│   └── validators.py
├── core/
│   ├── __init__.py
│   ├── celery.py
│   ├── config.py
│   ├── constants.py
│   ├── database.py
│   ├── dependencies.py
│   ├── email.py
│   ├── exceptions.py
│   ├── logging.py
│   ├── operations_service.py
│   ├── reference_models.py
│   ├── reference_repository.py
│   ├── reference_service.py
│   └── security.py
├── db/
│   ├── __init__.py
│   ├── base.py
│   └── seed.py
├── orders/
│   ├── __init__.py
│   ├── algorithms.py
│   ├── exceptions.py
│   ├── models.py
│   ├── repository.py
│   ├── router.py
│   ├── schemas.py
│   └── service.py
├── payments/
│   ├── __init__.py
│   ├── bkash_strategy.py
│   ├── exceptions.py
│   ├── factory.py
│   ├── models.py
│   ├── repository.py
│   ├── router.py
│   ├── schemas.py
│   ├── service.py
│   ├── strategy.py
│   ├── stripe_strategy.py
│   └── webhook.py
├── products/
│   ├── __init__.py
│   ├── cache.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── models.py
│   ├── repository.py
│   ├── router.py
│   ├── schemas.py
│   ├── service.py
│   └── storage.py
├── redis/
│   ├── __init__.py
│   ├── cache.py
│   └── client.py
├── tests/
│   ├── conftest.py
│   ├── auth/
│   ├── orders/
│   ├── payments/
│   ├── products/
│   └── users/
└── users/
    ├── __init__.py
    ├── exceptions.py
    ├── models.py
    ├── repository.py
    ├── router.py
    ├── schemas.py
    └── service.py

## CLI package

backend/cli/
├── __init__.py
├── dependencies.py
├── exceptions.py
├── manage.py
├── output.py
├── prompts.py
└── commands/

## Infrastructure and deployment files

backend/docker/
├── api-entrypoint.sh
├── healthcheck.py
├── migrate-entrypoint.sh
└── worker-entrypoint.sh

backend/docker-compose.yml
backend/Dockerfile
