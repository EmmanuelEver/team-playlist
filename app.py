from flask import Flask, request, session, jsonify, make_response, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import safe_str_cmp
from flask_socketio import SocketIO, emit, send
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import json
import random
import os

app = Flask(__name__)
socketio = SocketIO(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL","sqlite:///data.db")
app.config["SECRET_KEY"] = os.environ.get("SECRET", "someSecretString")
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]
app.config["JWT_SECRET_KEY"] = "aasdasdj9882unsad"
db = SQLAlchemy(app)

loginmanager = LoginManager(app)
loginmanager.init_app(app)
loginmanager.login_view = "landing"

@loginmanager.user_loader
def load_user(user_id):
	return Room.query.get(int(user_id))

@app.before_first_request
def create_db():
	db.create_all()

class Room(UserMixin,db.Model):
	__tablename__ = "rooms"
	id = db.Column(db.Integer, primary_key = True)
	roomname = db.Column(db.String(30), unique = True, nullable = False)
	password = db.Column(db.String(20), nullable = False)
	masterKey = db.Column(db.String(20), nullable = False)
	date_created = db.Column(db.Date, nullable = False)
	users = db.relationship("User", backref = "member", lazy = "select")
	queue = db.relationship("Music", backref = "music", lazy = "select")

	def __init__(self, roomname, password, masterKey, date_created):
		self.roomname = roomname
		self.password = password
		self.masterKey = masterKey
		self.date_created = date_created

	def json(self):
		return {"roomname" : self.roomname, "admin" : self.admin}

	def add_music(self, music):
		self.queue.append(music)
		db.session.commit()

	def add_user(self, user):
		self.users.append(user)
		db.session.commit()

	def get_queue(self):
		return [ item.json() for item in self.queue ]

	def get_users(self):
		return [ user.json() for user in self.users ]

	def save_to_db(self):
		db.session.add(self)
		db.session.commit()

	def delete_from_db(self):
		db.session.delete(self)
		db.session.commit()

	@classmethod
	def find_by_id(cls, _id):
		room = cls.query.filter_by(id = _id).first()
		return room

	@classmethod
	def find_by_roomname(cls, roomname):
		room = cls.query.filter_by(roomname = roomname).first()
		return room


class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(30), unique = True, nullable = False)
	room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))

	def __init__(self, username):
		self.username = username

	def json(self):
		return {"username" : self.username, "avatar" :str(random.randint(1,8)) }

	def save_to_db(self):
		db.session.add(self)
		db.session.commit()

	def delete_from_db(self):
		db.session.delete(self)
		db.session.commit()

	@classmethod
	def find_by_username(cls, username):
		room = cls.query.filter_by(username = username).first()
		return room

	@classmethod
	def find_by_id(cls, id):
		user = cls.query.filter_by(id = id).first()
		return user


class Music(db.Model):
	__tablename__ = "musics"
	id = db.Column(db.Integer, primary_key = True)
	video_id = db.Column(db.String, nullable = False)
	video_title = db.Column(db.String, nullable = False)
	video_channel = db.Column(db.String)
	video_publishTime = db.Column(db.String(15))
	video_thumbnail = db.Column(db.String)
	room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))
	added_by = db.Column(db.String, nullable = False)

	def __init__(self, video_id, video_title, video_channel, video_publishTime, video_thumbnail, added_by):
		self.video_id = video_id
		self.video_title = video_title
		self.video_channel = video_channel
		self.video_publishTime = video_publishTime
		self.video_thumbnail = video_thumbnail
		self.added_by = added_by

	def json(self):
		return {
				"id" : self.id,
				"video_id" : self.video_id,
				"video_title" : self.video_title,
				"channel" : self.video_channel,
				"publishTime" : self.video_publishTime,
				"thumbnail" : self.video_thumbnail,
				"added_by" : self.added_by
			   }

	def save_to_db(self):
		db.session.add(self)
		db.session.commit()

	def delete_from_db(self):
		db.session.delete(self)
		db.session.commit()

	@classmethod
	def find_by_id(cls, id):
		music = cls.query.filter_by(id = id).first()
		return music


	@classmethod
	def find_by_videoId(cls, video_id):
		music = cls.query.filter_by(video_id = video_id).first()
		return music



@app.route("/", methods=["GET", "POST"])
def landing():
	if current_user.is_authenticated:
		return redirect(url_for("room"))
	if request.method == "POST":
		data = request.form
		roomname = data["roomname"]
		password = data["password"]
		room = Room.find_by_roomname(roomname)
		if room:
			if safe_str_cmp(password, room.password):
				login_user(room, remember=False)
				user = data.get("guestname", "anonymous")
				new_user = User(user)
				new_user.save_to_db()
				room.add_user(new_user)
				session["user"] = user
				session["id"] = new_user.id
				next_page = request.args.get("next")
				loc = "room" if not next_page or url_parse(next_page) else next_page
				return redirect(url_for(loc))

			flash("room password is incorrect", category="danger")
			return redirect(url_for("landing"))

		flash(f"No room with name, {roomname}", category="danger")
		return redirect(url_for("landing"))

	return render_template("landing.html")


@app.route("/create_room", methods=["GET", "POST"])
def new_room():
	if request.method == "POST":
		try:
			data = request.form.to_dict()
			user = User(data.get("guestname","anonymous"))
			data.pop("guestname")
			data["date_created"] = datetime.date(datetime.now())
			room = Room(**data)
			room.save_to_db()
			user.save_to_db()
			room.add_user(user)
			login_user(room)
			session["user"] = user.username
			session["id"] = user.id
			return redirect(url_for("room"))
		except Exception as e:
			print(e)
			return redirect(url_for(request.url))

	return render_template("register.html")


@app.route("/room")
@login_required
def room():
	return render_template("room.html", username = session.get("user"))


@app.route("/exit")
@login_required
def logout():
	session.pop("user")
	user = User.find_by_id(session.pop("id"))
	user.delete_from_db()
	room = Room.find_by_roomname(current_user.roomname)
	users_left =  room.get_users()
	socketio.emit("new-user", users_left , broadcast = True)
	logout_user()
	return redirect(url_for("landing"))

@app.route("/delete-room", methods=["POST"])
@login_required
def delete_room():
	if request.method == "POST":
		data = request.form
		room = Room.find_by_roomname(current_user.roomname)
		if room and safe_str_cmp(room.masterKey, data["masterpassword"]):
			room.delete_from_db()
			return redirect(url_for("landing"))
		return jsonify({"msg" : "Invalid credentials"}), 401


@socketio.on("message", namespace = "/room")
def see_message(message):
	print(f"\n\n\n {message} \n\n\n")

@socketio.on("new-user", namespace = "/room")
def new_user(data):
	print(data)
	room = Room.find_by_roomname(current_user.roomname)
	if room:
		users = room.get_users() 
		queue =	room.get_queue()
		print(queue)
		print(room.queue)
		emit("new-user", users , broadcast = True)
		emit("get-queue", queue)

@socketio.on("new-queue-item", namespace = "/room")
def new_queue_item(data):
	print(data)
	room = Room.find_by_roomname(current_user.roomname)
	if room:
		music = Music(**data)
		music.save_to_db()
		room.add_music(music)
		emit("new-queue", music.json(), broadcast = True)

@socketio.on("finished_music", namespace = "/room")
def finished_music(data):
	print(f"\n\n{data['id']}")
	music = Music.find_by_id(data["id"])
	print(f"\n\n{music.json()}")
	try:
		if music and music.video_id == data["video_id"]:
			music.delete_from_db()
	except Exception as e:
		print(e)

# @socketio.on('disconnect')
# def test_disconnect():
#     user = User.find_by_id(session["id"])
#     print(f"\n\n{user.username} has left \n\n")
#     room = Room.find_by_roomname(current_user.roomname)
#     if user:
#     	user.delete_from_db()	
#     	users =  room.get_users() 
#     	emit("new-user", users , broadcast = True)

if __name__ == "__main__":
	app.run()