import sys
import logging
from app import app

# הפעל logging מפורט
logging.basicConfig(level=logging.DEBUG)

print("🚀 Running app with debug to see health endpoint error")
print("=" * 50)

# בדוק את ה-health endpoint עם debug
with app.test_client() as client:
    # Enable testing mode to see errors
    app.testing = True
    
    try:
        response = client.get('/health')
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 500:
            print("\n📝 Response data:")
            print(response.data.decode('utf-8')[:500])
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 50)
