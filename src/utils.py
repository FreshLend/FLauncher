import os
import sys

VERSION = "v0.5.0"
MAIN_REPO = "MihailRis/voxelcore"
MAX_LOAD = 1000


def resource_path(relative_path):
    try:
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    except Exception:
        return relative_path


def get_platform_asset_pattern():
    system = sys.platform
    
    if system == 'win32':
        return 'win64.zip'
    elif system == 'darwin':
        return '.dmg'
    else:
        return '.AppImage'


def get_executable_pattern():
    system = sys.platform
    
    if system == 'win32':
        return '.exe'
    elif system == 'darwin':
        return '.app'
    else:
        return '.AppImage'

def format_date(date_str):
    if not date_str:
        return "Дата неизвестна"
    
    try:
        from datetime import datetime
        
        months_ru = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        
        release_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return f"{release_date.day} {months_ru[release_date.month]} {release_date.year}"
    except:
        return "Дата неизвестна"