import os
from dotenv import load_dotenv

load_dotenv()


class Ustawienia:
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.mongodb_nazwa_bazy = os.getenv("MONGODB_DB_NAME", "job_agent_db")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "bardzo_tajny_klucz_zmien_mnie")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


ustawienia = Ustawienia()
