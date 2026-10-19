import random
from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

# апгрейдер «Зачёт» подключается отдельным модулем из папки zachet
from zachet import bp as zachet_bp
app.register_blueprint(zachet_bp, url_prefix='/upgrader')

# Глобальный баланс игрока (пока без БД, хранится в оперативной памяти сервера)
USER_BALANCE = 5000


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


# функция для открытия слотов (теперь передает баланс в шаблон)
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
    
    # ставка
    if bet > USER_BALANCE or bet <= 0:
        return jsonify({'error': 'Недостаточно средств!'}), 400
        
    USER_BALANCE -= bet
    symbols = ['🍒', '🍋', '🍉', '⭐', '💎']
    
    # Генерируем 3 случайных барабана
    r1 = random.choice(symbols)
    r2 = random.choice(symbols)
    r3 = random.choice(symbols)
    
    # исправленная логика выигрыша:
    if r1 == r2 and r2 == r3:
        win_amount = bet * 15
        USER_BALANCE += win_amount
        is_win = True
    # 2. Утешительный приз (пара из трех картинок)
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
