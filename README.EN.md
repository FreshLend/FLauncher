# FLauncher

[Русская версия](README.md)

A launcher for [VoxelCore](https://github.com/MihailRis/VoxelCore), written in Python. Fully customizable — from colors to UI layout.

## Features

- Cross-platform (Windows / macOS / Linux)
- Offline mode
- Discord Rich Presence
- Integration of third-party GitHub repositories
- Mods page with VoxelWorld API integration
- Fully customizable themes

## Installing dependencies

```
pip install -r requirements.txt
```

## Building

```
pip install pyinstaller
pyinstaller build.spec
```

## Project structure

```
src/
├── main.py                     entry point
├── logging_setup.py            logging setup
├── settings_manager.py         settings and paths
├── thread_manager.py           thread pool
├── i18n.py                     localization
├── github_client.py            GitHub API client
├── version_manager.py          VoxelCore version management
├── download_manager.py         download and unpack
├── download_worker.py          QThread wrapper for downloads
├── discord_rpc.py              Discord integration
├── themes.py                   theme system
├── update_checker.py           launcher update checker
├── ui_mainwindow.py            main window
├── ui_components.py            high-level UI components
├── utils/                      utilities
│   ├── __init__.py             public re-exports
│   ├── constants.py            VERSION, MAIN_REPO, MAX_LOAD
│   ├── paths.py                resource_path
│   ├── platform.py             platform detection and patterns
│   └── archive.py              safe_extract_zip
├── ui/
│   ├── __init__.py             public re-exports
│   ├── widgets.py              custom widgets
│   ├── images/                 icons and backgrounds
│   ├── langs/                  language files (JSON)
│   └── themes/                 built-in themes
│       └── FLauncher/
│           ├── tlauncher.json
│           ├── legacy.json
│           └── dark.legacy.json
└── flmods/
    ├── api.py                  VoxelWorld API
    ├── workers.py              FLMODS workers
    └── catalog.py              mods catalog UI
```

---

## Theme system

Themes are JSON files that describe appearance, colors, sizes, fonts, blur, and layout of every launcher element. One theme — one JSON, plus optional variants via `<base>.<variant>.json`.

### Where themes live

**Built-in** (inside the launcher bundle):

```
<bundle>/themes/FLauncher/
    tlauncher.json
    legacy.json
    dark.legacy.json
```

**User-defined** (in the OS data folder):

| OS | Path |
|---|---|
| Windows | `%APPDATA%\com.flauncher.app\FLauncher\themes\` |
| macOS | `~/Library/Application Support/com.flauncher.app/FLauncher/themes/` |
| Linux | `~/.config/com.flauncher.app/FLauncher/themes/` |

The "Open themes folder" button in FLauncher settings opens this folder in the file manager.

User themes override built-in themes with the same file name.

### How files in a theme folder work

A folder may contain **multiple independent themes** and **variants**:

```
themes/FLauncher/
    tlauncher.json          # theme "TLauncher"
    legacy.json             # theme "Legacy Launcher"
    dark.legacy.json        # variant "Dark" of theme "Legacy Launcher"
    ui/                     # shared icons and background for all themes in this folder
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

- `<name>.json` — a standalone theme.
- `<variant>.<name>.json` — a **variant** of the `<name>` theme. Inherits all keys from the base theme and overrides only specified ones. Shown in the UI indented under the base theme.
- All PNGs and other assets live in `<theme folder>/ui/`. Paths in JSON are **relative to this folder** — e.g. `"background": "ui/background.png"` means `<theme folder>/ui/background.png`.

### Creating your own theme

1. Open FLauncher settings → "Open themes folder".
2. Create a new folder, e.g. `mytheme/` (folder name is arbitrary).
3. Copy `tlauncher.json` from `themes/FLauncher/` into it — it's a starting point with all keys.
4. Rename the file to `mytheme.json`.
5. Change `"name"` to your own — it's shown in the theme list.
6. Edit colors, fonts, layout.
7. If you need custom icons/background — create a `mytheme/ui/` folder next to it and put PNGs there. In JSON, use paths like `"ui/background.png"`.
8. Save. In settings, click "↻" next to the theme selector — the theme appears in the list.

### Creating a theme variant

Inside the theme folder, next to `mytheme.json`, create `variant.mytheme.json`. Specify only what differs from `mytheme.json`:

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

Everything else (`layout`, `icons`, `background`, font sizes, paddings) is inherited from `mytheme.json`. In the theme list, `variant` appears indented under `mytheme`.

### Theme keys

The full list of all keys with default values is in `themes.py` — variable `FALLBACK_THEME`.

Main groups:

**Layout** — placement of all elements:

```json
"layout": {
  "mode": "bar",              // "bar" — bottom/top panel, "centered" — centered panel
  "bar_position": "bottom",   // "bottom" or "top"
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

Each element is an array `[x, y, w, h]`. Negative `w`/`h` mean "offset from the right/bottom edge of the parent". For example, `[10, 3, -20, 15]` — width = parent width minus 20.

**Colors** — colors in `#RRGGBB`, `#RRGGBBAA`, `rgba(r, g, b, a)` or `rgb(r, g, b)` format.

**Blur** — panel blur:

```json
"bar_blur": 8,               // 0 = disabled, 8 = light, 20 = strong
"settings_blur": 8,
"release_panel_blur": 0,
"info_panel_blur": 0,
"flmods_blur": 0
```

If `*_blur > 0`, the panel becomes transparent via QSS, and a blurred slice of the background image is drawn underneath with the `*_bg` color overlaid.

**Icons** — custom icons:

```json
"icons": {
  "flm": "ui/FLM.png",
  "reload": "ui/reload.png",
  "folder": "ui/folder.png",
  "settings": "ui/settings.png"
}
```

If a key is missing or the file is not found — the default icon from `ui/images/` is used.

**Background** — custom window background:

```json
"background": "ui/background.png"
```

Recommended size 1100×650 (matches the main window's `setFixedSize`).

### Translation overrides in a theme

Any theme can override localization strings — fully or partially. Add a `texts` block to the theme JSON:

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

Keys are the same as in `ui/langs/*.json`. You only need to specify the strings that differ; the rest are inherited from the language file.

What can be overridden:

- UI texts — `button.play`, `info.title`, `settings.title`, `dialog.ok`, etc.
- Placeholders — `input.nick_placeholder`, `search.placeholder`.
- Hint and description strings.

What **cannot** be overridden via a theme:

- Plural forms (`time.years_ago` and others) — only from language files.
- Month names (`date.months`) — also only from language files.

A theme variant (`dark.mytheme.json`) may contain its own `texts` block — it is **merged** with the base theme's texts, not replaced. For example, if `mytheme.json` has `texts.ru_RU.button.play`, and the variant has only `texts.ru_RU.info.title`, then the variant will have both keys.

Overrides are applied together with language and theme loading — when switching languages, the current theme's overrides for the new language remain active if present.

### Applying changes

Changes to JSON are applied via the **"↻"** button next to the theme selector in FLauncher settings. The button re-reads files from disk, rebuilds the list, and repaints the interface. No launcher restart needed.
```

## Что изменилось

**build.spec.txt:**
- `get_version_from_file` теперь сначала читает `src/utils/constants.py`, а `src/utils.py` оставлен как fallback.
- `datas` исправлено: `('src/themes', 'themes')` (такого каталога нет) заменено на два корректных — `('src/ui/langs', 'ui/langs')` и `('src/ui/themes', 'ui/themes')`.
- `hiddenimports`: `'flmods.widgets'` → `'flmods.catalog'`, добавлены `'utils'`, `'utils.constants'`, `'utils.paths'`, `'utils.platform'`, `'utils.archive'`. Это критично — без явного указания подпакетов PyInstaller иногда не подтягивает их при `--onefile`, и в рантайме падает `ModuleNotFoundError`.

**README.md:**
- Сверху добавлена ссылка `[English version](README.EN.md)`.
- В особенности добавлена строка про локализацию с переопределением через темы.
- Структура проекта обновлена: `utils.py` → `utils/`, `flmods/widgets.py` → `flmods/catalog.py`, добавлены `i18n.py`, `ui/langs/`, `ui/themes/FLauncher/`.
- Добавлен раздел «Переопределение переводов в теме» с примером JSON, списком что можно/нельзя переопределять, и объяснением слияния `texts` в вариантах темы.

**README.EN.md:**
- Полный английский перевод README с той же структурой секций.
- Ссылка `[Русская версия](README.md)` сверху.

Обрати внимание: файл в задании назывался `build.spec.txt`, но README говорит `pyinstaller build.spec` — то есть у тебя в реальном проекте он, скорее всего, `build.spec`. Я оставил имя как в задании, просто переименуй при копировании в проект.