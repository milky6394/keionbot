from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    password: str

def check_password(input_password: str) -> bool:
    # Renderの環境変数（Environment Variables）から値を取得
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    salt = os.getenv("ADMIN_SALT", "")
    
    if not stored_hash:
        return False
    
    # 入力されたパスワード + salt を SHA-256 でハッシュ化
    hashed_input = hashlib.sha256((input_password + salt).encode("utf-8")).hexdigest()
    
    return hashed_input == stored_hash

@app.post("/api/login")
def login(req: LoginRequest):
    if check_password(req.password):
        return {"success": True, "message": "ログイン成功"}
    else:
        return {"success": False, "message": "パスワードが正しくありません"}