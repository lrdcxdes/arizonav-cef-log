import time

from ceflogs import CefLogs, ChatLog, NotificationLog
from win import is_foreground
from win.kb import send_message

log_path = r"C:\RAGEMP\clientdata\cef_game_logs.txt"

app = CefLogs(log_path)

while not is_foreground():
    print("Waiting for RAGE Multiplayer to be in foreground")
    time.sleep(2)

send_message("/enable-chat-logs")


@app.on(ChatLog)
async def handler1(log: ChatLog):
    print(log)


@app.on(NotificationLog)
async def handler2(log: NotificationLog):
    print(log)


if __name__ == "__main__":
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
