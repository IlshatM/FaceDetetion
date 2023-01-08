# Обработка фотографий с лицами людей
#### Выполнил: Мухамедьяров Ильшат, 11-909

## Инструкция
### Определение лиц на фото
1. Создать бакет `itis-2022-2023-vvot05-photos`
2. Создать функцию `vvot16-face-detection`. Код в репозитории.
3. Создать триггер `vvot05-photo-trigger`, который активизируется при создании объекта в бакете **itis-2022-2023-vvot05-photos** с суффиксом `.jpg`. Обработчик - функция `vvot16-face-detection`.
### Вырезать лицо
1. Создать бакет `itis-2022-2023-vvot05-faces`
2. Создать очередь `vvot05-tasks`
3. Создать контейнер `vvot05-face-cut`
4. Зарегестрировать реестр. Докерфайл и код в папке `vvot05-face-cut`.
5. В редакторе контейнера `vvot05-face-cut` выбрать созданный нужный образ.
6. Создать триггер `vvot05-task-trigger`. Триггеро по очереди `vvot05-tasks`, обработчик - контейнер `vvot05-face-cut`
7. Создать YDB `vvot05-db-photo-face`.
8. Запустить скрипт в YDB `CREATE TABLE photo_faces(id Int64, name String, photo_key String, face_key String, user_chat_id Int64, PRIMARY KEY (id));`
### Настройка телеграмма
1. Создать публичную функцию `vvot05-boot`. Код в репозитории.
2. Создать API-gateway `vvot05-boot-gateway`. YML в папке `vvot05-boot`.
3. Зарегестрировать бота в bot_father в телеграмм.
4. Зарегистрировать функцию как вебхук `https://api.telegram.org/bot{my_bot_token}/setWebhook?url={url_to_send_updates_to}`. Достаточно просто вбить url в браузере.
