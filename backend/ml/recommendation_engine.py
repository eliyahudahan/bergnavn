import pandas as pd
from sklearn.neighbors import NearestNeighbors
from backend.models.cruise import Cruise  # Import חשוב!

def recommend_cruises(user_preferences: dict, n_recommendations: int = 3):
    cruises = Cruise.query.all()
    cruise_data = [
        {
            "id": cruise.id,
            "origin": cruise.origin,
            "price": cruise.price,
            "duration_days": cruise.duration_days  # כאן משתמשים ב-property
        }
        for cruise in cruises
    ]
    df = pd.DataFrame(cruise_data)

    if df.empty:
        return []  # אין נתונים, מחזיר ריק

    origin_cat = df["origin"].astype("category")
    if user_preferences.get("origin") not in origin_cat.cat.categories:
        return Cruise.query.order_by(Cruise.price.asc()).limit(n_recommendations).all()

    df["origin_encoded"] = origin_cat.cat.codes
    X = df[["origin_encoded", "price", "duration_days"]]

    n_recommendations = min(n_recommendations, len(df))

    model = NearestNeighbors(n_neighbors=n_recommendations)
    model.fit(X)

    region_encoded = origin_cat.cat.categories.get_loc(user_preferences["origin"])
    user_input = [[region_encoded, user_preferences["price"], user_preferences["duration_days"]]]

    distances, indices = model.kneighbors(user_input)
    recommended_ids = df.iloc[indices[0]]["id"].tolist()

    return Cruise.query.filter(Cruise.id.in_(recommended_ids)).all()
