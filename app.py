from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shadow_monarch_key"

DB_FILE = "players.json"

# --- DATABASE HELPERS ---
def load_data():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

# --- HOME (REGISTRATION) ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    players = load_data()
    
    new_player = {
        "id": len(players) + 1,
        "time": datetime.now().strftime("%H:%M"),
        "nickname": request.form.get('nickname'),
        "uid": request.form.get('uid'),
        "txn_id": request.form.get('txn_id'),
        "sender_name": request.form.get('sender_name'),
        "match": request.form.get('match_type'),
        "status": "Pending", 
        "room_details": "Waiting for Admin..." 
    }
    
    players.append(new_player)
    save_data(players)
    
    return redirect(url_for('profile', uid=new_player['uid']))

# --- PLAYER DASHBOARD ---
@app.route('/profile')
def profile():
    uid = request.args.get('uid')
    players = load_data()
    
    my_info = None
    if uid:
        for p in players:
            if p.get('uid') == uid:
                my_info = p
    
    return render_template('profile.html', player=my_info)

# --- ADMIN PANEL ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Login Check
    if request.method == 'POST':
        if request.form.get('password') == "jinwoo": 
            session['admin'] = True
    
    if not session.get('admin'):
        return render_template('login.html')

    return render_template('admin.html', players=load_data())

# --- VERIFY & SEND ID ---
@app.route('/verify/<int:player_id>', methods=['POST'])
def verify(player_id):
    if not session.get('admin'): return "Access Denied"
    
    room_info = request.form.get('room_info')
    players = load_data()

    for p in players:
        if p['id'] == player_id:
            p['status'] = "Verified"
            p['room_details'] = room_info
            break
            
    save_data(players)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
