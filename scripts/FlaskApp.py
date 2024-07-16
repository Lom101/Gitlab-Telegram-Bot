from flask import Flask, request, redirect
import requests
import os
from dotenv import load_dotenv

from ConfigManager import ConfigManager

load_dotenv()
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_CLIENT_ID = os.getenv("GITLAB_CLIENT_ID")
GITLAB_CLIENT_SECRET = os.getenv("GITLAB_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

authorized_users = ConfigManager("../tokens.json")

app = Flask(__name__)

# Тестовая ручка
@app.route('/test', methods=['GET'])
def test():
    return "Это тестовая ручка!", 200

@app.route('/gitlab/callback')
def gitlab_callback():
    code = request.args.get('code')
    chat_id = request.args.get('state') # при отправке request в state мы зашиваем chat_id

    print(code)
    print(chat_id)

    token_url = f'{GITLAB_URL}/oauth/token'
    token_data = {
        'client_id': GITLAB_CLIENT_ID,
        'client_secret': GITLAB_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }
    token_response = requests.post(token_url, data=token_data).json()
    access_token = token_response.get('access_token')

    if access_token:
        print("Авторизация прошла успешно!")
        # добавляем в базу данных chat_id и токен пользователя
        authorized_users.add_value(str(chat_id), str(access_token))
        return "Авторизация прошла успешно! Вы можете вернуться в Telegram."
    else:
        print("Ошибка авторизации. Попробуйте еще раз.")
        return "Ошибка авторизации. Попробуйте еще раз."


if __name__ == '__main__':
    app.run(port=5000)