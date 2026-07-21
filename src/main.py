from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TCC IA Engine funcionando!"}

@app.get("/health")
def health():
    return {"status": "ok"}
