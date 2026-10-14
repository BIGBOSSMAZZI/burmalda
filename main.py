from flask import Flask, render_template
app = Flask(__name__)


#функция для открытия главной страницы (также по дефолту)
@app.route('/main_page')
@app.route('/')
def main_page():
    return render_template('main_page.html')

#функция для открытия ракетки
@app.route('/raketka')
def raketka():
    return render_template('raketka.html')

#функция для открыия апгрейдера
@app.route('/upgrader')
def upgrader():
    return render_template('upgrader.html')

#функция для открытия кейс баттла
@app.route('/case_battle')
def case_battle():
    return render_template('case_battle.html')

#функция для открыия слотов
@app.route('/slots')
def slots():
    return render_template('slots.html')

#функция для открытия тапалки
@app.route('/vorona combat')
def vorona_combat():
    return render_template('vorona_combat.html')


#в этом ифе само тело программы
if __name__ == '__main__':
    app.run(debug=True)