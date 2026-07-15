# Build a Production-Grade CLI Management System

Implement a production-grade CLI management system for an enterprise FastAPI e-commerce backend.

## CLI Structure

```text
backend/
│
├── app/
│   ├── auth/
│   ├── users/
│   ├── products/
│   ├── categories/
│   ├── orders/
│   ├── payments/
│   ├── core/
│   ├── db/
│   └── main.py
│
├── cli/
│   ├── __init__.py
│   ├── manage.py
│   ├── dependencies.py
│   ├── output.py
│   ├── prompts.py
│   ├── exceptions.py
│   └── commands/
│       ├── createsuperuser.py
│       ├── createstaff.py
│       ├── createuser.py
│       ├── promoteuser.py
│       ├── demoteuser.py
│       ├── resetpassword.py
│       ├── seed.py
│       ├── clearcache.py
│       ├── backupdb.py
│       ├── restoredb.py
│       ├── healthcheck.py
│       └── cleanuplogs.py
│
└── alembic/
```

---

## Architecture

```text
                         Terminal
                             │
                             ▼
python -m cli.manage <command>
                             │
                             ▼
                    Typer CLI Router
                             │
                             ▼
                  CLI Command Module
                             │
                             ▼
        Existing Application Service Layer
          (app/*/service.py only)
                             │
                             ▼
                 Repository Layer
                             │
                             ▼
          PostgreSQL / Redis / Storage
```

---

## Rules

* Use **Typer**.
* Entry point must be:

```bash
python -m cli.manage <command>
```

* Follow Django-style command names (no hyphens):

```text
createsuperuser
createstaff
createuser
promoteuser
demoteuser
resetpassword
seed
clearcache
backupdb
restoredb
healthcheck
cleanuplogs
```

* CLI is **only an entry point**.
* Never place business logic inside CLI commands.
* Commands must call the existing Service layer only.
* Services use repositories.
* Repositories handle all database operations.
* Reuse existing SQLAlchemy AsyncSession, authentication, password hashing, logging, configuration, and exception handling.
* Follow SOLID, DRY, SRP, Clean Architecture, Repository Pattern, and Service Layer Pattern.
* Fully async where appropriate.
* Fully typed and production-ready.

---

## Command Responsibilities

### createsuperuser

* Create the initial superuser.
* Refuse duplicate email.
* Prevent multiple superusers unless `--force` is explicitly provided.

### createstaff

* Create a new staff account.

### createuser

* Create a normal user.

### promoteuser

* Promote an existing user to STAFF, ADMIN, or SUPERUSER.
* Validate the role transition.
* Never create a new account.

### demoteuser

* Downgrade an existing user's role.

### resetpassword

* Securely reset a user's password.

### seed

* Seed only reference data:

  * Roles
  * Permissions
  * Categories
  * Order Statuses
  * Payment Methods
  * Shipping Methods
  * Default System Settings
* Must be idempotent.

### clearcache

* Safely clear Redis.

### backupdb

* Perform PostgreSQL backup.

### restoredb

* Restore PostgreSQL backup.

### healthcheck

* Verify PostgreSQL, Redis, Celery, SMTP, Storage, and external integrations.

### cleanuplogs

* Remove expired log files according to retention policy.

---

## Internal Flow

```text
Developer
     │
     ▼
python -m cli.manage promoteuser
     │
     ▼
Collect CLI arguments / prompt for missing values
     │
     ▼
Validate input
     │
     ▼
Create AsyncSession
     │
     ▼
Call Existing Service
     │
     ▼
Repository
     │
     ▼
Database
     │
     ▼
Commit / Rollback
     │
     ▼
Rich formatted success or error output
```

---

## Quality Requirements

* Professional developer experience similar to Django's `manage.py`.
* Automatic `--help` support.
* Rich colored terminal output.
* Hidden password prompts.
* Interactive mode when required arguments are omitted.
* Non-interactive mode via CLI options for automation.
* Proper exit codes.
* Structured logging.
* Comprehensive error handling.
* Easy to extend with additional commands.
* No duplicate business logic.
* Clean, modular, maintainable, enterprise-quality code.
