## 🇬🇧 English version:

```markdown
# BergNavn

BergNavn is a project tailored for travelers, couples, and families.  
It offers personalized cruise planning with a focus on safety and precise timing.

---

## Quickstart

> 🛠️ It is recommended to run this project in a Linux environment or using WSL on Windows.  
> However, it can also run on Windows as long as Python and pip are properly installed.

1. Clone the repository:
```bash
git clone https://github.com/your-username/bergnavn.git
cd bergnavn
2. Create a virtual environment:
python3 -m venv venv
source venv/bin/activate  # Linux / WSL
venv\Scripts\activate     # Windows without WSL
3. Install dependencies:
pip install -r requirements.txt
4. Run the server:
flask run
Note: You should now see the server running at: http://127.0.0.1:5000/

Project Structure
The project directory is organized as follows:

bergnavn/
│
├── backend/                   # Server-side code
│   ├── models/                # Database models
│   │   ├── user.py            # User model
│   │   └── cruise.py          # Cruise model
│   │
│   ├── routes/                # API files (Blueprints)
│   │   ├── user_routes.py     # User routes
│   │   └── cruise_routes.py   # Cruise routes
│   │
│   ├── controllers/           # Business logic (processes data between Routes and Models)
│   │   ├── user_controller.py
│   │   └── cruise_controller.py
│   │
│   ├── services/              # External services (if any, e.g. email service or external APIs)
│   │
│   ├── middleware/            # Security and authorization layer
│   │
│   ├── config/                # Configuration files (DB, API keys, secrets)
│   │   └── config.py          # Environment settings (from .env file)
│   │
│   ├── tests/                 # Unit tests
│   │   ├── test_user.py       # User module tests
│   │   └── test_cruise.py     # Cruise module tests
│   │
│   ├── app.py                 # Main server file
│   ├── .env                   # Environment file with secret variables (not tracked by git)
│   └── requirements.txt       # Dependency file for Flask (to set up the virtual environment)
│
├── frontend/                  # Client-side code (if applicable, this is where UI files would go)
│
├── database/                  # Database setup (if you have an initial schema import file)
│
├── .gitignore                 # Git ignore file (specifies files not to be tracked by git)
│
├── readme.md                  # Project documentation (what the system does, how to run it, API documentation, etc.)
│
└── config.py                  # Configuration file (if not placed inside backend/config)

## 🧰 Technologies

The project uses the following technologies and libraries:

🔹 **Flask** - A Python framework for building lightweight and fast web applications.  
🔹 **Flask-SQLAlchemy** - A module that allows easy integration with databases using ORM (Object-Relational Mapping).  
🔹 **Flask-Login** - For managing user authentication and sessions.  
🔹 **PostgreSQL** - A high-performance relational database.  
🔹 **Python** - The main programming language used for the project.  
🔹 **Jinja2** - A templating engine that helps separate logic from the user interface code in Flask.  
🔹 **SQLAlchemy** - A Python ORM library for working with relational databases.  
🔹 **pytest** - A framework for running automated unit tests.  
🔹 **dotenv** - To manage environment variables securely and conveniently.

## 📂 Project Structure

The project is organized in a modular way, with a clear folder structure to ease development and maintenance:

🔹 **backend/** - Contains all server-side code. This includes models, API routes, logic, and status management.  
🔹 **frontend/** - If applicable, this folder would contain all client-side code (e.g., React, Vue). Currently, this folder might be empty in this project.  
🔹 **database/** - Contains database-related files (schemas, setup scripts).  
🔹 **.gitignore** - Specifies which files and folders should be excluded from version control (e.g., environment files, virtual environments).  
🔹 **readme.md** - Provides comprehensive documentation for the project, setup instructions, and API details.  
🔹 **config.py** - Global configuration settings (e.g., API keys, environment configurations).

## 🗺️ Future Vision

Some future goals for the project include:

🔹 **User Interface Enhancement** - Develop a more advanced client-side application with dynamic and modular UI components.  
🔹 **Integration with External APIs** - Add third-party services (e.g., real-time weather data).  
🔹 **Performance Optimization** - Implement advanced data management techniques, like caching, to improve performance.  
🔹 **Support for Different Navigation Systems** - Add features such as real-time navigation and map integrations for users.

## 👤 Project Creator

This project was created by:  
🔹 **Eli**  
🔹 [GitHub Profile](https://github.com/eliyahudahan)  
🔹 Email: framgangsrik747@gmail.com

