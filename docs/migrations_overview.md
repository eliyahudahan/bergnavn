**📘 `docs/migrations_overview.md` – Database & Migrations Flow**

### 🧠 Concept Summary

This project uses **Flask** + **SQLAlchemy** + **Alembic** for handling database migrations. Below is a high-level explanation of how the system works.

---

### 🔁 Flow Overview

```plaintext
[Flask App] 
     │
     ▼
[Loads Models with SQLAlchemy]
     │
     ▼
[Run: alembic revision --autogenerate]
     │
     ▼
[Alembic compares Models ↔ Database Schema]
     │
     ▼
[Migration script is created]
     │
     ▼
[Run: alembic upgrade head]
     │
     ▼
[Database schema is updated]
```

---

### 🧩 Components

* **Flask App**: Initializes the application and creates the app context.
* **SQLAlchemy**: Defines models (tables) in Python.
* **Alembic**: Generates migration scripts and applies schema changes.
* **Migrations Folder**: Contains versioned scripts under `migrations/versions`.

---

### 📦 Commands Cheat Sheet

```bash
# Create a new migration script based on model changes
alembic revision --autogenerate -m "message"

# Apply the latest migration(s) to the database
alembic upgrade head

# Rollback the last migration
alembic downgrade -1
```

---

### 🧪 Example Path: How It Works Together

1. You **edit a model** in `backend/models/`.
2. Run `alembic revision --autogenerate`.
3. Alembic checks the **difference** between models and the current database.
4. A new script is created in `migrations/versions/`.
5. Run `alembic upgrade head` to apply it.

