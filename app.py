import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash

# Use /tmp for SQLite file on Elastic Beanstalk (writable location)
DB_PATH = os.path.join("/tmp", "letstalk.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-please-change")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Use eventlet in production (with gunicorn), threading for local dev
async_mode = "eventlet" if os.environ.get("FLASK_ENV") == "production" else "threading"
socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins="*")

login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text, default="")
    avatar_url = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship("Post", backref="author", lazy=True, cascade="all, delete-orphan")
    likes = db.relationship("PostLike", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship("PostLike", backref="post", lazy=True, cascade="all, delete-orphan")

    @property
    def like_count(self) -> int:
        return len(self.likes)


class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seen_at = db.Column(db.DateTime, nullable=True)

    @property
    def status(self) -> str:
        return "seen" if self.seen_at else "sent"


# Create tables once at startup (instead of on every request)
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


@app.route("/")
@login_required
def home():
    users = User.query.filter(User.id != current_user.id).order_by(User.display_name).all()
    recent_messages = (
        Message.query.filter(
            (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
        )
        .order_by(Message.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("home.html", users=users, recent_messages=recent_messages)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not display_name or not password:
            flash("All fields are required.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
        else:
            user = User(username=username, display_name=display_name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to Let'sTalk!", "success")
            return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in!", "success")
            return redirect(url_for("home"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


@app.route("/users")
@login_required
def user_list():
    users = User.query.order_by(User.display_name).all()
    return render_template("users.html", users=users)


@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    liked_post_ids = {like.post_id for like in current_user.likes}
    return render_template("profile.html", profile_user=user, posts=posts, liked_post_ids=liked_post_ids)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.display_name = request.form.get("display_name", current_user.display_name).strip()
        current_user.bio = request.form.get("bio", current_user.bio).strip()
        current_user.avatar_url = request.form.get("avatar_url", current_user.avatar_url).strip()
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile", user_id=current_user.id))
    return render_template("edit_profile.html")


@app.route("/posts/create", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content", "").strip()
    if not content:
        flash("Post cannot be empty.", "danger")
    else:
        post = Post(user_id=current_user.id, content=content)
        db.session.add(post)
        db.session.commit()
        flash("Posted!", "success")
    return redirect(url_for("profile", user_id=current_user.id))


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = db.session.get(Post, post_id) or abort(404)
    if post.user_id != current_user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post removed.", "info")
    return redirect(url_for("profile", user_id=current_user.id))


@app.route("/posts/<int:post_id>/like", methods=["POST"])
@login_required
def like_post(post_id: int):
    post = db.session.get(Post, post_id) or abort(404)
    existing = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        db.session.delete(existing)
        flash("Unliked.", "info")
    else:
        db.session.add(PostLike(user_id=current_user.id, post_id=post.id))
        flash("Liked!", "success")
    db.session.commit()
    return redirect(url_for("profile", user_id=post.user_id))


@app.route("/chat/<int:user_id>")
@login_required
def chat(user_id: int):
    other = db.session.get(User, user_id) or abort(404)
    if other.id == current_user.id:
        flash("You cannot chat with yourself.", "warning")
        return redirect(url_for("home"))
    messages = (
        Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == other.id))
            | ((Message.sender_id == other.id) & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )
    # Mark incoming messages as seen.
    unseen = [
        m
        for m in messages
        if m.receiver_id == current_user.id and m.seen_at is None
    ]
    if unseen:
        for m in unseen:
            m.seen_at = datetime.utcnow()
        db.session.commit()
    return render_template("chat.html", other=other, messages=messages)


@app.route("/chat/<int:user_id>/send", methods=["POST"])
@login_required
def send_message(user_id: int):
    other = db.session.get(User, user_id) or abort(404)
    if other.id == current_user.id:
        abort(400)
    if request.is_json:
        content = (request.json or {}).get("content", "").strip()
    else:
        content = request.form.get("content", "").strip()
    if not content:
        flash("Message cannot be empty.", "danger")
        return redirect(url_for("chat", user_id=other.id))
    msg = Message(sender_id=current_user.id, receiver_id=other.id, content=content)
    db.session.add(msg)
    db.session.commit()
    payload = {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "sender_name": current_user.display_name,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
        "seen_at": None,
        "status": msg.status,
    }
    socketio.emit("message", payload, room=f"user-{current_user.id}")
    socketio.emit("message", payload, room=f"user-{other.id}")
    unread_total = Message.query.filter_by(receiver_id=other.id, seen_at=None).count()
    socketio.emit("unread", {"count": unread_total}, room=f"user-{other.id}")
    if request.is_json:
        return jsonify(payload), 201
    return redirect(url_for("chat", user_id=other.id))


@app.route("/api/messages/<int:user_id>")
@login_required
def api_messages(user_id: int):
    other = db.session.get(User, user_id) or abort(404)
    messages = (
        Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == other.id))
            | ((Message.sender_id == other.id) & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )
    return jsonify(
        [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.author.display_name if hasattr(m, "author") else None if not hasattr(m, "author") else None,
                "receiver_id": m.receiver_id,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "seen_at": m.seen_at.isoformat() if m.seen_at else None,
                "status": m.status,
            }
            for m in messages
        ]
    )


@app.route("/api/messages/<int:user_id>/seen", methods=["POST"])
@login_required
def api_mark_seen(user_id: int):
    other = db.session.get(User, user_id) or abort(404)
    incoming = Message.query.filter(
        (Message.sender_id == other.id) & (Message.receiver_id == current_user.id) & (Message.seen_at.is_(None))
    ).all()
    for msg in incoming:
        msg.seen_at = datetime.utcnow()
    db.session.commit()
    unread_total = Message.query.filter_by(receiver_id=current_user.id, seen_at=None).count()
    socketio.emit("unread", {"count": unread_total}, room=f"user-{current_user.id}")
    if incoming:
        socketio.emit(
            "seen",
            {"by": current_user.id, "for_user": other.id, "message_ids": [m.id for m in incoming]},
            room=f"user-{other.id}",
        )
    return jsonify({"updated": len(incoming), "unread": unread_total})


@app.route("/api/unread_count")
@login_required
def api_unread_count():
    unread_total = Message.query.filter_by(receiver_id=current_user.id, seen_at=None).count()
    return jsonify({"count": unread_total})


@socketio.on("join")
def on_join(data):
    user_id = data.get("user_id")
    if not current_user.is_authenticated or current_user.id != user_id:
        return False
    join_room(f"user-{user_id}")
    emit("joined", {"room": f"user-{user_id}"})


def main():
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    socketio.run(app, debug=debug, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
