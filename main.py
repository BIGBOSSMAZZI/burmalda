import random
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import json
import os
app = Flask(__name__)
app.secret_key = 'burmalda-secret'  # нужен, чтобы работала session

# апгрейдер «Зачёт» подключается отдельным модулем из папки zachet
from zachet import bp as zachet_bp
app.register_blueprint(zachet_bp, url_prefix='/upgrader')

USERS_FILE = 'users.json'
USER_BALANCE = 5000 #балик
START_BALANCE = 5000

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


# сохраняет всех пользователей в файл
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)


# возвращает баланс того, кто сейчас вошёл (или None, если никто не вошёл)
def get_balance():
    login_name = session.get('user')
    users = load_users()
    if login_name not in users:
        return None
    return users[login_name]['balance']


# записывает новый баланс тому, кто сейчас вошёл
def set_balance(new_balance):
    login_name = session.get('user')
    users = load_users()
    if login_name in users:
        users[login_name]['balance'] = new_balance
        save_users(users)


# передаёт логин и баланс во ВСЕ шаблоны, чтобы шапка знала, кто вошёл
@app.context_processor
def inject_user():
    return {'current_user': session.get('user'), 'current_balance': get_balance()}

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
    balance = get_balance()
    if balance is None:  # никто не вошёл — отправляем на вход
        return redirect(url_for('login'))
    return render_template('slots.html', balance=balance)


# Эндпоинт для обработки вращения барабанов (POST-запрос)
@app.route('/slots/spin', methods=['POST'])
def slots_spin():
    USER_BALANCE = get_balance()  # баланс вошедшего игрока из users.json
    if USER_BALANCE is None:
        return jsonify({'error': 'Сначала войди в аккаунт'}), 401
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
    set_balance(USER_BALANCE)
    return jsonify({
        'reels': [r1, r2, r3],
        'is_win': is_win,
        'win_amount': win_amount,
        'balance': USER_BALANCE
    })


# функция для открытия тапалки
@app.route('/vorona combat', methods=['GET', 'POST'])
def vorona_combat():
    if request.method == 'POST':
        balance = get_balance()
        if balance is None:  # никто не вошёл
            return jsonify({'error': 'Сначала войди в аккаунт'}), 401
        balance += 1000
        set_balance(balance)
        return jsonify({'balance': balance})
    return render_template('vorona_combat.html')

# баланс для апгрейдера: GET — узнать баланс, POST — сохранить новый
@app.route('/api/balance', methods=['GET', 'POST'])
def api_balance():
    balance = get_balance()
    if balance is None:  # никто не вошёл
        return jsonify({'error': 'Сначала войди в аккаунт'}), 401
    if request.method == 'POST':
        balance = int(request.json['balance'])
        set_balance(balance)
    return jsonify({'balance': balance})

# страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login_name = request.form['login']
        password = request.form['password']
        users = load_users()

        if login_name in users and users[login_name]['password'] == password:
            session['user'] = login_name  # запоминаем, кто вошёл
            return redirect(url_for('profile'))
        error = 'Неверный логин или пароль'

    return render_template('login.html', error=error)


# страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        login_name = request.form['login']
        password = request.form['password']
        users = load_users()

        if not login_name or not password:
            error = 'Заполни оба поля'
        elif login_name in users:
            error = 'Такой логин уже занят'
        else:
            users[login_name] = {'password': password, 'balance': START_BALANCE}
            save_users(users)
            return redirect(url_for('login'))

    return render_template('register.html', error=error)


# личный кабинет
@app.route('/profile')
def profile():
    if get_balance() is None:  # никто не вошёл — отправляем на вход
        return redirect(url_for('login'))
    return render_template('profile.html')


# выход из аккаунта
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main_page'))


# в этом ифе само тело программы
if __name__ == '__main__':
    app.run(debug=True)