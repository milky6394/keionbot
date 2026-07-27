from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# GitHub Pagesからのアクセスを許可（CORS設定）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 後でご自身のGitHub PagesのURLに絞ると安全です
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Render上のFastAPIが正常に動いています！"}

@app.get("/api/test")
def test_endpoint():
    return {"data": "ここにBotの処理結果などを載せて返します"}