from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json, hashlib, secrets, time

app = FastAPI(title="OMEGA AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = Path("users.json")
TOKENS = {}

def load_users():
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return {}

def save_users(users):
    DB.write_text(json.dumps(users, indent=2), encoding="utf-8")

def hash_pw(password: str):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class AuthIn(BaseModel):
    email: str
    password: str

class ChatIn(BaseModel):
    message: str

@app.get("/")
def root():
    return {"app": "OMEGA AI Backend", "status": "online"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register")
def register(data: AuthIn):
    users = load_users()
    if data.email in users:
        raise HTTPException(400, "Benutzer existiert bereits")
    users[data.email] = {
        "password": hash_pw(data.password),
        "plan": "demo",
        "created_at": int(time.time())
    }
    save_users(users)
    return {"message": "Registrierung erfolgreich"}

@app.post("/auth/login")
def login(data: AuthIn):
    users = load_users()
    if data.email not in users or users[data.email]["password"] != hash_pw(data.password):
        raise HTTPException(401, "Falsche Zugangsdaten")
    token = secrets.token_urlsafe(32)
    TOKENS[token] = data.email
    return {"token": token, "email": data.email, "plan": users[data.email]["plan"]}

def current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Nicht eingeloggt")
    token = authorization.split(" ", 1)[1]
    email = TOKENS.get(token)
    if not email:
        raise HTTPException(401, "Token ungültig")
    return email

@app.post("/chat")
def chat(data: ChatIn, authorization: str | None = Header(default=None)):
    email = current_user(authorization)
    return {"reply": f"Hallo {email}, du hast geschrieben: {data.message}. Die echte KI-Anbindung kommt als nächster Schritt."}

@app.get("/me")
def me(authorization: str | None = Header(default=None)):
    email = current_user(authorization)
    users = load_users()
    return {"email": email, "plan": users[email].get("plan", "demo")}
