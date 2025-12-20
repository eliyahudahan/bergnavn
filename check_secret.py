import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('/home/framg/dev/bergnavn') / '.env'
load_dotenv(dotenv_path=env_path)

secret = os.getenv('BARENTSWATCH_CLIENT_SECRET', '')

print(f"Secret length: {len(secret)}")
print(f"First 20 characters (hex): {' '.join(f'{ord(c):02x}' for c in secret[:20])}")
print(f"Contains quotes: {\"'\" in secret or '\"' in secret}")
print(f"Contains spaces: {' ' in secret}")
print(f"Contains newlines: {'\\n' in secret or '\\r' in secret}")
print(f"Secret ends with: '{secret[-5:] if len(secret) >= 5 else secret}'")

# Show as Python string literal
print(f"\nPython string representation: {repr(secret)}")
