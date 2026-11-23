import os, sqlite3, secrets
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()
APP_PASSWORD=os.getenv("APP_PASSWORD","")
DB=Path(os.getenv("DB_PATH","nova.sqlite3"))
app=FastAPI(title="NOVA AI")

def db():
    conn=sqlite3.connect(DB)
    conn.row_factory=sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS chats (
      id TEXT PRIMARY PRIMARY KEY, title TEXT, created TEXT, updated TEXT
    )""".replace("PRIMARY PRIMARY","PRIMARY"))
    conn.execute("""CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT,
      created TEXT, FOREIGN KEY(chat_id) REFERENCES chats(id)
    )""")
    conn.commit()
    return conn

sessions=set()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return Path("static/index.html").read_text(encoding="utf-8")

@app.post("/api/login")
async def login(req: Request):
    data=await req.json()
    if not APP_PASSWORD:
        raise HTTPException(500,"APP_PASSWORD is not configured")
    if not secrets.compare_digest(str(data.get("password","")), APP_PASSWORD):
        raise HTTPException(401,"Incorrect password")
    token=secrets.token_urlsafe(32)
    sessions.add(token)
    resp=JSONResponse({"ok":True})
    resp.set_cookie("nova_session",token,httponly=True,samesite="lax",secure=os.getenv("COOKIE_SECURE","false").lower()=="true")
    return resp

@app.post("/api/logout")
def logout(req: Request):
    sessions.discard(req.cookies.get("nova_session",""))
    resp=JSONResponse({"ok":True})
    resp.delete_cookie("nova_session")
    return resp

def auth(req: Request):
    if req.cookies.get("nova_session","") not in sessions:
        raise HTTPException(401,"Please log in")

@app.get("/api/chats")
def chats(req: Request):
    auth(req)
    c=db()
    rows=c.execute("SELECT id,title,updated FROM chats ORDER BY updated DESC").fetchall()
    c.close()
    return [dict(x) for x in rows]

@app.post("/api/chats")
async def create_chat(req: Request):
    auth(req)
    data=await req.json()
    cid=secrets.token_hex(8)
    title=(data.get("title") or "New chat")[:100]
    now=datetime.utcnow().isoformat()
    c=db()
    c.execute("INSERT INTO chats VALUES (?,?,?,?)",(cid,title,now,now))
    c.commit(); c.close()
    return {"id":cid,"title":title}

@app.get("/api/chats/{cid}")
def get_chat(cid: str, req: Request):
    auth(req)
    c=db()
    rows=c.execute("SELECT role,content,created FROM messages WHERE chat_id=? ORDER BY id",(cid,)).fetchall()
    c.close()
    return [dict(x) for x in rows]

@app.post("/api/chat")
async def chat(req: Request):
    auth(req)
    data=await req.json()
    cid=data.get("chat_id")
    prompt=str(data.get("message","")).strip()
    model=str(data.get("model","auto"))[:80]
    if not cid or not prompt: raise HTTPException(400,"chat_id and message required")
    c=db()
    if not c.execute("SELECT id FROM chats WHERE id=?",(cid,)).fetchone():
        c.close(); raise HTTPException(404,"Chat not found")
    now=datetime.utcnow().isoformat()
    c.execute("INSERT INTO messages(chat_id,role,content,created) VALUES(?,?,?,?)",(cid,"user",prompt,now))
    history=c.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id",(cid,)).fetchall()
    c.execute("UPDATE chats SET title=?,updated=? WHERE id=?",(prompt[:42],now,cid))
    c.commit()
    try:
        from g4f.client import Client
        client=Client()
        result=client.chat.completions.create(
            model=model,
            messages=[{"role":r["role"],"content":r["content"]} for r in history],
        )
        answer=result.choices[0].message.content or "No response received."
    except Exception as e:
        answer=f"AI provider error: {type(e).__name__}: {str(e)[:300]}"
    c.execute("INSERT INTO messages(chat_id,role,content,created) VALUES(?,?,?,?)",(cid,"assistant",answer,datetime.utcnow().isoformat()))
    c.commit(); c.close()
    return {"answer":answer}

@app.get("/api/health")
def health():
    return {"status":"ok","app":"NOVA AI"}
