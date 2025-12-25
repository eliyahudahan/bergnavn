from app import app

print("🩺 Creating simple health endpoint test")

# הוסף endpoint זמני לבדיקה
@app.route('/test-health')
def test_health():
    return {"status": "ok", "timestamp": "2025-12-25T19:00:00Z", "message": "Test health endpoint works"}

# הרץ בדיקה
with app.test_client() as client:
    print("\n🧪 Testing /test-health...")
    response = client.get('/test-health')
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Data: {response.get_json()}")
        print("✅ Simple health endpoint works!")
    else:
        print(f"Error: {response.data[:200]}...")

print("\n" + "=" * 50)
