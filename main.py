from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Renovaciones IA API",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "Success"}
