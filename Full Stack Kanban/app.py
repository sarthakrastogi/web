from flask import *
from flask_caching import Cache
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_cors import CORS
from flask_login import current_user
import sqlite3
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from datetime import datetime
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from celery import Celery
from httplib2 import Http
from json import dumps
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from dateutil import parser
import json
from celery.schedules import crontab
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



DEBUG = True
global dbfilename
dbfilename = 'instance/database8.db'
global TASKS_TABLE
TASKS_TABLE = "tasks_table"
global LISTS_TABLE
LISTS_TABLE = "lists_table"

app = Flask(__name__)
app.config["CELERY_BROKER_URL"] = "redis://localhost:6379"
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_HOST"] = "localhost"
app.config["CACHE_REDIS_PORT"] = 6379

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"], backend="redis://localhost:6379")
celery.conf.update(app.config)

cache = Cache(app)

CORS(app, resources={r'/*': {'origins': '*'}})


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database8.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)




login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#source: official flask_login documentation

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), nullable=False, unique=True)
    password = db.Column(db.String(10), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=8, max=14)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=14)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Sign up')
    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError(
                'Username already exists!')


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=8, max=14)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=14)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Sign in')


class List(db.Model, UserMixin):
    list_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    list_title = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.String(64), nullable=False)
    last_updated_at = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)


class Task(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.String(64), nullable=False)
    deadline = db.Column(db.String(64), nullable=False)
    completed_flag = db.Column(db.String(64), nullable=False)
    list_id = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.String(64), nullable=False)
    last_updated_at = db.Column(db.String(64), nullable=False)
    completed_at = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(64), nullable=False)



@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                print("logged in as", user.username)
                global username
                username = user.username
                return redirect(url_for('kanbanhome', username=user.username))
    return render_template('signin.html', form=form)


@ app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        db.session.add(User(username=form.username.data, password=bcrypt.generate_password_hash(form.password.data)))
        db.session.commit()
        return redirect(url_for('signin'))
    return render_template('signup.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('signin'))


@app.route('/kanban/<username>')
@cache.cached(timeout=2)
@login_required
def kanbanhome(username):
    with sqlite3.connect(dbfilename) as conn:
        cur = conn.cursor()
        cur.execute(f"select * from {TASKS_TABLE} where username='{username}';")
        taskslist = cur.fetchall()
        cur.execute(f"select * from {LISTS_TABLE} where username='{username}';")
        listslist = cur.fetchall()
        return render_template("main.html")#, status='success', tasksjin=taskslist, listsjin=listslist)



@app.route('/insert_task/<username>', methods=['GET', 'POST'])
@login_required
def insert(username):
    response_object = {'status': 'success'}
    if request.method == 'POST':
        post_data = request.get_json(silent=True)
        #id = post_data.get('id')
        title = post_data.get('title')
        content = post_data.get('content')
        deadline = post_data.get('deadline')
        completed_flag = post_data.get('completed_flag')
        list_id = post_data.get('list_id')

        print(title, content, deadline, completed_flag, list_id)

        with sqlite3.connect(dbfilename) as conn:
            print(3)
            cur = conn.cursor()
            if completed_flag == "True":
                cur.execute(f'insert into {TASKS_TABLE} (title, content, deadline, completed_flag, list_id, created_at, completed_at, username) values ("{title}", "{content}", "{deadline}", "{completed_flag}", "{list_id}", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, "{username}")')
            else:
                cur.execute(f'insert into {TASKS_TABLE} (title, content, deadline, completed_flag, list_id, created_at, username) values ("{title}", "{content}", "{deadline}", "{completed_flag}", "{list_id}", CURRENT_TIMESTAMP, "{username}")')

            conn.commit()
            print('insertion complete')
        response_object['message'] = "Successfully Added"
    return jsonify(response_object)

@app.route('/edit_task/<string:id>/<username>', methods=['GET', 'POST'])
@login_required
def edit(id, username):
    with sqlite3.connect(dbfilename) as conn:
        print("editing task with id: ", id)
        cur = conn.cursor()
        cur.execute(f"select * from {TASKS_TABLE} WHERE id = '{id}' and username = '{username}'")
        row = cur.fetchone()
        print('editing task complete')
    return jsonify({
        'status': 'success',
        'editmember': row
    })


@app.route('/update_task/<username>', methods=['GET', 'POST'])
@login_required
def update(username):
    response_object = {'status': 'success'}
    if request.method == 'POST':
        with sqlite3.connect(dbfilename) as conn:
            cur = conn.cursor()
            post_data = request.get_json(silent=True)

            new_id = post_data.get('new_id')
            new_title = post_data.get('new_title')
            new_content = post_data.get('new_content')
            new_deadline = post_data.get('new_deadline')
            new_completed_flag = post_data.get('new_completed_flag')
            new_list_id = post_data.get('new_list_id')

            print(new_id, new_title, new_content, new_deadline, new_completed_flag, new_list_id)
            if new_completed_flag == "False":
                cur.execute(f"update {TASKS_TABLE} set title='{new_title}', content='{new_content}', deadline='{new_deadline}', completed_flag='{new_completed_flag}', list_id='{new_list_id}', last_updated_at=CURRENT_TIMESTAMP where id='{new_id}'")
            else:
                cur.execute(f"update {TASKS_TABLE} set title='{new_title}', content='{new_content}', deadline='{new_deadline}', completed_flag='{new_completed_flag}', list_id='{new_list_id}', last_updated_at=CURRENT_TIMESTAMP, completed_at=CURRENT_TIMESTAMP where id='{new_id}'")
            conn.commit()
            cur.close()
            print("updated task")

        response_object['message'] = "Successfully Updated"
    return jsonify(response_object)

@app.route('/delete_task/<string:id>/<username>', methods=['GET', 'POST'])
@login_required
def delete(id, username):
    with sqlite3.connect(dbfilename) as conn:
        print("deleting task with id", id)
        cur = conn.cursor()
        response_object = {'status': 'success'}
        cur.execute(f"delete from {TASKS_TABLE} where id='{id}'")
        conn.commit()
        cur.close()
        print("deleted task")

    response_object['message'] = "Successfully Deleted"
    return jsonify(response_object)


@celery.task()
def export_a_task(id):
    with sqlite3.connect(dbfilename) as conn:
        print("exporting task with id", id)
        cur = conn.cursor()
        cur.execute(f"select * from {TASKS_TABLE} where id='{id}'")
        row = cur.fetchall()
        print("exported row is ", row)
        df = pd.DataFrame(row, columns=['id', 'title', 'content', 'deadline', 'completed_flag', 'list_id', 'created_at', 'last_updated_at', 'completed_at', 'username'])
        df.to_csv(str(row[0][1])+'.csv', index=False)
        conn.commit()
        cur.close()
        print("exported task")


@celery.task()
def export_a_board(username):
    with sqlite3.connect(dbfilename) as conn:
        print("exporting board")
        cur = conn.cursor()
        cur.execute(f"select * from {TASKS_TABLE} where username='{username}'")
        row = cur.fetchall()
        print("exported table is ", row)
        df = pd.DataFrame(row, columns=['id', 'title', 'content', 'deadline', 'completed_flag', 'list_id', 'created_at', 'last_updated_at', 'completed_at', 'username'])
        df.to_csv('task_board.csv', index=False)
        conn.commit()
        cur.close()
        print("exported the whole board")


@app.route('/export_task/<string:id>', methods=['GET', 'POST'])
@login_required
def export(id):
    export_a_task.delay(id)
    response_object = {'status': 'success'}
    response_object['message'] = "Successfully Exported"
    return jsonify(response_object)


@app.route('/export_all/<username>', methods=['GET', 'POST'])
@login_required
def export_all(username):
    export_a_board.delay(username)
    response_object = {'status': 'success'}
    response_object['message'] = "Successfully Exported"
    return jsonify(response_object)


@app.route('/insert_list/<username>', methods=['GET', 'POST'])
@login_required
def insert_list(username):
    response_object = {'status': 'success'}
    if request.method == 'POST':
        post_data = request.get_json(silent=True)
        #list_id = post_data.get('list_list_id')
        list_title = post_data.get('list_title')
        with sqlite3.connect(dbfilename) as conn:
            cur = conn.cursor()
            cur.execute(f'insert into {LISTS_TABLE} (list_title, created_at, last_updated_at, username) values ("{list_title}", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, "{username}")')
            conn.commit()
            print("added list")
        response_object['message'] = "Successfully Added"
    return jsonify(response_object)

@app.route('/edit_list/<string:list_id>/<username>', methods=['GET', 'POST'])
@login_required
def edit_list(list_id, username):
    with sqlite3.connect(dbfilename) as conn:
        print("editing list with id: ", list_id)
        cur = conn.cursor()
        cur.execute(f"select * from {LISTS_TABLE} WHERE list_id = '{list_id}' and username = '{username}'")
        row = cur.fetchone()
        print('fetching list complete')
    return jsonify({
        'status': 'success',
        'editmember': row
    })

@app.route('/update_list/<username>', methods=['GET', 'POST'])
@login_required
def update_list(username):
    response_object = {'status': 'success'}
    if request.method == 'POST':
        with sqlite3.connect(dbfilename) as conn:
            cur = conn.cursor()
            post_data = request.get_json(silent=True)
            #new_list_id = post_data.get('new_list_list_id')
            new_list_title = post_data.get('new_list_title')
            current_list_id = post_data.get('current_list_id')

            print("replacing list with id", current_list_id, "with", new_list_title)

            cur.execute(f"select list_title from {LISTS_TABLE} WHERE list_id = '{current_list_id}' and username = '{username}'")
            row = cur.fetchone()

            print("current list name", row)

            cur.execute(f"update {LISTS_TABLE} set list_title='{new_list_title}', last_updated_at=CURRENT_TIMESTAMP where list_id='{current_list_id}' and username = '{username}'")

            cur.execute(f"update {TASKS_TABLE} set list_id='{new_list_title}', last_updated_at=CURRENT_TIMESTAMP where list_id='{row[0]}' and username = '{username}'")
            conn.commit()
            cur.close()
            print("edited list")

        response_object['message'] = "Successfully Updated"
    return jsonify(response_object)


@app.route('/delete_list/<string:list_id>/<username>', methods=['GET', 'POST'])
@login_required
def delete_list(list_id, username):
    with sqlite3.connect(dbfilename) as conn:
        cur = conn.cursor()
        cur.execute(f"select * from {LISTS_TABLE} WHERE list_id = '{list_id}'")
        row = cur.fetchone()
    return jsonify({
        'status': 'success',
        'editmember': row
    })


@app.route('/pre_delete_list/<username>', methods=['GET', 'POST'])
@login_required
def pre_delete_list(username):
    response_object = {'status': 'success'}
    if request.method == 'POST':
        with sqlite3.connect(dbfilename) as conn:
            cur = conn.cursor()
            post_data = request.get_json(silent=True)
            list_name_for_deletion = post_data.get('list_name_for_deletion')
            what_to_do = post_data.get('what_to_do')
            list_holding_these_tasks = post_data.get('list_holding_these_tasks')

            cur.execute(f"select list_id from {LISTS_TABLE} where list_title='{list_name_for_deletion}'")
            required_list_id = cur.fetchall()
            if required_list_id != []:
                required_list_id = required_list_id[0][0]
            cur.execute(f"select list_id from {LISTS_TABLE} where list_title='{list_holding_these_tasks}'")
            list_to_replace_with = cur.fetchall()
            if list_to_replace_with != []:
                list_to_replace_with = list_to_replace_with[0][0]

            if what_to_do == "delete_tasks_in_this_list":
                print("deleting all tasks with lid ", required_list_id, list_name_for_deletion)
                cur.execute(f"delete from {TASKS_TABLE} where list_id='{list_name_for_deletion}'")
                conn.commit()
                cur.execute(f"delete from {LISTS_TABLE} where list_id='{required_list_id}'")
                conn.commit()
            elif what_to_do == "move_tasks_to_other_list":
                print("moving tasks to ", list_holding_these_tasks, list_to_replace_with)
                cur.execute(f"update {TASKS_TABLE} set list_id='{list_holding_these_tasks}', last_updated_at=CURRENT_TIMESTAMP where list_id='{list_name_for_deletion}'")
                conn.commit()
                cur.execute(f"delete from {LISTS_TABLE} where list_id='{required_list_id}'")
                conn.commit()
            cur.close()

        response_object['message'] = "Successfully Updated"
    return jsonify(response_object)


@app.route('/fetch/<username>', methods=['GET'])
def fetchkanban(username):
    with sqlite3.connect(dbfilename) as conn:
        cur = conn.cursor()
        cur.execute(f"select * from {TASKS_TABLE} where username='{username}';")
        taskslist = cur.fetchall()
        cur.execute(f"select * from {LISTS_TABLE} where username='{username}';")
        listslist = cur.fetchall()
    result = jsonify({
        'status': 'success',
        'tasks': taskslist,
        'lists': listslist,
        'username': username
    })
    print(result)
    return result


@app.route('/user', methods=['GET'])
def usern():
    result = jsonify({
        'status': 'success',
        'username': username
    })
    return result



@celery.task()
def plotReport(username):
    with sqlite3.connect(dbfilename) as conn:
        cur = conn.cursor()
        cur.execute(f"select distinct list_title from {LISTS_TABLE} where username='{username}'")
        all_lists = [i[0] for i in cur.fetchall()]
        images = []
        past_deadline = []
        completed_tasks = []

        for list_name in all_lists:
            cur.execute(f"select * from {TASKS_TABLE} where list_id='{list_name}'")
            rows = cur.fetchall()
            fig = Figure()
            axis = fig.add_subplot(1, 1, 1)
            axis.set_title(list_name, fontsize=32)
            if rows:
                for row in rows:
                    (tid, title, desc, dl, comp, lname, created, updated, completed, username) = row
                    axis.grid()
                    format = '%Y-%m-%d %H:%M:%S'
                    y = [created, updated, completed]
                    y = [datetime.strptime(time, format) if time else None for time in y]
                    x = ["created", "updated", "completed"]
                    axis.plot(x, y, "ro-", linewidth=5)
                    axis.grid(False)
                    axis.annotate(title, xy=(0, y[0]), fontsize=14, va="center", bbox=dict(boxstyle="round", fc=(1.0, 0.7, 0.7), ec="none"))
                pngImage = io.BytesIO()
                FigureCanvas(fig).print_png(pngImage)

                image = "data:image/png;base64," + base64.b64encode(pngImage.getvalue()).decode('utf8')
                images.append(image)


            tasks_in_this_list_past_deadline = []
            for row in rows:
                print("ROW TO PARSE", row)
                deadline = parser.parse(row[3])

                if deadline < datetime.now():# and not row[4]:
                    tasks_in_this_list_past_deadline.append((row[1], row[2], row[3], row[5]))
            past_deadline.append(tasks_in_this_list_past_deadline)


            tasks_in_this_list_completed = []
            for row in rows:
                if json.loads(row[4].lower()):
                    tasks_in_this_list_completed.append((row[1], row[2], row[3], row[5]))
            completed_tasks.append(tasks_in_this_list_completed)

    return images, past_deadline, completed_tasks


def mail(to, sub, message):
    msg = MIMEMultipart()
    msg['From'] = "sarthakrastogi.work@gmail.com"
    msg['To'] = to
    msg['Subject'] = sub
    msg.attach(MIMEText(message, 'html'))
    s = smtplib.SMTP(host="localhost", port=1025)
    s.login(msg['From'], "abcd")
    s.send_message(msg)
    s.quit()
    return True



@celery.on_after_finalize.connect
def setup_periodic_reports(sender, **kwargs):
    sender.add_periodic_task(
    crontab(day_of_month=1, month="*"),
    saveReport.s())

@celery.task()
def saveReport():
    res = plotReport.delay()
    images, past_deadline, completed_tasks = res.get()
    rendered_template =  render_template("b.html", images=images, past_deadline=past_deadline, completed_tasks=completed_tasks)
    mail("sarthakrastogi.work@gmail.com", "Monthly Report", rendered_template)
    with open("report.html", "w") as f:
        f.write(rendered_template)


@app.route("/plots/<username>", methods=["GET"])
@login_required
def plotView(username):
    res = plotReport.delay(username)
    images, past_deadline, completed_tasks = res.get()
    print("got images")
    rendered_template =  render_template("a.html", images=images, past_deadline=past_deadline, completed_tasks=completed_tasks)
    with open("report.html", "w") as f:
        f.write(rendered_template)
    return rendered_template


def send_messages_to_google_chat(text):
    #taken from official google documentation: https://developers.google.com/chat/how-tos/webhooks
    url = 'https://chat.googleapis.com/v1/spaces/AAAAR16zpIU/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=U-VOnLe-ZpfDpThMnOBzCxjnvUGLzDQFSt1ApQQzd8w%3D'
    bot_message = {
        'text' : text}
    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
    http_obj = Http()
    response = http_obj.request(
        uri=url,
        method='POST',
        headers=message_headers,
        body=dumps(bot_message),
    )


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    #print("USERNAME IN CEL", username)
    sender.add_periodic_task(
    crontab(minute=47, hour=11),
    remind_of_remaining_tasks.s())

@celery.task()
def remind_of_remaining_tasks():
    with sqlite3.connect(dbfilename) as conn:
        cur = conn.cursor()
        cur.execute(f"select * from {TASKS_TABLE}")
        rows = cur.fetchall()
        pending_tasks = []
        for row in rows:
            if not json.loads(row[4].lower()):
                pending_tasks.append(row[1])

        message = "Hey, the following tasks are still pending: \n"
        for task in pending_tasks:
            message += str(task) + "\n"
        message += "Please update the status on these tasks."
        send_messages_to_google_chat(message)
        conn.commit()
        cur.close()


if __name__ == '__main__':
    app.run(debug=True)
