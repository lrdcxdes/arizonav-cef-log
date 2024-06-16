import openai
from enum import Enum

openai.api_key = "pk-mzLPnqoMkHqVqaouTqLEqnhOCQkcAjVSIbbLxmNIwwbNwYUm"
openai.base_url = "https://api.pawan.krd/v1/"


class ReportAnswer(Enum):
    TECH_BUG = "TECH-BUG"
    BAD = "BAD"


def gpt_answer(prompt: str) -> ReportAnswer | str | None:
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-unfiltered",
            messages=[
                {
                    "role": "system",
                    "content": "Отвечай 'TECH-BUG' если вопрос технический, отвечай текстом кратко если на"
                    " вопрос можно ответить без "
                    "взаимодействия с игроком который задает этот вопрос, и только в крайнем случае отвечай 'BAD' если нужно взаимодействие"
                    " со стороны администратора чтобы помочь игроку с вопросом, но лучше все же подбирай ответ сам. "
                               "Отвечай только на русском, все ответы не связанные с реальной жизнью, это игра гта.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        # print(completion.choices[0].message.content)
        if "TECH-BUG" in completion.choices[0].message.content.upper():
            return ReportAnswer.TECH_BUG
        elif "BAD" in completion.choices[0].message.content.upper():
            return ReportAnswer.BAD
        elif "error" in completion.choices[0].message.content.lower():
            return None
        else:
            return completion.choices[0].message.content
    except Exception as e:
        print(e)
        return None


def get_default_response(prompt: str):
    completion = openai.chat.completions.create(
        model="gpt-3.5-unfiltered",
        messages=[
            {
                "role": "system",
                "content": "Отвечай чтобы писали на форум если вопрос технический, отвечай текстом кратко если на"
                " вопрос можно ответить без "
                "взаимодействия с игроком который задает этот вопрос, и только в крайнем случае отвечай 'к сожалению не могу помочь' если нужно взаимодействие"
                " со стороны администратора чтобы помочь игроку с вопросом.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    print(completion.choices[0].message.content)
    return completion.choices[0].message.content


if __name__ == "__main__":
    print(gpt_answer("привет вы тут?"))
