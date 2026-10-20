import random
from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

# апгрейдер «Зачёт» подключается отдельным модулем из папки zachet
from zachet import bp as zachet_bp
app.register_blueprint(zachet_bp, url_prefix='/upgrader')

USER_BALANCE = 5000 #балик

# функция для открытия главной страницы (также по дефолту)
@app.route('/main_page')
@app.route('/')
def main_page():
    return render_template('main_page.html')


# функция для открытия ракетки
@app.route('/raketka')
def raketka():
    return render_template('raketka.html')


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


# в этом ифе само тело программы
if __name__ == '__main__':
    app.run(debug=True)
