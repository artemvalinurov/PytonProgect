import os
from flask import Flask, render_template_string
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

app = Flask(__name__)

# Получаем данные из переменных окружения
SENDER = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
RECIPIENT = os.getenv("EMAIL_RECEIVER")

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Secure Send</title></head>
<body style="text-align:center; padding-top:50px;">
    <form action="/send" method="post">
        <button style="padding:10px 20px;">Отправить письмо</button>
    </form>
    {% if message %}<p>{{ message }}</p>{% endif %}
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/send', methods=['POST'])
def send_mail():
    # Проверка: загрузились ли данные
    if not SENDER or not PASSWORD:
        return render_template_string(HTML_TEMPLATE, message="Ошибка: данные в .env не найдены!")

    msg = MIMEText("Это сообщение отправлено через переменные окружения.")
    msg['Subject'] = 'Безопасная отправка'
    msg['From'] = SENDER
    msg['To'] = RECIPIENT

    try:
        server = smtplib.SMTP('64.233.165.108', 587)
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECIPIENT, msg.as_string())
        server.quit()
        return render_template_string(HTML_TEMPLATE, message="Успешно отправлено!")
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, message=f"Ошибка: {e}")

if __name__ == '__main__':
    app.run(debug=True)
