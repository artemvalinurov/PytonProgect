from flask_wtf import FlaskForm
from wtforms import PasswordField, EmailField, StringField, TextAreaField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo

class RegisterForm(FlaskForm):
    email = EmailField('Введите почту', validators=[DataRequired()])
    password = PasswordField('Придумайте пароль', validators=[DataRequired(), Length(min=8)])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo("password", message="Пароли не совпадают")])
    nickname = StringField('Придумайте никнейм', validators=[DataRequired()])
    about = TextAreaField('О себе', validators=[DataRequired()])
    # Новое поле: первый элемент — значение в БД, второй — текст в списке
    role = SelectField('Роль', choices=[('edit', 'Редактор'), ('root', 'Администратор')])
    submit = SubmitField('Отправить')

class LoginForm(FlaskForm):
    nickname = StringField('Введите никнейм', validators=[DataRequired()])
    password = PasswordField('Введите пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')