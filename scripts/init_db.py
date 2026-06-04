import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ooh_signal.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 信号表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS signals (
        id TEXT PRIMARY KEY,
        brand_name TEXT NOT NULL,
        industry TEXT,
        signal_type TEXT NOT NULL,
        title TEXT,
        summary TEXT,
        source_url TEXT,
        source_name TEXT,
        score INTEGER DEFAULT 0,
        reason TEXT,
        published_at TEXT,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        tags TEXT DEFAULT '[]',
        likes INTEGER DEFAULT 0,
        reposts INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        author TEXT,
        author_followers INTEGER DEFAULT 0
    )
    ''')

    # 品牌表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS brands (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        industry TEXT,
        scale TEXT DEFAULT 'small',
        is_listed INTEGER DEFAULT 0,
        signal_count INTEGER DEFAULT 0,
        latest_score INTEGER DEFAULT 0,
        website TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 数据源配置表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT,
        source_type TEXT,
        is_active INTEGER DEFAULT 1,
        last_collected_at TEXT
    )
    ''')

    # 品牌评分历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS score_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_name TEXT NOT NULL,
        score INTEGER NOT NULL,
        signal_count INTEGER DEFAULT 0,
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_score ON signals(score DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_collected ON signals(collected_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_brand ON signals(brand_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_industry ON signals(industry)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_score_history_brand ON score_history(brand_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_score_history_date ON score_history(recorded_at)')

    # 添加新字段（如果不存在）
    migrations = [
        ("signals", "likes", "INTEGER DEFAULT 0"),
        ("signals", "reposts", "INTEGER DEFAULT 0"),
        ("signals", "comments", "INTEGER DEFAULT 0"),
        ("signals", "author", "TEXT"),
        ("signals", "author_followers", "INTEGER DEFAULT 0"),
    ]
    for table, column, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            pass  # 列已存在

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_db()
