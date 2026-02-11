from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "zeni_secret_key"

# --- DATA STORAGE ---
registrations = []
approved_players = {} 
leaderboards = {'SOLO': [], 'DUO': []}

@app.route('/')
def index():
    return render_template('index.html', solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])

@app.route('/register', methods=['POST'])
def register():
    mode = request.form.get('mode')
    
    # SAVE DETAILS (Including Substitute)
    new_reg = {
        'mode': mode,
        'p1_name': request.form.get('p1_name'),
        'p1_uid': request.form.get('p1_uid'),
        'p2_name': request.form.get('p2_name', '-'),
        'p2_uid': request.form.get('p2_uid', '-'),
        'sub_name': request.form.get('sub_name', '-'), # NEW SUB FIELD
        'sub_uid': request.form.get('sub_uid', '-'),   # NEW SUB FIELD
        'sender': request.form.get('sender_name'),
        'txn_id': request.form.get('txn_id'),
        'status': 'PENDING'
    }
    
    registrations.append(new_reg)
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
            # Check if they are Player 1 OR Player 2
            if reg['p1_uid'] == uid or reg['p2_uid'] == uid:
                status = "PENDING"
                break
    return render_template('profile.html', uid=uid, status=status, room=room)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == "zeni123":
            return render_template('admin.html', requests=registrations, solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])
        else:
            return "WRONG PASSWORD!"
    return render_template('admin_login.html')

@app.route('/update_leaderboard', methods=['POST'])
def update_leaderboard():
    lb_type = request.form.get('lb_type')
    leaderboards[lb_type].append({
        'name': request.form.get('name'),
        'kills': request.form.get('kills'),
        'prize': request.form.get('prize')
    })
    return render_template('admin.html', requests=registrations, solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])

@app.route('/approve/<uid>', methods=['POST'])
def approve(uid):
    approved_players[uid] = {'id': request.form.get('room_id'), 'pass': request.form.get('room_pass')}
    for reg in registrations:
        if reg['p1_uid'] == uid:
            reg['status'] = 'APPROVED'
    return render_template('admin.html', requests=registrations, solo_lb=leaderboards['SOLO'], duo_lb=leaderboards['DUO'])

if __name__ == '__main__':
    app.run(debug=True)
