# backend/services/weather_dl.py
# DL inference service for weather prediction

import numpy as np
import pandas as pd
import os
from tensorflow.keras.models import load_model

MODEL_PATH = "models/weather_lstm.h5"
DATA_PATH = "data/weather_history.csv"

def predict_next_temperature():
    """Predict next-hour temperature from MET history (24-hour sequence)."""

    if not os.path.exists(MODEL_PATH):
        return None
    if not os.path.exists(DATA_PATH):
        return None

    model = load_model(MODEL_PATH)

    df = pd.read_csv(DATA_PATH)
    temps = df["temp"].values.astype(float)

    if len(temps) < 24:
        return None

    seq = temps[-24:].reshape(1, 24, 1)
    pred = model.predict(seq)[0][0]
    return float(pred)
