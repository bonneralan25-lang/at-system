import httpx
import sys
sys.path.insert(0, ".")
from config import get_settings

settings = get_settings()
headers = {
    "Authorization": f"Bearer {settings.ghl_api_key}",
    "Version": "2021-07-28",
}

# Step 1: search conversations by contactId
contact_id = "rSM79lQNDkiVff9gzunT"
r = httpx.get(
    "https://services.leadconnectorhq.com/conversations/search",
    headers=headers,
    params={"contactId": contact_id},
    timeout=15,
)
print("Search status:", r.status_code)
data = r.json()
convs = data.get("conversations", [])
print("Conversations found:", len(convs))

if not convs:
    print("RAW response:", r.text[:500])
    sys.exit(0)

conv_id = convs[0]["id"]
print("Conv ID:", conv_id)

# Step 2: fetch messages
r2 = httpx.get(
    f"https://services.leadconnectorhq.com/conversations/{conv_id}/messages",
    headers=headers,
    timeout=15,
)
print("Messages status:", r2.status_code)
msgs_data = r2.json()
messages = msgs_data.get("messages", {})
if isinstance(messages, dict):
    messages = messages.get("messages", [])
print("Messages found:", len(messages))
if messages:
    print("First msg:", messages[0])
else:
    print("RAW messages response:", r2.text[:500])
