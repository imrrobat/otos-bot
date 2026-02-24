import sqlite3
from datetime import datetime, timedelta

DB_NAME = "otos.db"


def migrate():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # -----------------------------
    # 1️⃣ اضافه کردن ستون done_tasks_count
    # -----------------------------
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]

    if "done_tasks_count" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN done_tasks_count INTEGER DEFAULT 0")
        print("✅ column done_tasks_count added")
    else:
        print("ℹ️ done_tasks_count already exists")

    # -----------------------------
    # 2️⃣ ساخت جدول history
    # -----------------------------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            category TEXT,
            priority INTEGER,
            done_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    print("✅ task_history table ensured")

    # ایندکس برای سرعت گزارش‌ها
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_user_date
        ON task_history (user_id, done_date)
        """
    )

    # -----------------------------
    # 3️⃣ انتقال داده‌های قبلی (۲ ماه اخیر)
    # -----------------------------
    two_months_ago = datetime.now() - timedelta(days=60)
    two_months_ago_str = two_months_ago.strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        SELECT id, user_id, title, category, priority, done_date
        FROM tasks
        WHERE is_done = 1 AND done_date >= ?
        """,
        (two_months_ago_str,),
    )

    rows = cur.fetchall()

    inserted = 0

    for row in rows:
        _, user_id, title, category, priority, done_date = row

        # چک کنیم قبلا وارد نشده باشه (idempotent)
        cur.execute(
            """
            SELECT 1 FROM task_history
            WHERE user_id = ? AND title = ? AND done_date = ?
            """,
            (user_id, title, done_date),
        )

        if cur.fetchone():
            continue

        cur.execute(
            """
            INSERT INTO task_history (user_id, title, category, priority, done_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, title, category, priority, done_date),
        )

        inserted += 1

    print(f"✅ {inserted} history rows inserted")

    # -----------------------------
    # 4️⃣ مقداردهی اولیه done_tasks_count
    # -----------------------------
    cur.execute(
        """
        UPDATE users
        SET done_tasks_count = (
            SELECT COUNT(*)
            FROM tasks t
            WHERE t.user_id = users.id AND t.is_done = 1
        )
        """
    )

    print("✅ done_tasks_count backfilled")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
