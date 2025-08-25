from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3

app = Flask(__name__)
DATABASE = "helpdesk.sqlite3"

def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
      CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        desc TEXT,
        priority TEXT CHECK(priority IN ('Low','Medium','High')) DEFAULT 'Low',
        status TEXT CHECK(status IN ('Open','Closed')) DEFAULT 'Open',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    """)
    db.commit()

@app.route("/")
def index():
    q = request.args.get("q","").strip()
    db = get_db()
    if q:
        rows = db.execute(
            "SELECT * FROM tickets WHERE title LIKE ? OR desc LIKE ? ORDER BY id DESC",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    counts = db.execute("""
      SELECT
        SUM(CASE WHEN status='Open'  THEN 1 ELSE 0 END) AS open_count,
        SUM(CASE WHEN status='Closed'THEN 1 ELSE 0 END) AS closed_count
      FROM tickets
    """).fetchone()
    return render_template("tickets.html", tickets=rows, q=q, counts=counts)

@app.route("/tickets/new", methods=["POST"])
def new_ticket():
    title = request.form.get("title","").strip()
    desc = request.form.get("desc","").strip()
    priority = request.form.get("priority","Low")
    if title:
        db = get_db()
        db.execute("INSERT INTO tickets (title, desc, priority, status) VALUES (?,?,?, 'Open')",
                   (title, desc, priority))
        db.commit()
    return redirect(url_for("index"))

@app.route("/tickets/<int:tid>/close", methods=["POST"])
def close_ticket(tid):
    db = get_db()
    db.execute("UPDATE tickets SET status='Closed' WHERE id=?", (tid,))
    db.commit()
    return redirect(url_for("index"))

@app.route("/tickets/<int:tid>/delete", methods=["POST"])
def delete_ticket(tid):
    db = get_db()
    db.execute("DELETE FROM tickets WHERE id=?", (tid,))
    db.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
