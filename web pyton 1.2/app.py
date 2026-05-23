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

# 1. Загружаем переменные из скрытого файла .env в самом начале
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'movavi_school_monday'

login_manager = LoginManager()
login_manager.init_app(app)


# 2. Чистая функция отправки писем (использует твой рабочий IP-адрес)
def send_email_notification(filename, nickname, recipients_list):
    SENDER = os.getenv("EMAIL_USER")
    PASSWORD = os.getenv("EMAIL_PASS")

    if not SENDER or not PASSWORD:
        print("Ошибка: EMAIL_USER или EMAIL_PASS не настроены в .env!")
        return

    if not recipients_list:
        print("Нет других пользователей для отправки уведомлений.")
        return

    # Формируем текст письма
    body = f"Пользователь {nickname} добавил новую фотографию на сайт семейных походов.\nИмя файла: {filename}"
    msg = MIMEText(body)
    msg['Subject'] = '📸 Новое фото в галерее!'
    msg['From'] = SENDER
    msg['To'] = ", ".join(recipients_list)  # Объединяем список почт через запятую

    try:
        # Твой проверенный IP для обхода ошибки DNS
        server = smtplib.SMTP('64.233.165.108', 587)
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, recipients_list, msg.as_string())
        server.quit()
        print(f"Уведомление успешно отправлено для {len(recipients_list)} пользователей!")
    except Exception as e:
        print(f"Не удалось отправить уведомление: {e}")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


# --- МАРШРУТЫ САЙТА ---


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


# 3. Маршрут ДОБАВЛЕНИЯ фотографии + автоматическая РАССЫЛКА
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

        # Логика рассылки
        users_emails = db_sess.query(User.email).filter(User.id != current_user.id).all()
        recipients = [email[0] for email in users_emails if email[0]]
        send_email_notification(filename, current_user.nickname, recipients)

        return redirect('/')
        
    return render_template('mem.html', title='Добавление фотографии', form=form)


# ОДИНАРНЫЙ МАРШРУТ УДАЛЕНИЯ (С РОЛЯМИ)
@app.route('/delete/<int:mem_id>', methods=['POST'])
@login_required
def delete_mem(mem_id):
    db_sess = db_session.create_session()
    mem = db_sess.get(Mem, mem_id)

    if not mem:
        return "Фотография не найдена", 404

    # Удаляет автор ИЛИ root
    if str(mem.creator) == str(current_user.id) or current_user.role == "root":
        try:
            file_path = os.path.join('static/uploads', mem.image)
            if os.path.exists(file_path):
                os.remove(file_path)

            db_sess.delete(mem)
            db_sess.commit()
            print(f"Фото {mem_id} успешно удалено!")
        except Exception as e:
            db_sess.rollback()
            print(f"Ошибка при удалении: {e}")
            return "Произошла ошибка при удалении файла", 500

        return redirect('/photogalery')
    else:
        return "У вас нет прав на удаление этой фотографии", 403


# ОДИНАРНЫЙ МАРШРУТ РЕДАКТИРОВАНИЯ (С РОЛЯМИ)
@app.route('/edit_description/<int:mem_id>', methods=['POST'])
@login_required
def edit_description(mem_id):
    db_sess = db_session.create_session()
    mem = db_sess.get(Mem, mem_id)
    
    if not mem:
        return "Фотография не найдена", 404
        
    # Редактирует автор ИЛИ root
    if str(mem.creator) == str(current_user.id) or current_user.role == "root":
        new_text = request.form.get('new_description')
        if new_text:
            try:
                mem.description = new_text.strip()
                db_sess.commit()
                print(f"Подпись к фото {mem_id} успешно изменена!")
            except Exception as e:
                db_sess.rollback()
                print(f"Ошибка при сохранении: {e}")
                return "Произошла ошибка при сохранении данных", 500
                
            return redirect('/photogalery')
        else:
            return "Описание не может быть пустым", 400
    else:
        return "У вас нет права на редактирование этой фотографии", 403


@app.route('/photogalery')
def photogalery():
    db_sess = db_session.create_session()
    mems = db_sess.query(Mem).all()
    return render_template('photogalery.html', title='Фотогалерея', mems=mems)


def main():
    db_session.global_init('db/monday.db')
    app.run()

# Автоматическое закрытие сессий после каждого запроса
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.create_session().close()


if __name__ == '__main__':
    main()