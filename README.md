# trainee-gitlab-telebot 

Телеграмм-бот для Gitlab отслеживающий статусы MR

## Getting started

Чтобы запустить бота необходимо переименовать файл .env_example в .env и вписать в него:
BOT_TOKEN, GITLAB_URL, GITLAB_TOKEN

```
cd existing_repo
git remote add origin https://gitlab.infra.tatneftm.ru/trainee-projects/trainee-gitlab-telebot.git
git branch -M main
git push -uf origin main
```