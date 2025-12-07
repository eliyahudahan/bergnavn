# scripts/train_weather_lstm.py
# Train a simple LSTM model from MET weather time series.
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

DATA_PATH = "data/weather_history.csv"
MODEL_PATH = "models/weather_lstm.h5"

# Load data
df = pd.read_csv(DATA_PATH)
temps = df["temp"].values.astype(float)

# Prepare sequences
SEQ_LEN = 24
X, y = [], []

for i in range(len(temps) - SEQ_LEN):
    X.append(temps[i:i+SEQ_LEN])
    y.append(temps[i+SEQ_LEN])

X = np.array(X).reshape(-1, SEQ_LEN, 1)
y = np.array(y)

# Build model
model = Sequential([
    LSTM(32, return_sequences=False, input_shape=(SEQ_LEN, 1)),
    Dense(16, activation="relu"),
    Dense(1)
])

model.compile(optimizer="adam", loss="mse")

# Train model
model.fit(
    X,
    y,
    epochs=20,
    batch_size=16,
    validation_split=0.2,
    callbacks=[EarlyStopping(patience=3, restore_best_weights=True)],
    verbose=1
)

# Save model
model.save(MODEL_PATH)
print(f"✅ Saved model to {MODEL_PATH}")
