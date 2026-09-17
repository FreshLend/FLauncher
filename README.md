# FLauncher

[English version](README.EN.md)

Лаунчер для [VoxelCore](https://github.com/MihailRis/VoxelCore), написанный на Python. Имеет полную кастомизацию — от цветов до расположения интерфейса.

## Особенности

- Кроссплатформенность (Windows / macOS / Linux)
- Работа в оффлайн-режиме
- Discord Rich Presence
- Интеграция сторонних GitHub-репозиториев
- Страница модов с интеграцией VoxelWorld API
- Полностью кастомизируемые темы

## Установка библиотек

```
pip install -r requirements.txt
```

## Сборка

```
pip install pyinstaller
pyinstaller build.spec
```

## Структура проекта

```
src/
├── main.py                     точка входа
├── logging_setup.py            настройка логирования
├── settings_manager.py         сохранение настроек и путей
├── thread_manager.py           пул потоков
├── i18n.py                     локализация
├── github_client.py            запросы к GitHub API
├── version_manager.py          управление версиями VoxelCore
├── download_manager.py         скачивание и распаковка
├── download_worker.py          QThread-обёртка для скачивания
├── discord_rpc.py              интеграция с Discord
├── themes.py                   система тем
├── update_checker.py           проверка обновлений лаунчера
├── ui_mainwindow.py            главное окно
├── ui_components.py            верхнеуровневые компоненты UI
├── utils/                      утилиты
│   ├── __init__.py             реэкспорт публичных функций
│   ├── constants.py            VERSION, MAIN_REPO, MAX_LOAD
│   ├── paths.py                resource_path
│   ├── platform.py             определение платформы и паттернов
│   └── archive.py              safe_extract_zip
├── ui/
│   ├── __init__.py             реэкспорт публичных функций
│   ├── widgets.py              кастомные виджеты
│   ├── images/                 иконки и фоны
│   ├── langs/                  языковые файлы (JSON)
│   └── themes/                 встроенные темы
│       └── FLauncher/
│           ├── tlauncher.json
│           ├── legacy.json
│           └── dark.legacy.json
└── flmods/
    ├── api.py                  VoxelWorld API
    ├── workers.py              воркеры FLMODS
    └── catalog.py              UI каталога модов
```

---

## Система тем

Темы — это JSON-файлы, которые описывают внешний вид, цвета, размеры, шрифты, размытие и расположение всех элементов лаунчера. Одна тема — один JSON, плюс опциональные варианты через `<base>.<variant>.json`.

### Где лежат темы

**Встроенные** (в бандле лаунчера):

```
<bundle>/themes/FLauncher/
    tlauncher.json
    legacy.json
    dark.legacy.json
```

**Пользовательские** (в папке данных ОС):

| ОС | Путь |
|---|---|
| Windows | `%APPDATA%\com.flauncher.app\FLauncher\themes\` |
| macOS | `~/Library/Application Support/com.flauncher.app/FLauncher/themes/` |
| Linux | `~/.config/com.flauncher.app/FLauncher/themes/` |

Кнопка «Открыть папку тем» в настройках FLauncher открывает эту папку в файловом менеджере.

Пользовательские темы имеют приоритет над встроенными с тем же именем файла.

### Как работают файлы в папке темы

Внутри папки может быть **несколько независимых тем** и **вариантов**:

```
themes/FLauncher/
    tlauncher.json          # тема "TLauncher"
    legacy.json             # тема "Legacy Launcher"
    dark.legacy.json        # вариант "Dark" для темы "Legacy Launcher"
    ui/                     # общие иконки и фон для всех тем в этой папке
        background.png
        FLM.png
        reload.png
        folder.png
        settings.png
        legacy-FLM.png
        legacy-reload.png
        legacy-folder.png
        legacy-settings.png
```

- `<name>.json` — самостоятельная тема.
- `<variant>.<name>.json` — **вариант** темы `<name>`. Наследует все ключи базовой темы и переопределяет только указанные. В UI отображается под базовой с отступом.
- Все PNG и другие ресурсы лежат в `<папка темы>/ui/`. Пути в JSON указываются **относительно этой папки** — например, `"background": "ui/background.png"` означает `<папка темы>/ui/background.png`.

### Как создать свою тему

1. Открой настройки FLauncher → «Открыть папку тем».
2. Создай новую папку, например `mytheme/` (имя папки произвольное).
3. Скопируй туда `tlauncher.json` из `themes/FLauncher/` — это стартовая точка со всеми ключами.
4. Переименуй файл в `mytheme.json`.
5. Поменяй `"name"` на своё название — оно отображается в списке тем.
6. Отредактируй цвета, шрифты, layout.
7. Если нужны свои иконки/фон — создай рядом папку `mytheme/ui/` и положи туда PNG. В JSON укажи пути вида `"ui/background.png"`.
8. Сохрани. В настройках нажми «↻» рядом с выбором темы — тема появится в списке.

### Как создать вариант темы

Внутри папки темы рядом с `mytheme.json` создай `variant.mytheme.json`. В нём укажи только то, что отличается от `mytheme.json`:

```json
{
  "name": "variant",
  "bar_bg": "rgba(18, 18, 24, 71)",
  "bar_text": "#e6e6ea",
  "input_bg": "#1e1e26",
  "input_text": "#e6e6ea",
  "play_bg": "#2a2a35",
  "play_text": "#e6e6ea"
}
```

Всё остальное (`layout`, `icons`, `background`, размеры шрифтов, отступы) подтянется из `mytheme.json`. В списке тем `mytheme` появится под `variant` с отступом.

### Ключи темы

Полный список всех ключей с дефолтными значениями смотри в `themes.py` — переменная `FALLBACK_THEME`.

Основные группы:

**Layout** — расположение всех элементов:

```json
"layout": {
  "mode": "bar",              // "bar" — панель снизу/сверху, "centered" — панель по центру
  "bar_position": "bottom",   // "bottom" или "top"
  "bar_height": 90,
  "hide_info": false,
  "hide_releases": false,
  "release_scroll": [20, 10, 800, -20],
  "info_panel": [830, 10, 250, -20],
  "nick_input": [10, 20, 200, 60],
  "version_combo": [220, 20, 300, 60],
  "play_button": [530, 20, 300, 60],
  "flm_button": [835, 20, 60, 60],
  "reload_button": [895, 20, 60, 60],
  "folder_button": [965, 20, 60, 60],
  "settings_button": [1035, 20, 60, 60],
  "progress_bar": [10, 3, -20, 15],
  "cancel_button": [1010, 3, 80, 15]
}
```

Каждый элемент — массив `[x, y, w, h]`. Отрицательные `w`/`h` означают «отступ от правого/нижнего края родителя». Например, `[10, 3, -20, 15]` — ширина = ширина родителя минус 20.

**Colors** — цвета в формате `#RRGGBB`, `#RRGGBBAA`, `rgba(r, g, b, a)` или `rgb(r, g, b)`.

**Blur** — размытие любой панели:

```json
"bar_blur": 8,               // 0 = выключено, 8 = лёгкое, 20 = сильное
"settings_blur": 8,
"release_panel_blur": 0,
"info_panel_blur": 0,
"flmods_blur": 0
```

Если `*_blur > 0`, панель становится прозрачной по QSS, а под ней рисуется размытый кусок фонового изображения с наложенным цветом `*_bg`.

**Icons** — кастомные иконки:

```json
"icons": {
  "flm": "ui/FLM.png",
  "reload": "ui/reload.png",
  "folder": "ui/folder.png",
  "settings": "ui/settings.png"
}
```

Если ключ не указан или файл не найден — берётся дефолтная иконка из `ui/images/`.

**Background** — свой фон окна:

```json
"background": "ui/background.png"
```

Рекомендуемый размер 1100×650 (совпадает с `setFixedSize` главного окна).

### Переопределение переводов в теме

Любая тема может переопределять строки локализации — полностью или частично. Для этого в JSON темы добавь блок `texts`:

```json
{
  "name": "My Theme",
  "texts": {
    "ru_RU": {
      "button.play": "Запустить",
      "info.title": "МОЙ ЛАУНЧЕР",
      "info.subtitle": "ЛАУНЧЕР ДЛЯ VOXELCORE"
    },
    "en_US": {
      "button.play": "Launch",
      "info.title": "MY LAUNCHER",
      "info.subtitle": "LAUNCHER FOR VOXELCORE"
    }
  }
}
```

Ключи — те же, что и в файлах `ui/langs/*.json`. Указывать можно только те строки, которые отличаются; остальные подтянутся из языкового файла.

Что можно переопределять:

- Тексты интерфейса — `button.play`, `info.title`, `settings.title`, `dialog.ok` и т. д.
- Плейсхолдеры — `input.nick_placeholder`, `search.placeholder`.
- Строки подсказок и описаний.

Что **нельзя** переопределять через тему:

- Плюральные формы (`time.years_ago` и др.) — работают только из языковых файлов.
- Список месяцев (`date.months`) — тоже только из языковых файлов.

Вариант темы (`dark.mytheme.json`) может содержать свой блок `texts` — он **сливается** с текстами базовой темы, а не заменяет их. Например, если в `mytheme.json` есть `texts.ru_RU.button.play`, а в варианте — только `texts.ru_RU.info.title`, то в варианте будут оба ключа.

Переопределения применяются вместе с загрузкой языка и темы — при смене языка остаются активны переопределения текущей темы для нового языка, если такие есть.

### Как применить изменения

Правки в JSON применяются по кнопке **«↻»** рядом с выбором темы в настройках FLauncher. Кнопка перечитывает файлы с диска, пересобирает список и перерисовывает интерфейс. Перезапуск лаунчера не нужен.