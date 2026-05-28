from fastapi import FastAPI
from app.api.endpoints import router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicio - conectar a BD
    from app.services.database import db
    await db.connect()
    print("✅ API iniciada correctamente")
    yield
    # Cierre
    await db.close()
    print("👋 API finalizada")

app = FastAPI(title="Logyca Sales Processor", lifespan=lifespan)
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Logyca Sales Processor API", "status": "running"}