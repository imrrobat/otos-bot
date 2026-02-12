import sqlite3
from datetime import datetime, timedelta, date
from datetime import datetime
from pytz import timezone

DB_NAME = "otos.db"


tehran_tz = timezone("Asia/Tehran")
today_str = datetime.now(tehran_tz).date().isoformat()


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_users_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            score INTEGER DEFAULT 0,
            join_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


def create_tasks_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            category TEXT,
            priority INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_done INTEGER DEFAULT 0,
            done_date TEXT,
            is_expired INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    )

    conn.commit()
    conn.close()


def init_db():
    create_users_table()
    create_tasks_table()


def get_user_by_telegram_id(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()

    conn.close()
    return user


def add_user(telegram_id, full_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (telegram_id, full_name)
        VALUES (?, ?)
    """,
        (telegram_id, full_name),
    )

    conn.commit()
    conn.close()


def add_task(user_telegram_id, title, category, priority):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return False

    user_id = user[0]

    cur.execute(
        """
        INSERT INTO tasks (user_id, title, category, priority)
        VALUES (?, ?, ?, ?)
    """,
        (user_id, title, category, int(priority)),
    )

    conn.commit()
    conn.close()
    return True


def get_user_tasks(telegram_id, only_pending=True):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return []

    user_id = user[0]

    if only_pending:
        cur.execute(
            """
            SELECT id, title, category, priority
            FROM tasks
            WHERE user_id = ? AND is_done = 0
        """,
            (user_id,),
        )
    else:
        cur.execute(
            """
            SELECT id, title, category, priority
            FROM tasks
            WHERE user_id = ?
        """,
            (user_id,),
        )

    rows = cur.fetchall()
    conn.close()

    tasks = []
    for row in rows:
        tasks.append(
            {"id": row[0], "title": row[1], "category": row[2], "priority": row[3]}
        )

    return tasks


def delete_task(task_id, telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return False

    user_id = user[0]

    cur.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    task = cur.fetchone()
    if not task:
        conn.close()
        return False

    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    cur.execute(
        """
        UPDATE users
        SET score = score - 2
        WHERE id = ?
    """,
        (user_id,),
    )

    conn.commit()
    conn.close()
    return True


def mark_task_done(task_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT created_at, user_id, priority FROM tasks WHERE id = ?", (task_id,)
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "تسک پیدا نشد"

    created_at_str, user_id, priority = row
    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    elapsed = now - created_at

    if elapsed < timedelta(minutes=30):
        remaining = timedelta(minutes=30) - elapsed
        minutes_left = int(remaining.total_seconds() // 60)
        conn.close()
        return (
            False,
            f"⚠️ هنوز نیم ساعت از ایجاد کار نگذشته. {minutes_left} دقیقه دیگر صبر کنید.",
        )

    cur.execute(
        """
        UPDATE tasks
        SET is_done = 1, done_date = CURRENT_TIMESTAMP
        WHERE id = ?
    """,
        (task_id,),
    )

    cur.execute("UPDATE users SET score = score + ? WHERE id = ?", (priority, user_id))

    conn.commit()
    conn.close()
    return True, f"✅ تسک با موفقیت انجام شد و {priority} امتیاز به شما اضافه شد"


def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_done_tasks_today(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return [], 0

    user_id = user[0]

    cur.execute(
        """
        SELECT title, priority
        FROM tasks
        WHERE user_id = ? AND is_done = 1 AND DATE(done_date) = DATE('now')
    """,
        (user_id,),
    )

    rows = cur.fetchall()
    conn.close()

    tasks = [row[0] for row in rows]
    total_priority = sum([row[1] for row in rows])

    return tasks, total_priority


def get_user_count():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_total_done_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks WHERE is_done = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_user_done_tasks_today(user_telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    # today_str = date.today().isoformat()

    cur.execute(
        """
        SELECT title, priority
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        WHERE u.telegram_id = ? AND t.is_done = 1 AND DATE(t.done_date) = ?
    """,
        (user_telegram_id, today_str),
    )

    rows = cur.fetchall()
    conn.close()

    tasks = [{"title": row[0], "priority": row[1]} for row in rows]
    return tasks


def get_rank(score):
    if score >= 3000:
        return "شاه سیاه!"
    elif score >= 2000:
        return "شاه!"
    elif score >= 1500:
        return "وزیر!"
    elif score >= 1200:
        return "رخ دیوانه!"
    elif score >= 900:
        return "رخ!"
    elif score >= 600:
        return "راهب!"
    elif score >= 400:
        return "شوالیه!"
    elif score >= 250:
        return "سرباز!"
    else:
        return "پرنسس!"
