# CROUS watcher → Telegram

Проверяет trouverunlogement.lescrous.fr каждые ~5 минут на серверах GitHub
и сразу присылает сообщение в Telegram о каждом новом предложении.
Ноутбук может быть выключен.

## 1. Telegram-бот (2 минуты)
1. В Telegram откройте **@BotFather** → `/newbot` → придумайте имя → получите **токен** (`123456:ABC...`).
2. Откройте своего нового бота и нажмите **Start** (иначе он не сможет вам писать).
3. Откройте **@userinfobot** → он покажет ваш **ID** (число) — это `TELEGRAM_CHAT_ID`.

## 2. Ссылка на поиск CROUS
1. Зайдите на https://trouverunlogement.lescrous.fr, выберите город/зону на карте, фильтры (цена, тип).
2. Нажмите поиск и скопируйте **адрес из браузера**, например
   `https://trouverunlogement.lescrous.fr/tools/42/search?bounds=2.22_48.90_2.47_48.81`
3. Можно несколько ссылок (разные зоны) — через пробел.

## 3. GitHub
1. Создайте аккаунт на github.com (бесплатно) → **New repository** → имя `crous-watch`,
   **Public** → Create (у публичных репозиториев Actions бесплатны без лимита;
   токен и ID всё равно хранятся скрыто в Secrets).
2. **Add file → Upload files** → загрузите все файлы из архива
   (важно: папка `.github/workflows/crous.yml` тоже; если веб-загрузка
   пропускает скрытую папку — создайте файл вручную: *Add file → Create new file*,
   имя `.github/workflows/crous.yml`, вставьте содержимое).
3. **Settings → Secrets and variables → Actions**:
   - вкладка *Secrets* → New: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`
   - вкладка *Variables* → New: `CROUS_URLS` = ваша ссылка (или несколько через пробел)
   - (необязательно) Variable `CROUS_KEYWORDS` = названия общаг через `;`,
     например `Jean Zay; Résidence Lourcine`. Пусто = все предложения из поиска.
4. **Actions** → включите workflows, если спросит → *CROUS watcher* → **Run workflow**
   для проверки. При первом запуске придут все предложения, которые доступны сейчас;
   дальше — только новые.

## Полезно знать
- GitHub запускает расписание «каждые 5 минут», но на практике бывают задержки 5–15 мин.
  Для более точного ритма: бесплатный **cron-job.org** может каждую минуту дёргать
  `POST https://api.github.com/repos/<user>/crous-watch/actions/workflows/crous.yml/dispatches`
  с телом `{"ref":"main"}` и заголовком `Authorization: Bearer <fine-grained token с правом Actions: write>`.
- Если предложение исчезло и снова появилось — придёт повторное уведомление.
- Если сайт CROUS изменит вёрстку и проверка упадёт, GitHub пришлёт письмо об ошибке.
- Приватный репозиторий: 2000 бесплатных минут/месяц — при запуске каждые 5 мин
  этого может не хватить; **публичный** репозиторий — без лимита (токены всё равно
  остаются скрытыми в Secrets).
