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
    
    # --- 1. BUILD THE FULL TEAM LIST FOR ADMIN ---
    # This creates a vertical list using <br> tags
    team_display = f"👑 <b>{request.form.get('nick1')}</b> (UID: {request.form.get('uid1')})"
    
    # Duo
    if request.form.get('nick2'):
        team_display += f"<br>2️⃣ {request.form.get('nick2')} ({request.form.get('uid2')})"
    if request.form.get('duo_sub_nick'):
        team_display += f"<br>🔄 Sub: {request.form.get('duo_sub_nick')} ({request.form.get('duo_sub_uid')})"

    # Squad
    if request.form.get('nick3'):
        team_display += f"<br>3️⃣ {request.form.get('nick3')} ({request.form.get('uid3')})"
        team_display += f"<br>4️⃣ {request.form.get('nick4')} ({request.form.get('uid4')})"
    if request.form.get('squad_sub_nick'):
        team_display += f"<br>🔄 Sub: {request.form.get('squad_sub_nick')} ({request.form.get('squad_sub_uid')})"

    new_player = {
        "id": len(players) + 1,
        "time": datetime.now().strftime("%H:%M"),
        "team_html": team_display,      # The big list for Admin
        "leader_name": request.form.get('nick1'), # For the profile title
        "uid": request.form.get('uid1'), # STRICT: Only Leader UID is saved here
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
            # STRICT CHECK: Only if the UID matches the LEADER'S UID
            if p.get('uid') == uid:
                my_info = p
                break
    
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

    app.run(host='0.0.0.0', port=8080)
