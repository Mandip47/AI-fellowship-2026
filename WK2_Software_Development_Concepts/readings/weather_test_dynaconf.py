from config import settings

print("--- Dynaconf Test ---")
# Using .get() prevents the app from crashing if the key is missing
print(f"App Name: {settings.get('name', 'Unknown')}")
print(f"Offset: {settings.get('offset', 'No offset found')}")

print(f"Your API Key is: {settings.api_key}")
