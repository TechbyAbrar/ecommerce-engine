#project file structure

app/
│
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── logging.py
│   ├── celery.py
│   ├── email.py
│   ├── exceptions.py
│   ├── dependencies.py
│   └── constants.py
│
├── common/
│   ├── enums.py
│   ├── pagination.py
│   ├── responses.py
│   ├── utils.py
│   └── validators.py
│
├── auth/
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py
│   ├── schemas.py
│   ├── dependencies.py
│   ├── security.py
│   ├── otp_service.py
│   ├── tasks.py
│   └── exceptions.py
│
├── users/
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py
│   ├── schemas.py
│   └── exceptions.py
│
├── categories/
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py
│   ├── schemas.py
│   ├── dfs.py
│   └── cache.py
│
├── products/
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py
│   ├── schemas.py
│   ├── dependencies.py
│   └── exceptions.py
│
├── orders/
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py
│   ├── schemas.py
│   ├── algorithms.py
│   └── exceptions.py
│
├── payments/
│   ├── router.py
│   ├── service.py
│   ├── repository.py
│   ├── models.py
│   ├── schemas.py
│   ├── strategy.py
│   ├── factory.py
│   ├── stripe_strategy.py
│   ├── bkash_strategy.py
│   ├── webhook.py
│   └── exceptions.py
│
├── redis/
│   ├── client.py
│   └── cache.py
│
├── db/
│   ├── seed.py
│   └── base.py
│
├── tests/
│   ├── auth/
│   ├── users/
│   ├── products/
│   ├── orders/
│   ├── payments/
│   └── conftest.py
│
├── main.py
│
├── __init__.py
│
└── alembic/
