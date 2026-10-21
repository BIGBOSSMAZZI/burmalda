"""Хранилище баланса и истории.

Сейчас всё лежит в сессии Flask (cookie), чтобы игра работала «из коробки».
Когда у команды появится общая БД/пользователи — достаточно заменить
реализацию этих четырёх функций, остальной код менять не нужно.
"""
from flask import session

START_BALANCE = 1000
HISTORY_LIMIT = 15


def get_balance():
    return session.setdefault("balance", START_BALANCE)


def set_balance(value):
    session["balance"] = int(value)


def get_history():
    return list(session.get("double_history", []))


def add_history(number):
    history = get_history()
    history.append(int(number))
    session["double_history"] = history[-HISTORY_LIMIT:]


def reset():
    session["balance"] = START_BALANCE
    session["double_history"] = []
