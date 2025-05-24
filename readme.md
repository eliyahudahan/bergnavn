````markdown
# 🇬🇧 English Version

```bash
git clone ...
````

# **BergNavn**

**BergNavn** is a project tailored for travelers, couples, and families.
It offers personalized cruise planning with a focus on safety and precise timing.

---

## 🚀 Quickstart

> 🛠️ Recommended: Run this project in a Linux environment or use WSL on Windows.
> It also works on Windows as long as Python and pip are properly installed.

1. Clone the repository:

   ```bash
   git clone ...
   cd bergnavn
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Linux / WSL
   venv\Scripts\activate       # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:

   ```bash
   flask run
   ```

   The server will run at: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 🧰 Technologies

The project uses the following libraries and tools:

* **Flask** – Lightweight Python framework for building web applications
* **Flask-SQLAlchemy** – ORM layer for database interaction
* **Flask-Login** – User authentication management
* **PostgreSQL** – Relational database
* **Python** – Main programming language
* **Jinja2** – Templating engine for separating logic and UI
* **SQLAlchemy** – Advanced ORM toolkit
* **pytest** – Unit testing framework
* **python-dotenv** – For managing environment variables securely

---

## 📁 Project Structure

The project is organized into modular folders for clarity and scalability:

```
bergnavn/
├── backend/                   # Server-side code
│   ├── models/                # Database models (user, cruise)
│   ├── routes/                # API endpoints using Flask Blueprints
│   ├── controllers/           # Business logic connecting routes and models
│   ├── services/              # External integrations (e.g., APIs, email)
│   ├── middleware/            # Security and authorization layers
│   ├── config/                # Configuration (env, secrets)
│   ├── tests/                 # Unit tests (pytest)
│   ├── app.py                 # Flask entry point
│   └── .env                   # Environment variables (not tracked by git)
│
├── frontend/                  # React-based UI (currently under development)
│   ⚠️ Note: May contain legacy `react-scripts` warnings; not critical for functionality
│
├── database/                  # DB schema setup (optional)
├── .gitignore                 # Excludes env files, logs, venvs, etc.
├── config.py                  # Global configuration (if not in backend/config)
└── readme.md                  # This documentation
```

---

## 🗺️ Vision & Roadmap

**BergNavn** aspires to become a trusted digital companion for modern travelers — combining safety, clarity, and elegance in cruise planning.

Future development goals include:

* **Smart User Interface** – Dynamic cruise planning UI with real-time feedback
* **API Integrations** – Real-time weather data, maps, and navigation services
* **Performance Optimization** – Caching and advanced query handling
* **Multi-language Support** – Especially for Nordic and Central European users
* **Mobile-ready Experience** – PWA support for seamless use on all devices

> *"This project started with a passion for the sea, and a desire to bring clarity to complex journeys. With every feature, we aim to make travel feel more human, more informed — and more beautiful."*

---

## ✅ Alembic Migration Test Instructions

To verify your Alembic configuration is working correctly:

1. **Make sure your app and Alembic are correctly linked:**

   * Check that `create_app()` is properly imported and used inside `env.py`
   * Ensure `get_engine_url()` is defined before it is called.

2. **Run a dry migration test:**

   ```bash
   alembic revision --autogenerate -m "Test migration after config change"
   ```

3. **Check the generated file:**

   * Look under the `migrations/versions/` folder for a `.py` file.
   * It should contain valid `op.create_table(...)` or similar migration code.

4. **If all looks good, apply the migration:**

   ```bash
   alembic upgrade head
   ```

> If you encounter issues such as `create_app not found` or `get_engine_url() not defined`, double-check import paths and function definitions inside your `migrations/env.py`.

---

## 👤 Project Creator

Created by:
**Eli**
[GitHub Profile](https://github.com/eliyahudahan)
Email: [framgangsrik747@gmail.com](mailto:framgangsrik747@gmail.com)

```
