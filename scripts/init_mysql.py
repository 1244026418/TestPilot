from pathlib import Path
import os
import sys

from dotenv import load_dotenv
import pymysql


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def main() -> None:
    host = os.getenv("TESTPILOT_MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("TESTPILOT_MYSQL_PORT", "3306"))
    user = os.getenv("TESTPILOT_MYSQL_USER", "root")
    password = os.getenv("TESTPILOT_MYSQL_PASSWORD", "")
    database = os.getenv("TESTPILOT_MYSQL_DATABASE", "testpilot")

    connection = pymysql.connect(host=host, port=port, user=user, password=password, charset="utf8mb4", autocommit=True)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        print(f"MySQL 数据库已就绪：{database}")
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"MySQL 初始化失败：{exc}")
        sys.exit(1)
