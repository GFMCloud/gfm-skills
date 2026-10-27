"""Firing log (Demo material for a skill eval; not a real project.)"""


def average_temp(tempC):
    return sum(tempC) / len(tempC)


def parse_cone(text):
    return int(text.lstrip("0"))
