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
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    salt = os.getenv("ADMIN_SALT", "").strip()
    
    # 送られてきたパスワードの前後から空白・改行（\n や \r）を除去する
    clean_password = input_password.strip()
    clean_salt = salt.strip()
    
    print(f"DEBUG - stored_hash: '{stored_hash}'")
    print(f"DEBUG - clean_salt: '{clean_salt}'")
    print(f"DEBUG - clean_password: '{clean_password}'")
    
    if not stored_hash:
        print("DEBUG - stored_hash が空です！環境変数が読み込めていません。")
        return False
    
    # 除去後のパスワードでハッシュ化
    hashed_input = hashlib.sha256((clean_password + clean_salt).encode("utf-8")).hexdigest()
    print(f"DEBUG - hashed_input: '{hashed_input}'")
    
    return hashed_input == stored_hash

@app.post("/api/login")
def login(req: LoginRequest):
    if check_password(req.password):
        return {"success": True, "message": "ログイン成功"}
    else:
        return {"success": False, "message": "パスワードが正しくありません"}