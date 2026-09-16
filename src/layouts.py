LAYOUTS = {
    "tlauncher": {
        "bar_position": "bottom",
        "bar_height": 90,
        "release_scroll": (20, 10, 800, -110),
        "info_panel": (830, 10, 250, -110),
        "nick_input": (10, 20, 200, 60),
        "version_combo": (220, 20, 300, 60),
        "play_button": (530, 20, 300, 60),
        "flm_button": (835, 20, 60, 60),
        "reload_button": (895, 20, 60, 60),
        "folder_button": (965, 20, 60, 60),
        "settings_button": (1035, 20, 60, 60),
        "progress_bar": (10, 0, -20, 20),
        "cancel_button": (1000, 0, 80, 20),
    },
    "legacy": {
        "bar_position": "top",
        "bar_height": 90,
        "release_scroll": (250, 10, -265, -20),
        "info_panel": (15, 10, 220, -20),
        "nick_input": (15, 15, 170, 50),
        "version_combo": (195, 15, 240, 50),
        "play_button": (445, 15, 320, 50),
        "flm_button": (775, 15, 50, 50),
        "reload_button": (830, 15, 50, 50),
        "folder_button": (885, 15, 50, 50),
        "settings_button": (940, 15, 50, 50),
        "progress_bar": (15, 68, -30, 18),
        "cancel_button": (-100, 68, 85, 18),
    },
}


def get_layout(name):
    return LAYOUTS.get(name, LAYOUTS["tlauncher"])