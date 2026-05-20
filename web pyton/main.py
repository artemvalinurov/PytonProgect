import os
import smtplib
import uuid
from email.mime.text import MIMEText

from data import db_session
from data.mems import Mem
from data.users import User
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from forms.mem import MemForm
from forms.user import LoginForm, RegisterForm
from werkzeug.utils import secure_filename

# Загружаем переменные из .env в самом начале
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'movavi_school_monday'

login_manager = LoginManager()
login_manager.init_app(app)


# Выносим чистую функцию отправки уведомления наружу
def send_email_notification(filename, nickname, recipients_list):
    SENDER = os.getenv("EMAIL_USER")
    PASSWORD = os.getenv("EMAIL_PASS")

    # Проверяем только отправителя и пароль (получатели придут из базы)
    if not SENDER or not PASSWORD:
        print("Ошибка: EMAIL_USER или EMAIL_PASS не настроены в .env!")
        return

    if not recipients_list:
        print("Нет других пользователей для отправки уведомлений.")
        return

    # Текст сообщения
    body = f"Пользователь {nickname} добавил новую фотографию на сайт семейных походов.\nИмя файла: {filename}"
    msg = MIMEText(body)
    msg['Subject'] = '📸 Новое фото в галерее!'
    msg['From'] = SENDER
    # По правилам хорошего тона при массовой рассылке адреса лучше скрывать в BCC (скрытая копия),
    # либо отправлять каждому лично. Сделаем отправку списком для простоты:
    msg['To'] = ", ".join(recipients_list) 

    try:
        server = smtplib.SMTP('64.233.165.108', 587)
        server.starttls()
        server.login(SENDER, PASSWORD)
        # Отправляем массив адресов recipients_list
        server.sendmail(SENDER, recipients_list, msg.as_string())
        server.quit()
        print(f"Уведомление успешно отправлено для {len(recipients_list)} пользователей!")
    except Exception as e:
        print(f"Не удалось отправить уведомление: {e}")


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
            return render_template(
                'register.html',
                title='Регистрация',
                form=form,
                message='Пользователь с указанной почтой уже зарегистрирован',
            )
        if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
            return render_template(
                'register.html',
                title='Регистрация',
                form=form,
                message='Такой никнейм уже занят',
            )
        user = User(
            email=form.email.data,
            nickname=form.nickname.data,
            about=form.about.data,
            role=form.role.data,
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
        user = (
            db_sess.query(User)
            .filter(User.nickname == form.nickname.data)
            .first()
        )
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect('/')
        return render_template(
            'login.html',
            title='Авторизация',
            form=form,
            message='Неправильный никнейм или пароль',
        )
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
        ext = os.path.splitext(secure_filename(file.filename))[1] # Исправил небольшую опечатку с индексом [1], которая была в прошлый раз
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

        # --- НАЧАЛО ЛОГИКИ РАССЫЛКИ ---
        
        # Запрашиваем из таблицы User только поле email у тех, чей ID НЕ равен ID текущего пользователя
        users_emails = db_sess.query(User.email).filter(User.id != current_user.id).all()
        
        # SQLAlchemy возвращает список кортежей вида [('email1@mail.ru',), ('email2@gmail.com',)], 
        # превращаем его в обычный плоский список строк:
        recipients = [email[0] for email in users_emails if email[0]]
        
        # Отправляем уведомление, передавая список получателей
        send_email_notification(filename, current_user.nickname, recipients)
        
        # --- КОНЕЦ ЛОГИКИ РАССЫЛКИ ---

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
