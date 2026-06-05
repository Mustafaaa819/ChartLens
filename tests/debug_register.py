import httpx

BASE = "http://localhost:8000"
r = httpx.post(f"{BASE}/auth/register", data={
    "email": "e2e_test@chartlens.test",
    "password": "e2etest123",
    "confirm_password": "e2etest123",
    "firm_name": "E2E Test Law Firm",
}, follow_redirects=False)

print(f"Status: {r.status_code}")
print(f"Location: {r.headers.get('location')}")
if r.status_code in (400, 422):
    # Look for error in HTML
    import re
    m = re.search(r'<span>(.*?)</span>', r.text)
    if m:
        print(f"Error: {m.group(1)}")
    else:
        print("Response snippet:", r.text[500:1000])
