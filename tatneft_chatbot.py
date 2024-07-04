from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import time
import gitlab
import telebot

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

app = ApplicationBuilder().token("<<TOKEN>>").build()

app.add_handler(CommandHandler("start", start))

app.run_polling() 
bot = telebot.TeleBot("<<TOKEN>>")

GITLAB_URL = 'https://gitlab.infra.tatneftm.ru/trainee-projects/trainee-gitlab-telebot'
GITLAB_TOKEN = '<<TOKEN>>'
CHAT_ID = '<<ID>>'

def get_merge_requests():
    gl = gitlab.Gitlab(GITLAB_URL, GITLAB_TOKEN)
    project = gl.projects.get(CHAT_ID)

    open_merge_requests = project.mergerequests.list(state='opened')

    return open_merge_requests

def check_merge_requests(bot):
    while True:
        merge_requests = get_merge_requests()
        
        for mr in merge_requests:
            bot.send_message(f'New merge request: {mr.title}')

        time.sleep(60) # Проверяем каждую минуту

def check_merge_request_status(bot):
    gl = gitlab.Gitlab(GITLAB_URL, GITLAB_TOKEN)
    project = gl.projects.get(CHAT_ID)
    
    merge_requests = get_merge_requests()
    merge_request_status = {mr.id: mr.state for mr in merge_requests}

    while True:
        for mr in merge_requests:
            new_mr_status = project.mergerequests.get(mr.id).state
            if new_mr_status != merge_request_status[mr.id]:
                bot.send_message(f'Merge request status changed: {mr.title}')

            merge_request_status[mr.id] = new_mr_status

        time.sleep(60) # Проверяем каждую минуту

class Bot:
    def send_message(self, message):
        print("message") # Здесь можно добавить отправку сообщения в чат


bot = Bot()
#check_merge_requests(bot)
