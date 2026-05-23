from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class MemForm(FlaskForm):
    description = TextAreaField('Описание фотографии', validators=[DataRequired()])
    photo = FileField('Загрузите файл с фотографией', validators=[DataRequired()])
    submit = SubmitField('Добавить')