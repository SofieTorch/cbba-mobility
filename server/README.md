## Getting started

1. Start the services:

```bash
cd /server
docker compose up -d
```

2. Run migrations:

```bash
docker compose exec bash
uv run alembic upgrade head
```

3. API is available at (http://localhost:8000)[http://localhost:8000]

## Creating migrations

To create a new migration with Alembic:

1. Auto-generate from model changes:

```bash
docker compose exec server alembic revision --autogenerate -m "add stops table"
```

2. The migration file will be created in `alembic/versions`. Then apply it with:

```bash
docker compose exec server alembic upgrade head
```

Other useful commands:

```bash
# Check current migration status
docker compose exec server alembic current

# See migration history
docker compose exec server alembic history

# Rollback one migration
docker compose exec server alembic downgrade -1

# Rollback to specific revision
docker compose exec server alembic downgrade 001
```