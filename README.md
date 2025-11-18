# Video Gallery

Мощно приложение за управление на видео колекция с YouTube интеграция, локални видео файлове, AI анализ и напреднало търсене в субтитри.

## Възможности

### 🎬 Видео Управление
- **YouTube Интеграция**: Импортирайте видеа от YouTube по URL или синхронизирайте запазените видеа
- **Локални Видеа**: Автоматично сканиране и индексиране на локални видео файлове
- **Колекции (Boards)**: Организирайте видеата в персонализирани колекции
- **Любими**: Маркирайте важни видеа като любими

### 🔍 Напреднало Търсене
- Търсене по заглавие, описание и тагове
- **Търсене в субтитри**: Намерете точния момент във видеото, където се споменава търсената дума
- Филтриране по източник (YouTube/Local)
- Сортиране по различни критерии

### 📝 Субтитри
- Автоматично изтегляне на субтитри от YouTube
- Извличане на вградени субтитри от локални файлове
- Поддръжка на SRT и WebVTT формати
- Търсене в субтитри с timestamp навигация

### 🤖 AI Функционалности (LM Studio)
- Автоматично генериране на резюме на видео съдържание
- Интелигентно създаване на тагове
- Категоризация на видеата
- Извличане на ключови точки

### 📊 Статистика
- Следене на гледанията
- История на гледане
- Общ брой видеа и колекции

## Технологичен Стек

### Backend
- **Flask**: Python уеб framework
- **SQLite**: База данни
- **OpenCV**: Видео обработка и генериране на thumbnails
- **yt-dlp**: YouTube видео информация и изтегляне
- **YouTube API**: Официален API за YouTube данни
- **FFmpeg**: Разширена видео/субтитри обработка

### Frontend
- **Vanilla JavaScript**: Без framework зависимости
- **CSS Grid/Flexbox**: Модерен responsive дизайн
- **Dark Theme**: Приятен за очите тъмен дизайн

## Инсталация

### Изисквания
- Python 3.8+
- FFmpeg (за обработка на видеа и субтитри)
- YouTube API Key (опционално, за YouTube интеграция)
- LM Studio (опционално, за AI функционалности)

### Стъпка 1: Клониране на репозиторито
```bash
git clone https://github.com/yourusername/video-gallery.git
cd video-gallery
```

### Стъпка 2: Инсталиране на зависимости

#### Python зависимости
```bash
pip install -r requirements.txt
```

#### FFmpeg
**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Изтеглете от [ffmpeg.org](https://ffmpeg.org/download.html) и добавете в PATH

### Стъпка 3: Конфигурация

#### YouTube API Key (Опционално)
1. Посетете [Google Cloud Console](https://console.cloud.google.com/)
2. Създайте нов проект
3. Активирайте YouTube Data API v3
4. Създайте API credentials (API Key)
5. Задайте environment variable:

```bash
export YOUTUBE_API_KEY="your-api-key-here"
```

#### LM Studio (Опционално)
1. Изтеглете и инсталирайте [LM Studio](https://lmstudio.ai/)
2. Заредете модел (препоръчително: mistral-7b или подобен)
3. Стартирайте локалния сървър (по подразбиране на порт 1234)
4. При необходимост променете URL-а:

```bash
export LM_STUDIO_URL="http://localhost:1234"
```

### Стъпка 4: Стартиране на приложението

```bash
cd backend
python app.py
```

Приложението ще бъде достъпно на: `http://localhost:5000`

## Структура на проекта

```
video-gallery/
├── backend/
│   ├── app.py                 # Flask сървър и API endpoints
│   ├── database.py            # SQLite база данни
│   ├── youtube_manager.py     # YouTube API интеграция
│   ├── video_processor.py     # Обработка на локални видеа
│   ├── subtitle_manager.py    # Управление на субтитри
│   └── ai_analyzer.py         # AI анализ чрез LM Studio
├── frontend/
│   ├── index.html             # HTML структура
│   ├── app.js                 # JavaScript логика
│   └── styles.css             # CSS стилове
├── videos/                    # Папка за локални видеа
├── thumbnails/                # Генерирани thumbnails
├── requirements.txt           # Python зависимости
└── README.md                  # Документация
```

## Използване

### Импортиране на YouTube видео
1. Кликнете "Import URL" в header-а
2. Поставете YouTube URL
3. Кликнете "Импортирай"

### Синхронизация на YouTube колекция
1. Конфигурирайте YouTube API Key
2. Кликнете "Sync YouTube"
3. Приложението ще импортира всички харесани видеа

### Сканиране на локални видеа
1. Поставете видео файлове в `videos/` папката
2. Кликнете "Scan Local"
3. Приложението ще индексира всички видеа и генерира thumbnails

### Създаване на колекция
1. Кликнете "+" бутона до "Колекции" в sidebar-а
2. Въведете име и описание
3. Изберете цвят и икона
4. Кликнете "Създай"

### AI Анализ
1. Отворете видео
2. Кликнете "🤖 AI Анализ"
3. Изчакайте генерирането на резюме и тагове

### Търсене в субтитри
1. Отворете видео със субтитри
2. Използвайте полето за търсене в субтитрите
3. Кликнете на намерен резултат за преход към момента във видеото

## API Endpoints

### Videos
- `GET /api/videos` - Получи всички видеа
- `GET /api/videos/<id>` - Получи конкретно видео
- `POST /api/videos/<id>/watch` - Маркирай като гледано
- `POST /api/videos/<id>/favorite` - Toggle favorite статус
- `DELETE /api/videos/<id>` - Изтрий видео

### YouTube
- `POST /api/youtube/sync` - Синхронизирай YouTube видеа
- `POST /api/youtube/import` - Импортирай видео по URL

### Local Videos
- `POST /api/videos/scan-local` - Сканирай локални видеа
- `GET /api/videos/<id>/stream` - Stream локално видео

### Search
- `GET /api/search?q=<query>` - Търси видеа и субтитри

### Boards
- `GET /api/boards` - Получи всички boards
- `POST /api/boards` - Създай нов board
- `POST /api/boards/<id>/videos` - Добави видео към board

### AI
- `POST /api/ai/analyze/<video_id>` - Анализирай видео с AI
- `GET /api/ai/status` - Провери AI статус

## Конфигурация

### Environment Variables

```bash
# YouTube API Key (опционално)
export YOUTUBE_API_KEY="your-api-key"

# LM Studio URL (по подразбиране: http://localhost:1234)
export LM_STUDIO_URL="http://localhost:1234"
```

### Съвети за оптимизация

1. **FFmpeg производителност**: За по-бързо обработване използвайте hardware acceleration
2. **LM Studio**: Изберете по-малък модел за по-бързи отговори
3. **Thumbnails**: Генерират се автоматично при сканиране
4. **Database**: SQLite е достатъчно бързо за хиляди видеа

## Отстраняване на проблеми

### FFmpeg не е намерен
```bash
# Проверете дали FFmpeg е инсталиран
ffmpeg -version

# Linux: Добавете към PATH
export PATH=$PATH:/usr/local/bin
```

### YouTube API квота изчерпана
- YouTube API има дневен лимит от 10,000 units
- Използвайте `yt-dlp` fallback (работи без API key)

### LM Studio не се свързва
```bash
# Проверете дали LM Studio сървърът работи
curl http://localhost:1234/v1/models

# Стартирайте Local Server от LM Studio интерфейса
```

### Субтитрите не се зареждат
- Уверете се, че видеото има налични субтитри
- Проверете форматът (SRT/VTT)
- За YouTube: не всички видеа имат субтитри

## Допринасяне

Приемаме contributions! Моля:
1. Fork-нете репозиторито
2. Създайте feature branch
3. Commit-нете промените
4. Push-нете към branch-а
5. Отворете Pull Request

## Лиценз

MIT License - виж LICENSE файла за детайли

## Автор

Създадено с ❤️ за любителите на видео съдържание

## Бъдещи функционалности

- [ ] Playlist поддръжка
- [ ] Видео анотации и bookmarks
- [ ] Export/Import на колекции
- [ ] Multi-user поддръжка
- [ ] Mobile приложение
- [ ] Video transcoding
- [ ] Podcast RSS feeds
- [ ] Collaboration features
