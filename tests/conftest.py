import os
from pathlib import Path


TEST_DB = Path(__file__).resolve().parent.parent / "test_testpilot.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["TESTPILOT_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ.pop("OPENAI_API_KEY", None)
