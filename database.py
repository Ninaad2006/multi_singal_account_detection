import sqlite3
from datetime import datetime

DB_NAME = "history.db"

def init_db():
    """Create the database and tables if they don't exist"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            platform TEXT,
            prediction TEXT,
            risk_score INTEGER,
            risk_level TEXT,
            confidence REAL,
            followers INTEGER,
            following INTEGER,
            posts INTEGER,
            bio_length INTEGER,
            is_verified INTEGER,
            spam_score INTEGER,
            face_detected INTEGER,
            clone_detected INTEGER,
            analyzed_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized!")

def save_analysis(result):
    """Save an analysis result to the database"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT INTO history (
            username, platform, prediction, risk_score,
            risk_level, confidence, followers, following,
            posts, bio_length, is_verified, spam_score,
            face_detected, clone_detected, analyzed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["data"]["username"],
        result["platform"],
        result["prediction"],
        result.get("risk_score", 0),
        result.get("risk_level", ""),
        result.get("confidence", 0),
        result["data"]["followers"],
        result["data"]["following"],
        result["data"].get("posts", result["data"].get("tweets", 0)),
        result["data"]["bio_length"],
        1 if result["data"]["is_verified"] else 0,
        result.get("spam", {}).get("spam_score", 0),
        1 if result.get("face", {}).get("has_face") else 0,
        1 if result.get("clone", {}).get("is_clone") else 0,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_history(limit=50):
    """Get recent analysis history"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("""
        SELECT * FROM history
        ORDER BY analyzed_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_stats():
    """Get overall statistics"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN prediction = 'fake' THEN 1 ELSE 0 END) as fake_count,
            SUM(CASE WHEN prediction = 'real' THEN 1 ELSE 0 END) as real_count,
            AVG(risk_score) as avg_risk,
            SUM(CASE WHEN clone_detected = 1 THEN 1 ELSE 0 END) as clones_found
        FROM history
    """)
    row = cursor.fetchone()
    conn.close()
    return {
        "total": row[0] or 0,
        "fake_count": row[1] or 0,
        "real_count": row[2] or 0,
        "avg_risk": round(row[3] or 0, 1),
        "clones_found": row[4] or 0
    }

def delete_history():
    """Clear all history"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()

# Initialize database when imported
init_db()

def init_monitoring():
    """Create monitoring table"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS monitored_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            platform TEXT,
            last_risk_score INTEGER,
            last_checked TEXT,
            alert_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            platform TEXT,
            alert_type TEXT,
            message TEXT,
            old_score INTEGER,
            new_score INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_monitored_account(username, platform):
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("""
            INSERT OR IGNORE INTO monitored_accounts 
            (username, platform, last_checked)
            VALUES (?, ?, ?)
        """, (username, platform, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def remove_monitored_account(username):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM monitored_accounts WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_monitored_accounts():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM monitored_accounts ORDER BY username")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def save_alert(username, platform, alert_type, message, old_score, new_score):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT INTO alerts (username, platform, alert_type, message, old_score, new_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, platform, alert_type, message, old_score, new_score,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.execute("""
        UPDATE monitored_accounts 
        SET alert_count = alert_count + 1, last_checked = ?
        WHERE username = ?
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit()
    conn.close()

def get_alerts(limit=20):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("""
        SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_monitored_score(username, new_score):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        UPDATE monitored_accounts 
        SET last_risk_score = ?, last_checked = ?
        WHERE username = ?
    """, (new_score, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit()
    conn.close()

# Initialize monitoring tables
init_monitoring()