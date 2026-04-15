import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self): 
        self._init_db()

    def _get_conn(self):
        url = os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL is not set in your .env file")
        return psycopg2.connect(
            url,
            cursor_factory=psycopg2.extras.RealDictCursor
        )

    def _init_db(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS calculations (
                        id              SERIAL PRIMARY KEY,
                        expression      TEXT NOT NULL,
                        result          TEXT NOT NULL,
                        operation       TEXT NOT NULL,
                        source          TEXT NOT NULL DEFAULT 'web',
                        user_identifier TEXT NOT NULL DEFAULT 'anonymous',
                        created_at      TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """)

                # Safe migrations
                cur.execute("""
                    ALTER TABLE calculations
                    ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'web'
                """)
                cur.execute("""
                    ALTER TABLE calculations
                    ADD COLUMN IF NOT EXISTS user_identifier TEXT NOT NULL DEFAULT 'anonymous'
                """)

            conn.commit()
        finally:
            conn.close()

    def save_calculation(
        self,
        expression: str,
        result,
        operation: str,
        source: str = 'web',
        user_identifier: str = 'anonymous'
    ):
        if source not in ('web', 'telegram'):
            source = 'web'

        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO calculations
                    (expression, result, operation, source, user_identifier)
                    VALUES (%s, %s, %s, %s, %s)
                """, (expression, str(result), operation, source, user_identifier))

            conn.commit()
        finally:
            conn.close()

    def get_all(self, source: str = None) -> list[dict]:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                if source:
                    cur.execute("""
                        SELECT *
                        FROM calculations
                        WHERE source = %s
                        ORDER BY id DESC
                    """, (source,))
                else:
                    cur.execute("""
                        SELECT *
                        FROM calculations
                        ORDER BY id DESC
                    """)

                return cur.fetchall()
        finally:
            conn.close()

    def get_stats(self, source: str = None) -> dict:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                where = "WHERE source = %s" if source else ""
                params = (source,) if source else ()

                # Total
                cur.execute(f"""
                    SELECT COUNT(*) AS total
                    FROM calculations
                    {where}
                """, params)
                total = cur.fetchone()["total"]

                # By operation
                cur.execute(f"""
                    SELECT operation, COUNT(*) AS count
                    FROM calculations
                    {where}
                    GROUP BY operation
                    ORDER BY count DESC
                """, params)
                by_op = cur.fetchall()

                # By source
                cur.execute(f"""
                    SELECT source, COUNT(*) AS count
                    FROM calculations
                    {where}
                    GROUP BY source
                """, params)
                by_source = cur.fetchall()

                # ✅ FIXED numeric stats
                numeric_where = (
                    "WHERE source = %s AND " if source else "WHERE "
                ) + "result::TEXT ~ '^-?[0-9]+(\\.[0-9]+)?$'"

                cur.execute(f"""
                    SELECT
                        AVG(result::NUMERIC) AS avg,
                        MIN(result::NUMERIC) AS min,
                        MAX(result::NUMERIC) AS max
                    FROM calculations
                    {numeric_where}
                """, params)

                numeric = cur.fetchone()

            return {
                "total": total,
                "by_op": list(by_op),
                "by_source": list(by_source),
                "avg": float(numeric["avg"]) if numeric["avg"] is not None else None,
                "min": float(numeric["min"]) if numeric["min"] is not None else None,
                "max": float(numeric["max"]) if numeric["max"] is not None else None,
            }

        finally:
            conn.close()

    def delete_by_id(self, id: int):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM calculations WHERE id = %s", (id,))
            conn.commit()
        finally:
            conn.close()

    def clear_all(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM calculations")
            conn.commit()
        finally:
            conn.close()