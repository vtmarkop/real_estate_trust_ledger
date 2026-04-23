import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@db:5432/mydb")
    SECRET_KEY: str = "ena_para_poly_megalo_mystiko_kleidi_gia_tin_paragogi_123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 1 εβδομάδα

settings = Settings()