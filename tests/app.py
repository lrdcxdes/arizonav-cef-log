import enum
import queue
import threading
import time
from dataclasses import dataclass
import re
from typing import Optional

import pyautogui
import pyscreeze

from utils.gpt import gpt_answer, ReportAnswer, get_default_response
from utils.ocr import detect_number
from win import is_foreground

from ceflogs import CefLogs, ChatLog, NotificationLog, WhoReported
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, KeyCode, Controller as KeyboardController

translation_table = str.maketrans("", "", "\n\r*`,:;!?()[]{}<>|=+-_")


def find_number(text: list[str]) -> Optional[int]:
    for line in text:
        # Remove unwanted characters
        line = line.translate(translation_table).replace("  ", " ")
        print(line)

        # Extract report number using regular expression
        match = re.search(r"(\d+)", line)
        if match:
            report_number = int(match.group(1))
            return report_number


mouse = MouseController()
keyboard = KeyboardController()

log_path = r"C:\Program Files (x86)\Arizona Tools\Dev Files\message.json"

app = CefLogs(log_path)


@dataclass
class MyReportAnswer:
    is_tech: bool = False
    response: str = ""


@dataclass
class Report:
    query_number: int
    who_reported: WhoReported
    message: str
    report_type: "ReportType"
    report_answer: Optional[MyReportAnswer] = None


reports: list[Report] = []


def is_bad_report(message: str) -> bool:
    return any(
        re.search(r"\b" + re.escape(bad_word) + r"\b", message, flags=re.IGNORECASE)
        for bad_word in [
            "следи",
            "спусти",
            "sledi",
            "spusti",
            # "дм",
            "тп",
            "tp",
        ]
    )


def is_rule_report(message: str) -> bool:
    return any(
        re.search(r"\b" + re.escape(bad_word) + r"\b", message, flags=re.IGNORECASE)
        for bad_word in [
            "нрд",
            "nrd",
            "nrp",
            "нрп",
            "non-rp",
            "nonrp",
            "нонрп",
            "нон-рп",
            "dm",
            "дм",
            "байт",
            "sk",
            "мг",
            "мета",
            "db",
            "дб",
            "mg",
            "саунд",
            "sound",
            "бумб",
            "boom",
        ]
    )


def is_flip_report(message: str) -> bool:
    return any(
        re.search(r"\b" + re.escape(bad_word) + r"\b", message, flags=re.IGNORECASE)
        for bad_word in [
            "flip",
            "флип",
            "перевер",
            "горизонт",
        ]
    )


def is_stuck_report(message: str) -> bool:
    return any(
        re.search(r"\b" + re.escape(bad_word) + r"\b", message, flags=re.IGNORECASE)
        for bad_word in [
            "застря",
            "stuck",
            "забаг",
        ]
    )


def is_demension_report(message: str) -> bool:
    return any(
        re.search(r"\b" + re.escape(bad_word) + r"\b", message, flags=re.IGNORECASE)
        for bad_word in [
            "dimension",
            "дменш",
            "деменш",
            "setdm",
            "выйти не могу",
            "не могу выйти",
            "другого дм",
            "другой дм",
            "вирт",
            "мире",
            "параллель",
            "парелель",
            # "другой мир",
            "мир",
        ]
    )


class ReportType(enum.Enum):
    BAD = "bad"
    RULE = "rule"
    FLIP = "flip"
    STUCK = "stuck"
    DEMENSION = "demension"
    UNKNOWN = "unknown"


def get_report_type(message: str) -> ReportType:
    if is_bad_report(message):
        return ReportType.BAD
    elif is_demension_report(message):
        return ReportType.DEMENSION
    elif is_rule_report(message):
        return ReportType.RULE
    elif is_flip_report(message):
        return ReportType.FLIP
    elif is_stuck_report(message):
        return ReportType.STUCK
    else:
        return ReportType.UNKNOWN


current_reports_query: int = 0


EmptyReport = lambda i: Report(
    message="",
    query_number=i,
    who_reported=WhoReported(name="", id=0, cid=""),
    report_type=ReportType.UNKNOWN,
)


def update_reports(new_report: Report | int):
    global reports
    global current_reports_query

    last_report_number = (
        new_report.query_number if isinstance(new_report, Report) else new_report
    )
    current_reports_query = last_report_number

    if len(reports) < last_report_number:
        # add at start
        reports = [
            EmptyReport(i) for i in range(last_report_number - len(reports))
        ] + reports

    # оставить только последние last_report_number
    if isinstance(new_report, Report):
        reports.append(new_report)

    reports = reports[-last_report_number:]

    print(f"Updated reports: {reports}")
    print(f"Length of reports: {len(reports)}")


def add_report(report: Report):
    update_reports(report)


def get_current_query_number() -> int:
    global tab_opened

    if not tab_opened:
        # press tab
        keyboard.tap(Key.tab)

        time.sleep(0.1)

        mouse.position = (1813, 31)
        mouse.click(Button.left, 1)

        time.sleep(0.1)

        mouse.position = (448, 106)
        mouse.click(Button.left, 1)

        time.sleep(0.1)

        tab_opened = True

    screenshot = pyscreeze.screenshot(region=(365, 80, 183, 51))

    # press tab
    # keyboard.tap(Key.tab)

    number = detect_number(screenshot)

    print(f"Current query number: {number}")

    return number


def write_report_answer(text: str) -> None:
    mouse.position = (692, 973)
    mouse.click(Button.left, 1)

    time.sleep(0.02)

    keyboard.type(text)

    time.sleep(0.02)

    keyboard.tap(Key.enter)


current_report: Optional[Report] = None
current_report_answer_time: float = 0.0
tab_opened: bool = False
is_gpt: bool = False

chat_key = KeyCode.from_char("t")


def open_current_report_tab():
    global tab_opened

    # press tab
    keyboard.tap(Key.tab)

    time.sleep(0.1)

    mouse.position = (1813, 31)
    mouse.click(Button.left, 1)

    time.sleep(0.1)

    mouse.position = (448, 106)
    mouse.click(Button.left, 1)

    time.sleep(0.1)

    mouse.position = (300, 250)
    mouse.click(Button.left, 1)

    time.sleep(0.1)

    tab_opened = True


def write_in_chat(text: str) -> None:
    global tab_opened
    if tab_opened:
        keyboard.tap(Key.esc)
        tab_opened = False

    time.sleep(0.1)

    keyboard.tap("t")

    time.sleep(0.1)

    # paste in chat
    pyautogui.typewrite(text, interval=0.1)

    time.sleep(0.1)

    keyboard.tap(Key.enter)

    time.sleep(0.1)


def answer_current_report(
    report: Report, response: str = None, is_tech_bug: bool = False
):
    global current_report
    global current_report_answer_time
    global tab_opened
    global is_gpt

    is_gpt = response is not None

    current_report = report

    if not tab_opened:
        # press tab
        keyboard.tap(Key.tab)

        time.sleep(0.1)

        mouse.position = (1813, 31)
        mouse.click(Button.left, 1)

        time.sleep(0.1)

        mouse.position = (448, 106)
        mouse.click(Button.left, 1)

        time.sleep(0.1)

        tab_opened = True

    mouse.position = (300, 974)
    mouse.click(Button.left, 1)

    time.sleep(0.25)

    if report.report_type == ReportType.BAD:
        print("Answering bad report")
    elif report.report_type == ReportType.RULE:
        print("Answering rule report")
        write_report_answer(
            "Здравствуйте! Если у вас есть доказательства нарушения правил, вы можете подать жалобу "
            "на игрока на нашем форуме: https://forum.arizona-v.com/forums/110/. Если у вас есть "
            "вопросы, пожалуйста, напишите их в чат."
        )
        current_report_answer_time = time.time()
    elif report.report_type == ReportType.FLIP:
        print("Answering flip report")
        # write_in_chat(f"/slap {report.who_reported.id}")
    elif report.report_type == ReportType.STUCK:
        print("Answering stuck report")
        # write_in_chat(f"/respawn {report.who_reported.id}")
    elif report.report_type == ReportType.DEMENSION:
        print("Answering demension report")
        write_report_answer("Здравствуйте! Сейчас попробую вам помочь.")
        write_in_chat(f"/setdm {report.who_reported.id} 0")
        if not tab_opened:
            open_current_report_tab()
            write_report_answer(
                "Изменил вам деменшн. Закрываю ваше обращение. Приятной игры на Arizona V!"
            )
            close_report()
    else:
        print("Answering unknown report")
        write_report_answer(
            "Здравствуйте! Сейчас попробую вам помочь. Пожалуйста, подождите."
        )
        current_report_answer_time = time.time()
        if is_tech_bug:
            write_report_answer(
                "Здравствуйте. Вы можете оставить жалобу в тех-разделе нашего форума: "
                "https://forum.arizona-v.com/forums/64/. Прикрепите все доказательства и создайте тему."
            )
            close_report()
        elif response:
            write_report_answer(response)
            close_report()


def set_report_answer(report: Report):
    if (
        report.report_type == ReportType.RULE
        or report.report_type == ReportType.DEMENSION
    ):
        report.report_answer = MyReportAnswer(
            is_tech=False,
            response="",
        )
    elif report.report_type == ReportType.UNKNOWN:
        response = gpt_answer(report.message)
        if response is None or response == ReportAnswer.BAD:
            report.report_answer = None
        elif response == ReportAnswer.TECH_BUG:
            report.report_answer = MyReportAnswer(
                is_tech=True,
                response="",
            )
        elif isinstance(response, str):
            report.report_answer = MyReportAnswer(
                is_tech=False,
                response=response,
            )
    else:
        report.report_answer = None

    print(f"Set report answer: {report.report_answer}")


# load from all log
logs_ = app.parse_full_logs()
for log_ in logs_:
    if log_.message.startswith("!{#b84639}[Новый репорт]"):
        query_number_ = log_.message.split("В очереди ")[1].split("] от ")[0]
        who_reported_raw_ = log_.message.split("от ")[1].split("): !{#ffffff}")[0]
        who_reported_: WhoReported = WhoReported(
            name=who_reported_raw_.split(" (id: ")[0],
            id=int(who_reported_raw_.split(" (id: ")[1].split(", cid: ")[0]),
            cid=who_reported_raw_.split(", cid: ")[1],
        )
        message_ = log_.message.split("): !{#ffffff}")[1]

        report_type_ = get_report_type(message_)

        add_report(
            Report(
                query_number=int(query_number_),
                who_reported=who_reported_,
                message=message_,
                report_type=report_type_,
            )
        )


# Create a FIFO queue
report_queue = queue.Queue()


def process_reports():
    while True:
        # Get the next report from the queue and process it
        report = report_queue.get()
        set_report_answer(report)
        # Mark the task as done (important for queue.join() to work correctly)
        report_queue.task_done()


# Start a thread that processes reports
threading.Thread(target=process_reports, daemon=True).start()


for _report in reports:
    report_queue.put(_report)

print(reports)


def if_answer_now() -> Optional[Report]:
    try:
        current_query_number = get_current_query_number()
        if current_query_number is None:
            if pyscreeze.pixelMatchesColor(
                x=tab_opened_coords[0],
                y=tab_opened_coords[1],
                expectedRGBColor=tab_opened_color,
            ):
                current_query_number = 0
            else:
                return None
    except Exception as e:
        print(e)
        return None
    # update reports, remove old
    if current_query_number != current_reports_query:
        update_reports(current_query_number)

    if reports:
        report = reports[0]
        return report


last_gpt_report = None

tab_opened_coords = (1786, 46)
tab_opened_color = (255, 255, 255)


def process_update():
    while True:
        if not is_foreground():
            continue

        if current_report is not None:
            # if answer time is more than 30 sec
            if time.time() - current_report_answer_time > 30:
                close_report()
            continue

        # check if report is not bad and not unknown
        first_report = if_answer_now()
        if first_report is None:
            continue

        print(f"First report: {first_report}")

        if first_report.report_answer is not None:
            # noinspection PyUnresolvedReferences
            answer_current_report(
                first_report,
                response=first_report.report_answer.response,
                is_tech_bug=first_report.report_answer.is_tech,
            )
            continue

        time.sleep(1)


thread = threading.Thread(target=process_update)
thread.start()


def close_report():
    global current_report

    if current_report is None:
        return

    current_report = None

    # write in input field "Закрываю ваше обращение. Приятной игры на Arizona V!"
    mouse.position = (692, 973)
    mouse.click(Button.left, 1)
    time.sleep(0.02)
    keyboard.type("Закрываю ваше обращение. Приятной игры на Arizona V!")
    time.sleep(0.02)
    keyboard.tap(Key.enter)
    time.sleep(0.02)

    # click at 1672, 423
    mouse.position = (1672, 423)
    mouse.click(Button.left, 1)
    print("Closed current report")


@app.on(ChatLog)
async def handler1(log: ChatLog):
    print(log.message)
    if log.message.startswith("!{#b84639}[Новый репорт]"):
        print("New report detected")
        query_number = log.message.split("В очереди ")[1].split("] от ")[0]
        print(f"Query number: {query_number}")
        who_reported_raw = log.message.split("от ")[1].split("): !{#ffffff}")[0]
        who_reported: WhoReported = WhoReported(
            name=who_reported_raw.split(" (id: ")[0],
            id=int(who_reported_raw.split(" (id: ")[1].split(", cid: ")[0]),
            cid=who_reported_raw.split(", cid: ")[1],
        )
        print(f"Who reported: {who_reported}")
        message = log.message.split("): !{#ffffff}")[1]
        print(f"Message: {message}")

        report_type = get_report_type(message)

        report = Report(
            query_number=int(query_number),
            who_reported=who_reported,
            message=message,
            report_type=report_type,
        )

        add_report(report)

        report_queue.put(report)
    elif log.type == "reportMessage":
        global current_report_answer_time

        ticket_id = log.ticket_id
        message = log.message
        # print(f"Report message: {message} (ticket ID: {ticket_id})")

        close_triggers = ["нет", "закр", "не", "ne", "спс", "спасиб", "пон", "всё"]
        if any(trigger in message.lower() for trigger in close_triggers):
            close_report()
        elif is_gpt:
            answer = get_default_response(message)
            if answer:
                write_report_answer(answer)
                current_report_answer_time = time.time()
            else:
                close_report()
        else:
            current_report_answer_time = time.time()
            print("Not closing current report")


@app.on(NotificationLog)
async def handler2(log: NotificationLog):
    print(log)


if __name__ == "__main__":
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
