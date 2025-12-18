import requests

r = requests.get("711c17ebfc78418ff12236b61b76d91f", timeout=60)
print(r.status_code)
print(r.text[:500])  # just the first 500 chars to check
