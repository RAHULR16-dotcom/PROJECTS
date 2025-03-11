from flask import Flask, request, jsonify
import imaplib
import email
from email.header import decode_header
import requests

app = Flask(__name__)
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/v1/completions"

# Email credentials (Use environment variables for security in production)
EMAIL_USER = "your-email@example.com"
EMAIL_PASS = "your-email-password"
IMAP_SERVER = "imap.gmail.com"

# Function to fetch emails
def fetch_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    status, messages = mail.search(None, "ALL")
    email_list = []

    for num in messages[0].split()[-10:]:  # Fetch last 10 emails
        status, data = mail.fetch(num, "(RFC822)")
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                email_list.append({"subject": subject, "from": msg["From"]})

    mail.close()
    mail.logout()
    return email_list

# Function to query Groq API
def query_groq(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "mixtral-8x7b",
        "prompt": prompt,
        "max_tokens": 50
    }
    response = requests.post(GROQ_API_URL, json=data, headers=headers)
    return response.json().get("choices", [{}])[0].get("text", "No response")

# Function to categorize emails using Groq
def categorize_email(subject):
    prompt = f"Classify this email subject: '{subject}' into categories: Work, Personal, Promotions, Spam."
    return query_groq(prompt).strip()

# Function to generate a reply suggestion using Groq
def suggest_reply(subject):
    prompt = f"Suggest a professional email reply for: '{subject}'"
    return query_groq(prompt).strip()

@app.route("/fetch", methods=["GET"])
def fetch():
    emails = fetch_emails()
    return jsonify(emails)

@app.route("/categorize", methods=["POST"])
def categorize():
    data = request.json
    category = categorize_email(data["subject"])
    return jsonify({"category": category})

@app.route("/suggest-reply", methods=["POST"])
def suggest():
    data = request.json
    reply = suggest_reply(data["subject"])
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
