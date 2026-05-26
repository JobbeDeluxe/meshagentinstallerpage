from __future__ import annotations

import hmac
import json
import os
import re
import secrets
import tempfile
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CODES_FILE = BASE_DIR / "codes.json"
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_RE = re.compile(r"^[A-Z0-9]{4,12}$")


def get_codes_file() -> Path:
    return Path(os.environ.get("CODES_FILE", DEFAULT_CODES_FILE)).expanduser()


def normalize_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def load_codes(path: Path | None = None) -> dict[str, dict[str, str]]:
    codes_file = path or get_codes_file()
    if not codes_file.exists():
        return {}

    with codes_file.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        return {}

    cleaned: dict[str, dict[str, str]] = {}
    for code, entry in data.items():
        if not isinstance(entry, dict):
            continue
        normalized = normalize_code(str(code))
        if not normalized:
            continue
        cleaned[normalized] = {
            "name": str(entry.get("name") or "Geraet"),
            "download_url": str(entry.get("download_url") or ""),
        }
    return cleaned


def save_codes(codes: dict[str, dict[str, str]], path: Path | None = None) -> None:
    codes_file = path or get_codes_file()
    codes_file.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        dir=codes_file.parent,
        prefix=f".{codes_file.name}.",
        suffix=".tmp",
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(codes, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp_name, codes_file)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def generate_code(existing: dict[str, dict[str, str]], length: int = 6) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))
        if code not in existing:
            return code


def is_valid_download_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_csrf() -> None:
    token = request.form.get("csrf_token", "")
    if not token or not hmac.compare_digest(token, session.get("csrf_token", "")):
        abort(400)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "")
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/lookup")
    def lookup():
        payload = request.get_json(silent=True) or {}
        code = normalize_code(str(payload.get("code", "")))
        entry = load_codes().get(code)
        if not entry:
            return jsonify({"ok": False, "message": "Code nicht gefunden."}), 404

        return jsonify(
            {
                "ok": True,
                "name": entry.get("name") or "Geraet",
                "download_url": entry["download_url"],
            }
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True})

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if not app.config["ADMIN_PASSWORD"]:
            return render_template("login.html", admin_disabled=True), 503

        if request.method == "POST":
            validate_csrf()
            password = request.form.get("password", "")
            if hmac.compare_digest(password, app.config["ADMIN_PASSWORD"]):
                session.clear()
                session["admin"] = True
                csrf_token()
                return redirect(request.args.get("next") or url_for("admin"))
            flash("Passwort stimmt nicht.", "error")

        return render_template("login.html", admin_disabled=False)

    @app.post("/admin/logout")
    @login_required
    def admin_logout():
        validate_csrf()
        session.clear()
        return redirect(url_for("admin_login"))

    @app.get("/admin")
    @login_required
    def admin():
        codes = load_codes()
        sorted_codes = sorted(codes.items(), key=lambda item: item[0])
        return render_template("admin.html", codes=sorted_codes)

    @app.post("/admin/codes")
    @login_required
    def save_code():
        validate_csrf()
        codes = load_codes()
        requested_code = normalize_code(request.form.get("code", ""))
        code = requested_code or generate_code(codes)
        name = request.form.get("name", "").strip()
        download_url = request.form.get("download_url", "").strip()

        if not CODE_RE.match(code):
            flash("Der Code darf nur 4 bis 12 Buchstaben/Zahlen enthalten.", "error")
            return redirect(url_for("admin"))
        if not name:
            flash("Bitte einen Geraetenamen eintragen.", "error")
            return redirect(url_for("admin"))
        if not is_valid_download_url(download_url):
            flash("Bitte eine gueltige http(s)-Download-URL eintragen.", "error")
            return redirect(url_for("admin"))

        codes[code] = {"name": name, "download_url": download_url}
        save_codes(codes)
        flash(f"Code {code} wurde gespeichert.", "success")
        return redirect(url_for("admin"))

    @app.post("/admin/codes/<code>/delete")
    @login_required
    def delete_code(code: str):
        validate_csrf()
        normalized = normalize_code(code)
        codes = load_codes()
        if normalized in codes:
            del codes[normalized]
            save_codes(codes)
            flash(f"Code {normalized} wurde geloescht.", "success")
        return redirect(url_for("admin"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055, debug=False)
