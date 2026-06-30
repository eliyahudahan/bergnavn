# BergNavn – Maritime AIS & Weather Analysis (Legacy Learning Project)

**This project was my first attempt at building a maritime data system.**
It connects to Norwegian AIS data and weather APIs for route visualization.

> ⚠️ This is a **legacy learning project (2025)** and not actively maintained.
> 
> **For current production projects, see:**
> - [EnumKraft](https://github.com/eliyahudahan/enumkraft) – Grid Stability
> - [Anomalitor](https://github.com/eliyahudahan/anomalitor) – Predictive Maintenance  
> - [Deviative](https://github.com/eliyahudahan/deviative) – Maritime Anomaly Detection

---

## 🔧 Setup

```bash
git clone <repo>
cd bergnavn
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run

📁 Structure
text
backend/
├── app.py
├── config/
├── controllers/
├── middleware/
├── models/
├── routes/
├── services/
└── tests/

frontend/          # React (partial)
database/          # Schema
📡 Data Sources
AIS: Norwegian Coastal Administration (Kystverket)

Weather: MET Norway

📄 License
MIT