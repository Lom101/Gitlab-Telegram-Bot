# trainee-gitlab-telebot 

Телеграмм-бот для Gitlab отслеживающий статусы MR

## Getting started

Чтобы запустить бота необходимо переименовать файл .env_example в .env и вписать в него:
BOT_TOKEN, GITLAB_URL, GITLAB_TOKEN, GITLAB_CLIENT_ID, GITLAB_CLIENT_SECRET
Два последних нужно взять в GitLab в настройках пользователя в разделе applications, 
добавив redirect_url=http://localhost:5000/gitlab/callback например
