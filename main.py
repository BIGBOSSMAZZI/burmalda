import math
import random
import threading
import time
import os

from flask import Flask, jsonify, render_template, request
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

#апгрейдер «Зачёт» подключается отдельным модулем из папки zachet
from zachet import bp as zachet_bp
app.register_blueprint(zachet_bp, url_prefix='/upgrader')

from double import double_bp
app.register_blueprint(double_bp, url_prefix="/double")

for rule in app.url_map.iter_rules():
    print(rule.endpoint, '->', rule.rule)


USER_BALANCE = 5000 #балик

# функция для открытия главной страницы (также по дефолту)
@app.route('/main_page')
@app.route('/')
def main_page():
    return render_template('main_page.html')



@app.route('/rocket')
def rocket():
    return render_template('index_rocket.html')

# функция для открытия кейс баттла
@app.route('/case_battle')
def case_battle():
    return render_template('case_battle.html')


# функция для открытия слотов (передает баланс в шаблон)
@app.route('/slots')
def slots():
    global USER_BALANCE
    return render_template('slots.html', balance=USER_BALANCE)


# Эндпоинт для обработки вращения барабанов (POST-запрос)
@app.route('/slots/spin', methods=['POST'])
def slots_spin():
    global USER_BALANCE
    data = request.json or {}
    bet = int(data.get('bet', 100))
    
    if bet > USER_BALANCE or bet <= 0:
        return jsonify({'error': 'Недостаточно средств!'}), 400
        
    USER_BALANCE -= bet
    
    # Список доступных символов
    symbols = ['🍒', '🍋', '🍉', '⭐', '💎', '🔥']
    
    # Задаем веса (вероятности) для каждого символа по порядку. Чем больше число, тем выше шанс выпадения элемента.
    weights = [22, 22, 22, 17, 15, 2]
    
    # Генерируем каждый барабан отдельно с учетом весов
    r1 = random.choices(symbols, weights=weights)[0]
    r2 = random.choices(symbols, weights=weights)[0]
    r3 = random.choices(symbols, weights=weights)[0]

    # 1. ГЛАВНЫЙ СУПЕРПРИЗ: Три редких элемента '🔥' подряд. в фронтэнде заменится на Никола
    if r1 == '🔥' and r2 == '🔥' and r3 == '🔥':
        win_amount = bet * 100  # Мега-джекпот х100!
        USER_BALANCE += win_amount
        is_win = True
    # 2. Обычный джекпот (все 3 совпали)
    elif r1 == r2 and r2 == r3:
        win_amount = bet * 15
        USER_BALANCE += win_amount
        is_win = True
    # 3. Утешительный приз (любая пара картинок)
    elif r1 == r2 or r2 == r3 or r1 == r3:
        win_amount = bet * 2
        USER_BALANCE += win_amount
        is_win = True
    else:
        win_amount = 0
        is_win = False
        
    return jsonify({
        'reels': [r1, r2, r3],
        'is_win': is_win,
        'win_amount': win_amount,
        'balance': USER_BALANCE
    })


# функция для открытия тапалки
@app.route('/vorona combat')
def vorona_combat():
    return render_template('vorona_combat.html')

# ---- игра «Ракета»: раунды и баланс считает сервер ----
BET_TIME = 5.0        # секунд на ставки
PAUSE_AFTER = 2.5     # пауза после взрыва до следующего раунда
GROWTH = 0.36         # скорость роста множителя (как в клиенте: 0.12 * 3)
HOUSE_EDGE = 0.96     # возврат игрокам, ~4% в пользу казино
HISTORY_LEN = 20

lock = threading.Lock()

state = {
    "phase": "waiting",       # waiting | flying | crashed
    "round_id": 0,
    "bet_end": 0.0,           # когда закончится приём ставок
    "launch_time": 0.0,       # когда ракета взлетела
    "crash_at": 1.0,          # множитель краха (скрыт, пока не случился)
    "next_round_at": 0.0,     # когда начнётся следующий раунд
    "balance": 1000.0,
    "bet": 0.0,
    "cashed_out": None,       # множитель, на котором игрок забрал
    "history": [],            # последние краши
}


def gen_crash():
    """Множитель краха с преимуществом дома."""
    r = random.random()
    c = HOUSE_EDGE / (1 - r)
    return max(1.0, math.floor(c * 100) / 100)


def current_mult(now):
    t = now - state["launch_time"]
    return math.floor(math.exp(GROWTH * t) * 100) / 100


def new_round(now):
    state["round_id"] += 1
    state["phase"] = "waiting"
    state["bet_end"] = now + BET_TIME
    state["crash_at"] = gen_crash()
    state["bet"] = 0.0
    state["cashed_out"] = None


def advance(now):
    """Переводит раунд в следующую фазу по времени. Вызывается при каждом запросе."""
    if state["phase"] == "waiting" and now >= state["bet_end"]:
        state["phase"] = "flying"
        state["launch_time"] = state["bet_end"]

    if state["phase"] == "flying":
        if current_mult(now) >= state["crash_at"]:
            state["phase"] = "crashed"
            state["next_round_at"] = now + PAUSE_AFTER
            state["history"].insert(0, state["crash_at"])
            del state["history"][HISTORY_LEN:]

    if state["phase"] == "crashed" and now >= state["next_round_at"]:
        new_round(now)


def snapshot(now):
    phase = state["phase"]
    if phase == "flying":
        mult = min(current_mult(now), state["crash_at"])
    elif phase == "crashed":
        mult = state["crash_at"]
    else:
        mult = 1.0
    return {
        "phase": phase,
        "round_id": state["round_id"],
        "multiplier": mult,
        "crash_at": state["crash_at"] if phase == "crashed" else None,
        "bet_left": max(0.0, state["bet_end"] - now) if phase == "waiting" else 0.0,
        "balance": round(state["balance"], 2),
        "bet": state["bet"],
        "cashed_out": state["cashed_out"],
        "history": state["history"],
    }

@app.route("/api/state")
def api_state():
    with lock:
        now = time.time()
        advance(now)
        return jsonify(snapshot(now))


@app.route("/api/bet", methods=["POST"])
def api_bet():
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify(error="Некорректная ставка"), 400

    with lock:
        now = time.time()
        advance(now)
        if state["phase"] != "waiting":
            return jsonify(error="Ставки принимаются только перед взлётом"), 409
        if state["bet"] > 0:
            return jsonify(error="Ставка уже сделана"), 409
        if amount <= 0 or amount > state["balance"]:
            return jsonify(error="Недостаточно средств или неверная ставка"), 400
        state["balance"] = round(state["balance"] - amount, 2)
        state["bet"] = amount
        return jsonify(snapshot(now))


@app.route("/api/cashout", methods=["POST"])
def api_cashout():
    with lock:
        now = time.time()
        advance(now)
        if state["phase"] != "flying" or state["bet"] <= 0 or state["cashed_out"] is not None:
            return jsonify(error="Забрать сейчас нельзя"), 409
        mult = min(current_mult(now), state["crash_at"])
        if mult >= state["crash_at"]:
            # ракета уже взорвалась в этот момент
            advance(now)
            return jsonify(error="Ракета уже взорвалась"), 409
        state["cashed_out"] = mult
        state["balance"] = round(state["balance"] + state["bet"] * mult, 2)
        state["bet"] = 0.0
        return jsonify(snapshot(now))

new_round(time.time())   # первый раунд при запуске сервера

for rule in app.url_map.iter_rules():
    print(rule.endpoint, "->", rule.rule)

# в этом ифе само тело программы
if __name__ == '__main__':
    app.run(debug=True)
