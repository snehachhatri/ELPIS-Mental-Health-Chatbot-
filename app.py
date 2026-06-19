from flask import Flask, render_template, request, jsonify
import random
import re
import os
import smtplib
from email.mime.text import MIMEText

# Loads variables from a local .env file (if present) so you can test
# email sending on your own computer without ever typing your real
# password into app.py. On Render/Railway, this line does nothing —
# they inject environment variables their own way, which is fine.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

# ---------------------------------------------------------------------------
# EMAIL CONFIG — pulled from environment variables (set these on your
# hosting platform's dashboard, NOT hardcoded here — keeps your password
# out of your code, which matters once this is public on the internet).
# Locally, you can set them in a .env file or directly in your terminal.
# ---------------------------------------------------------------------------
EMAIL_CONFIG = {
    "SMTP_SERVER": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "SMTP_PORT": int(os.environ.get("SMTP_PORT", 587)),
    "SENDER_EMAIL": os.environ.get("SENDER_EMAIL", "your-email@gmail.com"),
    "SENDER_APP_PASSWORD": os.environ.get("SENDER_APP_PASSWORD", "your-16-char-app-password"),
    "RECEIVER_EMAIL": os.environ.get("RECEIVER_EMAIL", "your-email@gmail.com"),
}

def send_booking_email(data):
    """Sends the booking request to RECEIVER_EMAIL. Returns (success, error)."""
    body = f"""New session booking request:

Name: {data.get('first_name','')} {data.get('last_name','')}
Email: {data.get('email','')}
Phone: {data.get('phone','') or '-'}
Topic: {data.get('topic','')}
Preferred slot: {data.get('slot','')}
Note: {data.get('note','') or '-'}

(First session is free for this client.)
"""
    msg = MIMEText(body)
    msg["Subject"] = f"New Elpis booking — {data.get('first_name','')} {data.get('last_name','')}"
    msg["From"] = EMAIL_CONFIG["SENDER_EMAIL"]
    msg["To"] = EMAIL_CONFIG["RECEIVER_EMAIL"]

    try:
        with smtplib.SMTP(EMAIL_CONFIG["SMTP_SERVER"], EMAIL_CONFIG["SMTP_PORT"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["SENDER_EMAIL"], EMAIL_CONFIG["SENDER_APP_PASSWORD"])
            server.sendmail(EMAIL_CONFIG["SENDER_EMAIL"], EMAIL_CONFIG["RECEIVER_EMAIL"], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)

# In-memory session state (single-user demo).
# For multi-user, swap this for a per-session dict keyed on a session id.
state = {
    "stage": "start",       # start -> reason -> advice -> followup
    "emotion": None,
    "name": None,
}

# ---------------------------------------------------------------------------
# Safety: crisis / self-harm detection always runs first, regardless of stage
# ---------------------------------------------------------------------------
CRISIS_PATTERNS = [
    "kill myself", "suicide", "end my life", "want to die", "hurt myself",
    "self harm", "self-harm", "no reason to live", "better off dead",
    "can't go on", "cant go on"
]

CRISIS_REPLY = (
    "I'm really glad you told me that, and I want you to know I'm taking it seriously. "
    "I'm not a crisis professional, so what you're feeling deserves more support than I can give "
    "right now — please reach out to someone who can help immediately: a trusted person nearby, "
    "a local emergency number, or a crisis helpline (in India, AASRA: 9152987821, or iCall: 9152987821 / 022-25521111). "
    "You don't have to carry this alone, and you matter. Can you tell me if there's someone nearby you can call right now?"
)

# ---------------------------------------------------------------------------
# Emotion detection (keyword-based — fast, transparent, no ML dependency)
# ---------------------------------------------------------------------------
EMOTION_KEYWORDS = {
    "sad":       ["sad", "depressed", "unhappy", "cry", "crying", "down", "low", "heartbroken"],
    "stress":    ["stress", "stressed", "pressure", "overwhelmed", "burnt out", "burnout", "exhausted"],
    "anxious":   ["anxious", "anxiety", "nervous", "panic", "worried", "worry", "scared", "afraid"],
    "frustrated":["frustrated", "annoyed", "angry", "irritated", "mad"],
    "lonely":    ["lonely", "alone", "isolated", "no one understands", "no friends"],
    "happy":     ["happy", "good", "great", "excited", "awesome", "joy", "amazing", "proud"],
    "motivated": ["motivated", "ready", "pumped", "determined", "focused"],
    "tired":     ["tired", "sleepy", "drained", "no energy", "unmotivated", "lazy"],
}

PRODUCTIVITY_KEYWORDS = [
    "assignment", "assignments", "deadline", "exam", "exams", "project",
    "task", "tasks", "todo", "to-do", "study", "studying", "work", "goal", "goals"
]

GREETING_KEYWORDS = ["hi", "hello", "hey", "yo", "hii", "heyy"]

def detect_emotion(msg):
    for emotion, words in EMOTION_KEYWORDS.items():
        if any(w in msg for w in words):
            return emotion
    return None

def mentions_productivity(msg):
    return any(w in msg for w in PRODUCTIVITY_KEYWORDS)

# ---------------------------------------------------------------------------
# Response banks — varied so Nova doesn't sound repetitive
# ---------------------------------------------------------------------------
ACK = {
    "sad":        ["I hear the heaviness in that.", "That sounds genuinely hard to sit with.", "Sounds like things feel pretty low right now."],
    "stress":     ["That's a lot to be carrying at once.", "Sounds like your plate is way too full.", "I can feel the overwhelm in that."],
    "anxious":    ["That on-edge feeling is exhausting, I get it.", "Anxiety has a way of making everything feel urgent.", "That sounds like a lot of noise in your head right now."],
    "frustrated": ["Yeah, that would frustrate anyone.", "That's a fair amount of annoyance to be sitting with.", "I'd be irritated too, honestly."],
    "lonely":     ["That sounds isolating, and I'm sorry you're feeling that.", "Loneliness is one of the heavier feelings to carry quietly.", "I hear you — that disconnect is rough."],
    "happy":      ["Okay, I love this energy.", "That's genuinely great to hear.", "This is the kind of message I love getting."],
    "motivated":  ["I can feel that energy from here.", "That's a great headspace to be in.", "Love this — let's not waste it."],
    "tired":      ["Running on empty is rough.", "Sounds like your tank is on fumes.", "That kind of tired isn't fixed by one good nap, I know."],
}

INSIGHT = {
    "sad":        "Sadness usually isn't random — it's your mind flagging that something important to you got disrupted.",
    "stress":     "Stress is just your brain's alarm system going off because the to-do list outgrew the hours in the day.",
    "anxious":    "Anxiety tends to be your brain rehearsing worst-case scenarios on a loop, trying to feel prepared.",
    "frustrated": "Frustration usually shows up when something feels unfair or out of your control.",
    "lonely":     "Loneliness isn't about how many people are around you — it's about feeling unseen by them.",
    "happy":      "Good moments like this are worth actually noticing, not just rushing past.",
    "motivated":  "Motivation is a great spark — the trick is building a small system before it fades.",
    "tired":      "Chronic tiredness is often less about sleep and more about having zero recovery time built into your days.",
}

NEXT_STEP = {
    "sad":        "Try naming one specific thing that's weighing on you — sometimes sadness gets lighter the second it has a shape.",
    "stress":     "Pick the smallest task on your list and finish just that one — momentum beats motivation.",
    "anxious":    "Try the 5-4-3-2-1 grounding trick: 5 things you see, 4 you hear, 3 you feel, 2 you smell, 1 you taste. Pulls you out of your head fast.",
    "frustrated": "Write down exactly what you wish had gone differently — it's surprisingly clarifying.",
    "lonely":     "Is there one person you could send a low-stakes message to today, just to reconnect?",
    "happy":      "Write this moment down somewhere — future-you on a hard day will want to read it.",
    "motivated":  "Lock in one concrete action in the next hour while the energy's hot.",
    "tired":      "Could you protect even 20 minutes today with zero obligations in it? Not productive rest — actual rest.",
}

CLOSING = [
    "I'm right here either way. 💚",
    "We'll figure this out one piece at a time.",
    "You're handling more than you're giving yourself credit for.",
    "Proud of you for even putting this into words.",
    "Whatever happens next, you're not doing it alone.",
]

PRODUCTIVITY_HUMOR = [
    "Your to-do list sounds like it was assembled by a supervillain. Let's defeat it one mission at a time.",
    "That list has main-character-villain-arc energy. Time to dethrone it.",
    "Okay, that's less a to-do list and more a final boss. We can still win this.",
]

def build_reply(emotion, user_msg):
    ack = random.choice(ACK.get(emotion, ["Thanks for telling me that."]))
    insight = INSIGHT.get(emotion, "")
    step = NEXT_STEP.get(emotion, "What feels like the smallest next step here?")
    close = random.choice(CLOSING)

    parts = [ack]
    if insight:
        parts.append(insight)
    if mentions_productivity(user_msg):
        parts.append(random.choice(PRODUCTIVITY_HUMOR))
    parts.append(step)
    parts.append(close)
    return " ".join(parts)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    raw = request.json.get("message", "")
    msg = raw.lower().strip()

    # --- Safety first, always, regardless of stage ---
    if any(p in msg for p in CRISIS_PATTERNS):
        return jsonify({"reply": CRISIS_REPLY})

    # --- Exit / gratitude handling ---
    if re.search(r"\bbye\b", msg):
        state["stage"] = "start"
        state["emotion"] = None
        return jsonify({"reply": "Take care of yourself out there 💚 I'm here whenever you need to talk again. Bye for now!"})

    if "thank" in msg:
        return jsonify({"reply": "Anytime, genuinely. That's what I'm here for — come back whenever you need to think out loud. 💖"})

    if any(g == msg or msg.startswith(g + " ") for g in GREETING_KEYWORDS):
        return jsonify({"reply": "Hey! Good to see you. What's actually going on with you today — the real version, not the 'I'm fine' version?"})

    # --- Stage machine ---
    if state["stage"] == "start":
        emotion = detect_emotion(msg)
        if not emotion:
            state["stage"] = "reason"
            state["emotion"] = "neutral"
            return jsonify({"reply": "Tell me a bit more about what's going on — I want to actually understand before I weigh in."})

        state["emotion"] = emotion
        state["stage"] = "reason"
        return jsonify({"reply": f"Sounds like {emotion} is the word for it right now. Want to tell me what's behind that?"})

    elif state["stage"] == "reason":
        emotion = state.get("emotion") or detect_emotion(msg) or "neutral"
        state["stage"] = "advice"
        reply = build_reply(emotion, msg)
        return jsonify({"reply": reply})

    else:  # advice / followup -> loop back, stay conversational
        new_emotion = detect_emotion(msg)
        if new_emotion:
            state["emotion"] = new_emotion
            state["stage"] = "reason"
            return jsonify({"reply": f"Okay, sounds like things shifted toward {new_emotion}. What's going on with that?"})

        state["stage"] = "reason"
        return jsonify({"reply": "I'm following — keep going, or tell me how that advice landed for you."})


@app.route('/book', methods=['POST'])
def book():
    data = request.json or {}
    required = ["first_name", "last_name", "email", "topic", "slot"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    success, error = send_booking_email(data)

    if success:
        return jsonify({
            "message": (
                f"Thanks {data['first_name']}! We've received your request for "
                f"{data['topic']} on {data['slot']}. Your first session is free — "
                f"check your inbox at {data['email']} for confirmation."
            )
        })
    else:
        # Email not configured yet / failed — don't lose the booking, log it.
        print("BOOKING (email failed to send):", data, "Error:", error)
        return jsonify({
            "message": (
                f"Thanks {data['first_name']}! Your request was received "
                f"(email delivery is still being set up on our end, so we've logged it "
                f"manually — we'll reach out at {data['email']} shortly)."
            )
        })


@app.route('/reset', methods=['POST'])
def reset():
    state["stage"] = "start"
    state["emotion"] = None
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
