from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shadow_monarch_key"
DB_FILE = "players.json"

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return []

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    players = load_data()
    
    match_type = request.form.get('match_type')
    
    # 1. Capture Leader
    team_details = f"👑 {request.form.get('nick1')} ({request.form.get('uid1')})"
    
    # 2. Capture Duo
    if request.form.get('nick2'):
        team_details += f" | 2️⃣ {request.form.get('nick2')} ({request.form.get('uid2')})"
    
    # 3. Capture Duo Substitute (NEW)
    if request.form.get('duo_sub_nick'):
        team_details += f" | 🔄 Sub: {request.form.get('duo_sub_nick')} ({request.form.get('duo_sub_uid')})"
        
    # 4. Capture Squad
    if request.form.get('nick3'):
        team_details += f" | 3️⃣ {request.form.get('nick3')} ({request.form.get('uid3')})"
        team_details += f" | 4️⃣ {request.form.get('nick4')} ({request.form.get('uid4')})"
        
    # 5. Capture Squad Substitute
    if request.form.get('squad_sub_nick'):
        team_details += f" | 🔄 Sub: {request.form.get('squad_sub_nick')} ({request.form.get('squad_sub_uid')})"

    new_player = {
        "id": len(players) + 1,
        "time": datetime.now().strftime("%H:%M"),
        "nickname": team_details, 
        "uid": request.form.get('uid1'),
        "txn_id": request.form.get('txn_id'),
        "sender_name": request.form.get('sender_name'),
        "match": match_type,
        "status": "Pending",
        "room_details": "Waiting for Admin..."
    }
    
    players.append(new_player)
    save_data(players)
    
    return redirect(url_for('profile', uid=request.form.get('uid1')))

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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == "jinwoo":
            session['admin'] = True
    if not session.get('admin'):
        return render_template('login.html')
    return render_template('admin.html', players=load_data())

@app.route('/verify/<int:player_id>', methods=['POST'])
def verify(player_id):
    if not session.get('admin'): return "Access Denied"
    players = load_data()
    for p in players:
        if p['id'] == player_id:
            p['status'] = "Verified"
            p['room_details'] = request.form.get('room_info')
            break
    save_data(players)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
