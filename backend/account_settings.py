"""Session-protected account management; device APIs remain unchanged."""
import json
import os
import re
import secrets
import sqlite3
from functools import wraps
from pathlib import Path
from flask import Blueprint, request, session, jsonify, render_template, redirect
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint("accounts", __name__)
DB = Path(__file__).resolve().parent.parent / "data" / "accounts.sqlite3"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, username TEXT UNIQUE COLLATE NOCASE NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL, password_hash TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1)")
    if not db.execute("SELECT 1 FROM accounts LIMIT 1").fetchone():
        legacy = DB.parent / "auth.json"
        if legacy.exists():
            data = json.loads(legacy.read_text(encoding="utf-8"))
            username, hashed = data["username"], data["password_hash"]
        else:
            username = os.environ.get("GATEWAY_ADMIN_USER", "admin")
            hashed = generate_password_hash(os.environ.get("GATEWAY_ADMIN_PASSWORD", "admin"))
        db.execute("INSERT INTO accounts(username,name,role,password_hash) VALUES(?,?,?,?)",
                   (username, "Selvarithik", "creator", hashed))
        db.commit()
    return db

def public(row):
    return {key: row[key] for key in ("id", "username", "name", "role")}

def current(db):
    row = db.execute("SELECT * FROM accounts WHERE id=?", (session.get("account_id"),)).fetchone()
    return row if row and row["version"] == session.get("account_version") else None

def protected(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        db = connect()
        try:
            actor = current(db)
            if not actor:
                return jsonify(error="Sign in to manage accounts."), 401
            if request.method != "GET" and not secrets.compare_digest(
                    request.headers.get("X-CSRF-Token", ""), session.get("account_csrf", secrets.token_hex(32))):
                return jsonify(error="Session token invalid. Reload and try again."), 403
            return fn(db, actor, *args, **kwargs)
        finally:
            db.close()
    return wrapped

@bp.get("/accounts")
def page():
    session.setdefault("account_csrf", secrets.token_hex(32))
    return render_template("accounts.html", account_csrf=session["account_csrf"])

@bp.app_context_processor
def account_context():
    session.setdefault("account_csrf", secrets.token_hex(32))
    db = connect()
    try:
        actor = current(db)
        return {"signed_account": public(actor) if actor else None, "sensor_csrf": session["account_csrf"]}
    finally:
        db.close()

@bp.post("/api/accounts/sign-in")
def sign_in():
    if not secrets.compare_digest(request.headers.get("X-CSRF-Token", ""), session.get("account_csrf", secrets.token_hex(32))):
        return jsonify(error="Reload Account Settings before signing in."), 403
    payload = request.get_json(silent=True) or {}
    db = connect()
    try:
        row = db.execute("SELECT * FROM accounts WHERE username=?", (str(payload.get("username", "")),)).fetchone()
        if not row or not check_password_hash(row["password_hash"], str(payload.get("password", ""))):
            return jsonify(error="Invalid user ID or password."), 401
        session.clear()
        session.update(account_id=row["id"], account_version=row["version"], account_csrf=secrets.token_hex(32))
        return jsonify(user=public(row), csrf=session["account_csrf"])
    finally:
        db.close()

@bp.get("/api/accounts")
@protected
def listing(db, actor):
    rows = db.execute("SELECT * FROM accounts ORDER BY username").fetchall() if actor["role"] != "user" else [actor]
    return jsonify(user=public(actor), accounts=[public(row) for row in rows], csrf=session["account_csrf"])

def may_manage(actor, target):
    return actor["role"] == "creator" or (actor["role"] == "administrator" and target["role"] == "user")

@bp.route("/api/accounts", methods=["POST"])
@bp.route("/api/accounts/<int:account_id>", methods=["PATCH", "DELETE"])
@protected
def mutate(db, actor, account_id=None):
    payload = request.get_json(silent=True) or {}
    target = db.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone() if account_id else None
    if account_id and not target:
        return jsonify(error="Account not found."), 404
    own = target and target["id"] == actor["id"]
    if target and not own and not may_manage(actor, target):
        return jsonify(error="This account requires creator access."), 403
    if request.method == "DELETE":
        if own:
            return jsonify(error="You cannot delete your signed-in account."), 400
        if target["role"] == "creator" and db.execute("SELECT COUNT(*) FROM accounts WHERE role='creator'").fetchone()[0] <= 1:
            return jsonify(error="Keep at least one creator."), 400
        db.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        db.commit()
        return jsonify(success=True)
    role = payload.get("role", target["role"] if target else "user")
    if role not in ("user", "administrator", "creator"):
        return jsonify(error="Invalid account type."), 400
    if not target and (actor["role"] == "user" or (actor["role"] == "administrator" and role != "user")):
        return jsonify(error="Insufficient permission to create this account type."), 403
    if target and role != target["role"]:
        if actor["role"] != "creator":
            return jsonify(error="Only creators can change account types."), 403
        if target["role"] == "creator" and db.execute("SELECT COUNT(*) FROM accounts WHERE role='creator'").fetchone()[0] <= 1:
            return jsonify(error="Keep at least one creator."), 400
    username = str(payload.get("username", target["username"] if target else "")).strip()
    name = str(payload.get("name", target["name"] if target else "")).strip()
    password = payload.get("password", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,40}", username) or not 1 <= len(name) <= 80:
        return jsonify(error="Name is required (up to 80 characters). User ID must be 3-40 letters, digits, dots, underscores or hyphens."), 400
    if not isinstance(password, str) or ((not target or password) and not 10 <= len(password) <= 128):
        return jsonify(error="New passwords must contain 10-128 characters."), 400
    if own and password and not check_password_hash(target["password_hash"], str(payload.get("current_password", ""))):
        return jsonify(error="Current password is incorrect."), 400
    try:
        if target:
            hashed = generate_password_hash(password) if password else target["password_hash"]
            db.execute("UPDATE accounts SET username=?,name=?,role=?,password_hash=?,version=version+1 WHERE id=?",
                       (username, name, role, hashed, account_id))
            if own:
                session["account_version"] = target["version"] + 1
        else:
            db.execute("INSERT INTO accounts(username,name,role,password_hash) VALUES(?,?,?,?)",
                       (username, name, role, generate_password_hash(password)))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="User ID already exists."), 409
    return jsonify(success=True)
