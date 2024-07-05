from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext
import requests
import asyncio

# Глобальная переменная для хранения задачи
task = None
BOT_TOKEN = "BOT_TOKEN"
GITLAB_URL = 'https://gitlab.infra.tatneftm.ru/'
GITLAB_TOKEN = 'GITLAB_TOKEN'

# Функция, которая будет выполняться в бесконечном цикле
async def mr_check():
    while True:
        print("Checking MR...")
        await asyncio.sleep(5)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global task
    if task is None or task.done():
        task = asyncio.create_task(mr_check())
        await update.message.reply_text("Process started.")
    else:
        await update.message.reply_text("Process is already running.")
    await update.message.reply_text(f'Привет, {update.effective_user.first_name}! Я пока что глупый, но ты не сердись ;)')
async def stop(update: Update, context: CallbackContext) -> None:
    # update.message.reply_text('Остановлен бесконечный процесс.')
    # # Остановка всех задач asyncio (если это необходимо)
    # for task in asyncio.all_tasks():
    #     task.cancel()
    global task
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            await update.message.reply_text("Process was cancelled.")
        task = None
    else:
        await update.message.reply_text("No running process to stop.")
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f'Your chat id is: {chat_id}')
async def gitlab_projects_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = get_gitlab_projects_info()
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
async def gitlab_merges_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = get_gitlab_projects_info()
    response_text = ""
    if projects:
        for project_info in projects:
            url = project_info['_links']['merge_requests']
            # print(f"{url}")
            merge_requests = get_gitlab_merges_info(url)
            for mr in merge_requests:
                mr_id = mr.get('id')
                title = mr.get('title')
                description = mr.get('description', 'No description')
                state = mr.get('state')
                created_at = mr.get('created_at')
                updated_at = mr.get('updated_at')
                web_url = mr.get('web_url')

                response_text += (
                    f"Merge Request ID: {mr_id}\n"
                    f"Title: {title}\n"
                    f"Description: {description}\n"
                    f"State: {state}\n"
                    f"Created At: {created_at}\n"
                    f"Updated At: {updated_at}\n"
                    f"URL: {web_url}\n\n"
                )
    else:
        response_text = "Не удалось получить информацию о проектах."
    await update.message.reply_text(response_text)

def get_gitlab_projects_info():
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
def get_gitlab_merges_info(url: str):
    try:
        response = requests.get(f"{url}?private_token={GITLAB_TOKEN}")
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        merges = response.json()
        return merges
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as ve:
        print(f"Invalid JSON response: {ve}")
        return None

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("project", gitlab_projects_info))
    app.add_handler(CommandHandler("merge", gitlab_merges_info))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
