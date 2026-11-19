import os
import tempfile

# app.db читає DATABASE_URL під час імпорту, тому змінні виставляємо до будь-якого імпорту застосунку.
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(tempfile.mkdtemp(), 'test.db')}")
os.environ.setdefault("CACHE_ENABLED", "false")
