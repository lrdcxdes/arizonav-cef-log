from typing import List


class Report:
    def __init__(self, message: str, query_number: int):
        self.message = message
        self.query_number = query_number

    def __repr__(self):
        return f"Report({self.message!r}, {self.query_number!r})"


def update_reports(new_report: Report, reports: List[Report]) -> List[Report]:
    query_size = new_report.query_number

    # return list size must be query_size
    # like query = [1, 2, 3]
    # if new query_size = 2, then return [3, new]
    # after that
    # like query = [3, new]
    # if new query_size = 2, then return [new, new]
    return reports[-query_size+1:] + [new_report]


# Пример использования
query = [Report("Запрос 1", 1), Report("Запрос 2", 2), Report("Запрос 3", 3)]

new_report = Report("Новый запрос", 2)

query = update_reports(new_report, query)

print(query)

new_report = Report("Еще один запрос", 2)

query = update_reports(new_report, query)

print(query)
