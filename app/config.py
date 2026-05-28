from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Modo de ejecución
    mode: str = "dev"
    
    # Azure (solo para modo docker)
    azure_storage_connection_string: str = ""
    container_name: str = "sales-csv"
    queue_name: str = "sales-queue"
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "logyca_db"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    
    # App
    job_table_name: str = "jobs"
    
    # Directorio para archivos en modo dev
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"

settings = Settings()

# Crear directorio de uploads si no existe
if settings.mode == "dev" and not os.path.exists(settings.upload_dir):
    os.makedirs(settings.upload_dir)
    print(f"📁 Directorio creado: {settings.upload_dir}")