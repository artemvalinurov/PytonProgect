from flask import Flask, render_template, redirect
from data import db_session
from forms.mem import MemForm
from forms.user import RegisterForm, LoginForm
from data.users import User
from data.mems import Mem
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'movavi_school_monday'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)

@app.route('/')
def main_page():
    db_sess = db_session.create_session()
    mems = db_sess.query(Mem).all()
    return render_template('index.html', title='Главная', mems=mems)



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message='Пользователь с указанной почтой уже зарегистрирован')
        if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message='Такой никнейм уже занят')
        user = User(
            email=form.email.data,
            nickname=form.nickname.data,
            about=form.about.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # обращаемся к базе данных и ищем запись в таблице User, где nickname совпадает с тем, что ввёл пользователь в форму
        user = db_sess.query(User).filter(User.nickname == form.nickname.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect('/')
        return render_template('login.html', title='Авторизация', form=form,
                               message='Неправильный никнейм или пароль')
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_mem():
    form = MemForm()
    if form.validate_on_submit():
        file = form.photo.data
        ext = os.path.splitext(secure_filename(file.filename))[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file.save(os.path.join('static/uploads', filename))
        db_sess = db_session.create_session()
        mem = Mem(
            description=form.description.data,
            image=filename,
            creator=current_user.id
        )
        db_sess.add(mem)
        db_sess.commit()
        return redirect('/')
    return render_template('mem.html', title='Добавление фотографии', form=form)

@app.route('/photogalery')
def photogalery():
    db_sess = db_session.create_session()
    mems = db_sess.query(Mem).all()
    return render_template('photogalery.html', title='Фотогалерея', mems=mems)

def main():
    db_session.global_init('db/monday.db')
    app.run()

if __name__ == '__main__':
    main()