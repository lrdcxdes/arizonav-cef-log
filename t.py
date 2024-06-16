import time
import pyautogui
from pynput.keyboard import KeyCode, Controller, Key, Listener
from win import is_foreground

keyboard = Controller()

chat_key = KeyCode.from_char("T")
tab_opened = True


def write_in_chat(text: str) -> None:
    if tab_opened:
        keyboard.tap(Key.esc)

    time.sleep(0.1)

    keyboard.tap("t")

    time.sleep(0.1)

    # paste in chat
    pyautogui.typewrite(text, interval=0.1)

    time.sleep(0.1)

    keyboard.tap(Key.enter)

    time.sleep(0.1)


while not is_foreground():
    time.sleep(1)


write_in_chat("/gethere 120")
