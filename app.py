from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
    with open(DB_FILE, 'r') as f:
        return json.load(f)

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
    
    # Get Data
    new_player = {
        "id": len(players) + 1,
        "time": datetime.now().strftime("%H:%M"),
        "nickname": request.form.get('nickname'),
        "uid": request.form.get('uid'),
        "txn_id": request.form.get('txn_id'),
        "sender_name": request.form.get('sender_name'),
        "match": request.form.get('match_type'),
        "status": "Pending",  # Pending -> Verified
        "room_details": "Waiting for Admin..." # The ID/Pass goes here
    }
    
    players.append(new_player)
    save_data(players)
    
    return redirect(url_for('profile', uid=new_player['uid']))

# --- PLAYER DASHBOARD (CHECK STATUS) ---
@app.route('/profile')
def profile():
    uid = request.args.get('uid')
    players = load_data()
    
    # Find the player by UID
    my_info = None
    if uid:
        for p in players:
            if p['uid'] == uid:
                my_info = p
    
    return render_template('profile.html', player=my_info)

# --- ADMIN PANEL ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Simple Password Check
    if request.method == 'POST':
        if request.form.get('password') == "jinwoo": # <--- YOUR PASSWORD
            session['admin'] = True
    
    if not session.get('admin'):
        return render_template('login.html')

    return render_template('admin.html', players=load_data())

# --- ADMIN ACTION: VERIFY & SEND ID ---
@app.route('/verify/<int:player_id>', methods=['POST'])
def verify(player_id):
    if not session.get('admin'): return "Access Denied"
    
    room_info = request.form.get('room_info') # Admin types ID/Pass here
    players = load_data()

    for p in players:
        if p['id'] == player_id:
            p['status'] = "Verified"
            p['room_details'] = room_info # Saves the ID/Pass to their profile
            break
            
    save_data(players)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
