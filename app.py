from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "zeni_secret_key"

# --- DATA STORAGE ---
registrations = []
approved_players = {} 
leaderboards = {'SOLO': [], 'DUO': []}

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html', solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])

@app.route('/register', methods=['POST'])
def register():
    mode = request.form.get('mode')
    new_reg = {
        'mode': mode,
        'p1_name': request.form.get('p1_name'),
        'p1_uid': request.form.get('p1_uid'),
        'p2_name': request.form.get('p2_name', '-'),
        'txn_id': request.form.get('txn_id'),
        'status': 'PENDING'
    }
    registrations.append(new_reg)
    # Send user to their profile immediately after registering
    return redirect(url_for('profile', uid=new_reg['p1_uid']))

@app.route('/profile')
def profile():
    uid = request.args.get('uid')
    status = "NOT FOUND"
    room = None
    
    if uid in approved_players:
        status = "APPROVED"
        room = approved_players[uid]
    else:
        for reg in registrations:
            if reg['p1_uid'] == uid:
                status = "PENDING"
                break
    return render_template('profile.html', uid=uid, status=status, room=room)

# --- ADMIN SYSTEM ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # If they submit the password form
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "zeni123":  # CHANGE THIS PASSWORD
            return render_template('admin.html', requests=registrations, solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])
        else:
            return "WRONG PASSWORD! GO BACK."
    
    # If they just open the page, show the Login Screen
    return render_template('admin_login.html')

@app.route('/update_leaderboard', methods=['POST'])
def update_leaderboard():
    lb_type = request.form.get('lb_type')
    leaderboards[lb_type].append({
        'name': request.form.get('name'),
        'kills': request.form.get('kills'),
        'prize': request.form.get('prize')
    })
    # Use a trick to keep them logged in (render admin directly)
    return render_template('admin.html', requests=registrations, solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])

@app.route('/approve/<uid>', methods=['POST'])
def approve(uid):
    room_id = request.form.get('room_id')
    room_pass = request.form.get('room_pass')
    approved_players[uid] = {'id': room_id, 'pass': room_pass}
    
    for reg in registrations:
        if reg['p1_uid'] == uid:
            reg['status'] = 'APPROVED'
            
    return render_template('admin.html', requests=registrations, solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])

if __name__ == '__main__':
    app.run(debug=True)
