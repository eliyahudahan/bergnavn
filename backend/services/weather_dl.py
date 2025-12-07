# backend/services/weather_dl.py
# DL inference service for weather prediction
import os
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

MODEL_PATH = "models/weather_lstm.h5"
DATA_PATH = "data/weather_history.csv"

# Load the trained model
model = load_model(MODEL_PATH)

def predict_next_temperature():
    """Predict next hour temperature from MET history"""
    df = pd.read_csv(DATA_PATH)
    temps = df["temp"].values.astype(float)

    if len(temps) < 24:
        return None  # Not enough data

    seq = temps[-24:].reshape(1, 24, 1)
    pred = model.predict(seq)[0][0]

    return float(pred)
