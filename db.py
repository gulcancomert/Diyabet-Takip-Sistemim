import os
import mysql.connector

class DB:
    """
    Basit bağlan–sorgula katmanı.
    with DB() as db: db.query(...)

    Ortam değişkeni varsa MYSQL_PW alınır,
    yoksa sabit yedek kullanılır.
    """

    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=os.getenv("MYSQL_PW") or "gulsuf201",
            database="diyabet_takip",
            charset="utf8mb4"
        )
        self.cur = self.conn.cursor(dictionary=True)

    # context-manager
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): self.close()

    def query(self, sql: str, params=(), fetch=True):
        """fetch=True → list[dict] döner, fetch=False → commit-only."""
        try:
            self.cur.execute(sql, params)
            data = self.cur.fetchall() if fetch else None
            self.conn.commit()
            return data
        except mysql.connector.Error:
            self.conn.rollback()
            raise

    def close(self):
        self.cur.close()
        self.conn.close()
