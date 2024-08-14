import telebot
import time


class TBot:
    def __init__(self, token, run_callback):
        super().__init__()
        self.bot = telebot.TeleBot(token, threaded=False)
        self.chat_id = None
        self.run_callback = run_callback

        @self.bot.message_handler(commands=["start"])
        def start(m, res=False):
            self.chat_id = m.chat.id
            self.bot.send_message(m.chat.id, 'Поток обработки запущен... Ожидайте новых объявлений')
            self.run_callback()

    def send_msg(self, msg: str):
        self.bot.send_message(self.chat_id, msg)

    def get_bot(self) -> object:
        return self.bot



