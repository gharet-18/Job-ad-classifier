#Shared logic: rules, scoring, redaction, OCR.
import re
from pathlib import Path

import joblib

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = BASE_DIR / "scam_model.joblib"

# (label, points, regex)
RULES = [
    ("Upfront fee requested", 40,
     r"\b(registration|training|activation|processing|application|admin)\s+(fee|money)\b"
     r"|pay\s+(a\s+)?(fee|deposit)|send\s+(money|payment)"),
    ("Asks for ID/bank details early", 30,
     r"\b(bvn|nin|bank\s+details|account\s+number|atm\s+pin|otp|passport|id\s+card)\b"),
    ("WhatsApp/Telegram-only contact", 20,
     r"\b(whatsapp|telegram)\b"),
    ("Urgency / pressure", 15,
     r"limited\s+slots?|apply\s+now|act\s+fast|hurry|today\s+only|last\s+chance|pay\s+now"
     r"|(slots?|spots?)\s+(are\s+)?(filling|going)\s+(up\s+)?fast|filling\s+fast"),
    ("Unrealistic pay / easy work", 25,
     r"(earn|make|get)\s+[\$₦#]?\s?\d[\d,]*\s*(k|usd|dollars|naira)?\s*(/|per\s+)?(day|daily|hour|week)"
     r"|no\s+experience|easy\s+(money|task|work)|playing\s+games|(like|liking)\s+videos"
     r"|guaranteed\s+(income|results|job)|earn\s+before"),
    ("Pidgin / DM-bait phrases", 25,
     r"pay\s+small\s+money|e\s+go\s+pay\s+you|double\s+your\s+money"
     r"|inbox\s+me|dm\s+me|dm\s+to\s+join|click\s+(the\s+)?link\s+in\s+(my\s+)?bio"
     r"|dm\s+[\"“”']?\w+[\"“”']?\s+to\s+(join|start|begin)"
     r"|join\s+our\s+(whatsapp|telegram)\s+group|send\s+am\s+now"),
    ("Play-to-earn / game money claims", 30,
     r"(play|playing)\s+(games?|this\s+game).{0,40}(earn|win|get\s+paid|cash)"
     r"|(earn|win|make)\s+(real\s+)?(money|cash).{0,40}(playing|game)"
     r"|withdraw(al)?\s+(to\s+)?(your\s+)?(bank|account|opay|palmpay)|cash\s*out"
     r"|minimum\s+withdraw|invite\s+(your\s+)?friends?\s+to\s+earn"
     r"|watch\s+ads?\s+(to\s+)?earn|spin\s+(to\s+)?win"),
    ("Free email address", 15,
     r"[\w.]+@(gmail|yahoo|outlook|hotmail)\.com"),
]

SCAM_THRESHOLD = 60
SUSPICIOUS_THRESHOLD = 25

_model = None
_model_checked = False


def load_model():
    """Load the trained ML model once. Returns None if it hasn't been trained."""
    global _model, _model_checked
    if not _model_checked:
        _model_checked = True
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
    return _model


def analyze(text):
    """Rule-based scan. Returns (score 0-100, flags, spans)."""
    score, flags, spans = 0, [], []
    for label, points, pattern in RULES:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            score += points
            flags.append((label, points, [m.group(0) for m in matches]))
            spans += [(m.start(), m.end()) for m in matches]
    return min(score, 100), flags, spans


def combined_score(text, rule_score):
    """Blend rule score (60%) with ML score (40%). Falls back to rules only."""
    model = load_model()
    if model is None:
        return rule_score, None
    ml = model.predict_proba([text])[0][1] * 100
    return round(0.6 * rule_score + 0.4 * ml), round(ml)


def verdict(score):
    if score >= SCAM_THRESHOLD:
        return "scam"
    if score >= SUSPICIOUS_THRESHOLD:
        return "suspicious"
    return "ok"


def redact(text):
    """Remove emails and phone numbers before anything is saved."""
    text = re.sub(r"[\w.]+@[\w.]+\.\w+", "[EMAIL]", text)
    text = re.sub(r"\+?\d[\d\s-]{8,}\d", "[PHONE]", text)
    return text


def read_image_text(img):
    """OCR an image. Returns '' if Tesseract is missing or nothing is readable."""
    try:
        import pytesseract
        from PIL import ImageOps
        gray = ImageOps.grayscale(img.convert("RGB"))
        gray = gray.resize((gray.width * 2, gray.height * 2))
        return pytesseract.image_to_string(gray).strip()
    except Exception:
        return ""


def read_video_text(path, max_frames=20):
    """Sample frames from a video and OCR them. Returns unique lines of text."""
    try:
        import cv2
        from PIL import Image
    except Exception:
        return ""
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        return ""
    step = max(int(fps), total // max_frames)  # at most max_frames, at least 1 per second
    seen, lines = set(), []
    for i in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok:
            break
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        for line in read_image_text(img).splitlines():
            line = line.strip()
            if len(line) >= 4 and line.lower() not in seen:
                seen.add(line.lower())
                lines.append(line)
    cap.release()
    return "\n".join(lines)
