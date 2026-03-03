import time
import threading
import asyncio
from pypresence import Presence


class DiscordRPC:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.client_id = "1143147014226444338"
        self.discord_presence = None
        self.connect()
    
    def connect(self):
        try:
            if self.settings_manager.settings.get("discord_rpc_enabled", True):
                self.discord_presence = Presence(self.client_id)
                self.discord_presence.connect()
        except Exception as e:
            print(f"Ошибка при подключении к Discord: {e}")
            self.discord_presence = None
    
    def set_presence(self, details, state, small_image=None):
        if self.discord_presence:
            threading.Thread(
                target=self._update_presence_async,
                args=(details, state, small_image),
                daemon=True
            ).start()
    
    def _update_presence_async(self, details, state, small_image=None):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.discord_presence:
                self.discord_presence.update(
                    details=details,
                    state=state,
                    start=time.time(),
                    large_image="icon",
                    small_image=small_image,
                    large_text="FLauncher"
                )
        except Exception as e:
            print(f"Ошибка при обновлении статуса Discord: {e}")
    
    def close(self):
        if self.discord_presence:
            try:
                self.discord_presence.close()
            except:
                pass