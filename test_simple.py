#!/usr/bin/env python3
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "BergNavn Test"

@app.route('/maritime/simulation')
def simulation():
    return render_template('maritime_split/realtime_simulation.html')

if __name__ == '__main__':
    print("🚀 Starting test server on http://localhost:5000")
    print("📊 Go to: http://localhost:5000/maritime/simulation")
    app.run(debug=True, port=5000)
