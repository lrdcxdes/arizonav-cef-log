import time

from pynput.keyboard import Key, KeyCode, Controller

keyboard = Controller()

chat_button = KeyCode(char="t")
enter_button = Key.enter


def send_message(text: str) -> bool:
    # press T to open chat
    keyboard.press(chat_button)
    keyboard.release(chat_button)
    time.sleep(0.1)
    # type message
    keyboard.type(text)
    # press enter to send
    keyboard.press(enter_button)
    keyboard.release(enter_button)
    return True
