# Negotiation Chat Service

## Требования

* Python 3.10+
* Credentials для GigaChat API

Проверить версию Python:

```powershell
python --version
```

---

## 1. Клонирование проекта

```powershell
git clone <URL_REPOSITORY>
cd chat-service
```

---

## 2. Создание виртуального окружения

```powershell
python -m venv .venv
```

Активация в Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

После активации в терминале должно появиться:

```text
(.venv)
```

---

## 3. Установка зависимостей

```powershell
pip install -r requirements.txt
```

---

## 4. Настройка GigaChat

Создать в корне проекта файл:

```text
.env
```

Добавить:

```env
GIGACHAT_CREDENTIALS=YOUR_CREDENTIALS
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat-2-Pro
GIGACHAT_VERIFY_SSL_CERTS=false
```

Вместо `YOUR_CREDENTIALS` указать реальные credentials GigaChat.

> Файл `.env` не нужно добавлять в Git.

---

# Запуск

Для работы необходимо запустить **два сервера**.

## 5. Запуск Chat Service

Открыть первый терминал в корне проекта:

```powershell
uvicorn src.chat_service.api:app --reload
```

Chat Service будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Проверить работу:

```text
http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok"
}
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## 6. Запуск Web UI

Открыть **второй терминал**.

Перейти в папку `test-ui`:

```powershell
cd test-ui
```

Запустить HTTP-сервер:

```powershell
python -m http.server 5500
```

Открыть в браузере:

```text
http://127.0.0.1:5500
```

---

## Итог

Должны быть запущены:

**Терминал 1:**

```powershell
uvicorn src.chat_service.api:app --reload
```

**Терминал 2:**

```powershell
cd test-ui
python -m http.server 5500
```

После этого открыть:

```text
http://127.0.0.1:5500
```
