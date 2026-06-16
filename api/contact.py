from http.server import BaseHTTPRequestHandler
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

MAX_MESSAGE_LEN = 4000
ALLOWED_TYPES = {
    "feature": "Request a Feature",
    "feedback": "Share Feedback",
    "bug": "Report a Bug or Issue",
}


def _json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _post_json(url, payload, headers=None, timeout=12):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", "replace")


def _notify_telegram(record):
    token = os.environ.get("CONTACT_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("CONTACT_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    text = (
        "📬 5dailywords contact submission\n"
        f"Type: {record['type_label']}\n"
        f"Name: {record['first_name']} {record['last_name']}\n"
        f"Email: {record['email']}\n"
        f"Subject: {record['subject']}\n"
        f"Page: {record.get('page') or 'not provided'}\n\n"
        f"{record['message']}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    _post_json(url, {"chat_id": chat_id, "text": text[:3900]})
    return True


def _store_airtable(record):
    api_key = os.environ.get("CONTACT_AIRTABLE_API_KEY")
    base_id = os.environ.get("CONTACT_AIRTABLE_BASE_ID")
    table = os.environ.get("CONTACT_AIRTABLE_TABLE", "Contact Submissions")
    if not api_key or not base_id:
        return False
    table_path = urllib.parse.quote(table, safe="")
    url = f"https://api.airtable.com/v0/{base_id}/{table_path}"
    fields = {
        "Submitted At": record["submitted_at"],
        "Type": record["type_label"],
        "First Name": record["first_name"],
        "Last Name": record["last_name"],
        "Email": record["email"],
        "Subject": record["subject"],
        "Message": record["message"],
        "Page": record.get("page", ""),
        "User Agent": record.get("user_agent", ""),
    }
    _post_json(url, {"fields": fields}, headers={"Authorization": f"Bearer {api_key}"})
    return True


def _validate(data):
    contact_type = str(data.get("type", "")).strip().lower()
    first_name = str(data.get("first_name", "")).strip()
    last_name = str(data.get("last_name", "")).strip()
    email = str(data.get("email", "")).strip()
    subject = str(data.get("subject", "")).strip()
    message = str(data.get("message", "")).strip()
    page = str(data.get("page", "")).strip()[:500]
    if contact_type not in ALLOWED_TYPES:
        raise ValueError("Please choose a contact type.")
    if not first_name:
        raise ValueError("Please enter your first name.")
    if not last_name:
        raise ValueError("Please enter your last name.")
    if not email:
        raise ValueError("Please enter your email address.")
    if not subject:
        raise ValueError("Please enter a subject.")
    if not message:
        raise ValueError("Please enter a message.")
    if len(subject) > 160:
        raise ValueError("Subject is too long.")
    if len(message) > MAX_MESSAGE_LEN:
        raise ValueError("Message is too long.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Please enter a valid email address.")
    return {
        "type": contact_type,
        "type_label": ALLOWED_TYPES[contact_type],
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "subject": subject,
        "message": message,
        "page": page,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 12000:
                return _json(self, 413, {"error": "Submission is too large."})
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw or "{}")
            record = _validate(data)
            record["user_agent"] = self.headers.get("User-Agent", "")[:300]

            stored = _store_airtable(record)
            notified = _notify_telegram(record)

            if not stored and not notified:
                # Do not silently accept submissions before at least one delivery target is configured.
                return _json(self, 503, {"error": "Contact form delivery is not configured yet."})
            return _json(self, 200, {"ok": True, "stored": stored, "notified": notified})
        except ValueError as exc:
            return _json(self, 400, {"error": str(exc)})
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            return _json(self, 502, {"error": f"Contact service error: {detail}"})
        except Exception:
            return _json(self, 500, {"error": "Contact form error."})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
