from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f'Your chat id is: {chat_id}')
async def gitlab_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = get_gitlab_project_info()
    if projects:
        response_text = ""
        for project_info in projects:
            response_text += (
                f"Project ID: {project_info['id']}\n"
                f"Name: {project_info['name']}\n"
                f"Description: {project_info['description']}\n"
                f"URL: {project_info['web_url']}\n\n"
            )
    else:
        response_text = "Не удалось получить информацию о проектах."

    await update.message.reply_text(response_text)

BOT_TOKEN = "BOT_TOKEN"
GITLAB_URL = 'https://gitlab.infra.tatneftm.ru/'
GITLAB_TOKEN = 'GITLAB_TOKEN'
CHAT_ID = ''

def get_gitlab_project_info():
    response = requests.get(f"https://gitlab.infra.tatneftm.ru/api/v4/projects?private_token={GITLAB_TOKEN}")
    # Отладочная информация
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as err:
        print(f"JSON decode error: {err}")
        return None

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("g", gitlab_info))
    app.run_polling()

if __name__ == '__main__':
    main()