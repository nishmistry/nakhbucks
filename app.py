from flask import Flask, render_template, request, url_for, redirect
from flask_socketio import SocketIO, emit
import math
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SECRET_KEY'] = '6PMTBEmyV2kQ35h4RA9IGYNwVwASRAIX'
socketio = SocketIO(app, logging=True, engineio_logger=True)

user_balances = {'User1': 0, 
                 'User2': 0, 
                 'User3': 0,
                 'User4': 0, 
                 'User5': 0}

live_bets = {}

currId = 0

bopruptcy_board = {}

def apply_interest():
    global user_balances
    for i in user_balances:
        user_balances[i] = round(user_balances[i] * 1.05)
    socketio.emit('force bop board reload')

scheduler = BackgroundScheduler()
scheduler.add_job(apply_interest, 'interval', minutes=1)
scheduler.start()

@socketio.on('send bet')
def add_bet(json, methods=['GET', 'POST']):
    global live_bets
    global currId
    live_bets[currId] = json
    temp_list = []
    temp_list.append(currId)
    temp_list.append(json)
    print("appended bet to live_bets")
    socketio.emit('update bets', temp_list)
    print("sent 'update bets' to client")
    currId += 1
    print(json)

@socketio.on('please load bets')
def load_all_live_bets():
    global live_bets
    print("---------------")
    print(live_bets)
    emit('load bets', live_bets, broadcast=False)

@socketio.on('please load bop balances')
def load_bop_balances():
    global user_balances
    emit('load bop balances', user_balances)

@socketio.on('send my balance')
def send_user_balance(user):
    global user_balances
    target_balance = user_balances[user]
    emit('receive my balance', target_balance)

@socketio.on('just bopped')
def remove_bop(user):
    global user_balances
    target_balance = user_balances[user]
    new_balance = int(target_balance) - 1
    if (new_balance < 0):
        new_balance = 0
    else:
        user_balances[user] = new_balance

@socketio.on('declare bopruptcy')
def declare_bopruptcy(user):
    global user_balances
    global bopruptcy_board
    this_balance = user_balances[user]
    if this_balance == 0:
        print("Attempted to declare bopruptcy with 0 balance")
    else:
        owed_balance = this_balance / (len(user_balances) - 1)
        bopruptcy_board[user] = math.ceil(owed_balance)
        user_balances[user] = 0
        socketio.emit('force bop board reload')

@socketio.on('send my bopruptcy gains')
def send_bopruptcy_gains(user):
    global bopruptcy_board
    my_gains = {}
    for i in bopruptcy_board:
        if (i != user):
            my_gains[i] = bopruptcy_board[i]
    emit('load my bopruptcy gains', my_gains)

@socketio.on('user one won')
def user_one_won(betId, methods=['GET', 'POST']):
    global live_bets
    global user_balances
    target_bet = live_bets[int(betId)]
    loser = target_bet['user_two']
    wager = target_bet['bet_amount']
    currentBal = user_balances[loser]
    newBal = int(currentBal) + int(wager)
    user_balances[loser] = newBal
    del live_bets[int(betId)]
    socketio.emit('force bop board reload')
    socketio.emit('force live bets reload')

@socketio.on('user two won')
def user_two_won(betId, methods=['GET', 'POST']):
    global live_bets
    global user_balances
    target_bet = live_bets[int(betId)]
    loser = target_bet['user_one']
    wager = target_bet['bet_amount']
    currentBal = user_balances[loser]
    newBal = int(currentBal) + int(wager)
    user_balances[loser] = newBal
    del live_bets[int(betId)]
    socketio.emit('force bop board reload')
    socketio.emit('force live bets reload')

@app.route('/')
def landing():
    return render_template('landing.html')
    
@app.route('/bop-board', methods=['GET', 'POST'])
def load_bop_board():
    if "login" in request.form:
        return render_template('bop-board.html')
    return render_template('bop-board.html')

@app.route('/live-bets')
def load_live_bets():
    return render_template('live-bets.html')

@app.route('/make-a-bet', methods=['GET', 'POST'])
def load_make_a_bet():
    return render_template('make-a-bet.html')

@app.route('/info')
def load_info():
    return render_template('info.html')

@app.route('/logout')
def load_logout():
    return render_template('logout.html')

if __name__ == '__main__':
    app.run()