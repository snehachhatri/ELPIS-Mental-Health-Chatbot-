# Elpis 🌿 — AI Wellness Companion

Elpis is an AI-powered mental health and wellness chatbot built with Flask. It offers emotional support, motivation, and stress-relief conversations, and lets users book a real therapy session directly through the app — with the first session free.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0-black)

---

## ✨ Features

- **Conversational support** — chats with the user, detects emotional state (stress, anxiety, sadness, frustration, loneliness, etc.) and responds with empathy and practical suggestions.
- **Crisis-safety handling** — flags self-harm/suicide-related language and responds with care and helpline information instead of generic advice.
- **Modern desktop-style UI** — full-screen chat layout (sidebar + chat area), similar to ChatGPT/Claude, instead of a small widget.
- **Book a Session** — an in-app form lets users request a 1:1 therapy session. Submissions are emailed directly to the admin inbox.
- **First session free** — pricing for sessions beyond the first is communicated by email based on the topic chosen.

---

## 🛠️ Tech Stack

| Layer       | Technology              |
|-------------|--------------------------|
| Backend     | Python, Flask            |
| Frontend    | HTML, CSS, vanilla JS    |
| Email       | smtplib (Gmail SMTP)     |
| Deployment  | Render / Railway (Gunicorn) |

---

## 📂 Project Structure

```
ELPIS-Mental-Health-Chatbot/
├── app.py                  # Flask backend — chat logic, emotion detection, booking emails
├── requirements.txt        # Python dependencies
├── Procfile                 # Start command for deployment
├── .env.example              # Template for required environment variables
├── .gitignore                # Keeps .env and other local files out of version control
├── static/
│   └── elpis-logo.png        # App logo
└── templates/
    └── index.html            # Chat UI (sidebar + chat window + booking modal)
```

---

## 🚀 Getting Started Locally

### 1. Clone the repository
```bash
git clone https://github.com/snehachhatri/ELPIS-Mental-Health-Chatbot-.git
cd ELPIS-Mental-Health-Chatbot-
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Copy `.env.example` to `.env` and fill in your real values:
```
SENDER_EMAIL=your-email@gmail.com
SENDER_APP_PASSWORD=your-16-character-gmail-app-password
RECEIVER_EMAIL=your-email@gmail.com
```
> Use a [Gmail App Password](https://myaccount.google.com/apppasswords), not your normal Gmail password. Never commit `.env` to GitHub.

### 4. Run the app
```bash
python app.py
```
Open **http://127.0.0.1:5000/** in your browser.

---

## ☁️ Deployment

This project is ready to deploy on **Render** or **Railway**:

1. Push this repo to GitHub.
2. Create a new Web Service on Render/Railway and connect the GitHub repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add the environment variables (`SENDER_EMAIL`, `SENDER_APP_PASSWORD`, `RECEIVER_EMAIL`) in the platform's dashboard.
6. Deploy — you'll get a live public URL.

---

## ⚠️ Disclaimer

Elpis is **not a licensed therapist or medical professional** and cannot diagnose or treat mental health conditions. It is designed to provide everyday emotional support and to connect users with real, qualified therapists for ongoing care. If you or someone you know is in crisis, please contact a local emergency service or a crisis helpline immediately.

---

## 📄 License

This project is open for personal and educational use. Feel free to fork and build on it.
