import time
import logging
from pypresence import Presence
from i18n import tr

log = logging.getLogger("flauncher.discord")


class DiscordRPC:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.client_id = "1143147014226444338"
        self.discord_presence = None
        self.connected = False
        self.connect()

    def connect(self):
        if not self.settings_manager.settings.get("discord_rpc_enabled", True):
            return

        try:
            self.discord_presence = Presence(self.client_id)
            self.discord_presence.connect()
            self.connected = True
        except Exception as e:
            log.error(tr("log.discord_connect_error", error=e))
            self.discord_presence = None
            self.connected = False

    def set_presence(self, details, state, small_image=None):
        if not self.connected or not self.discord_presence:
            return

        try:
            self.discord_presence.update(
                details=details,
                state=state,
                start=time.time(),
                large_image="icon",
                small_image=small_image,
                large_text="FLauncher"
            )
        except Exception as e:
            log.error(tr("log.discord_update_error", error=e))
            self.connected = False
            self.connect()

    def close(self):
        if self.discord_presence:
            try:
                self.discord_presence.close()
            except Exception:
                pass
            finally:
                self.discord_presence = None
                self.connected = False