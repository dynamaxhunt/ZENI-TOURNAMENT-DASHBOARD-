from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "zeni_secret_key"

# --- DATABASE SETUP ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zeni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DEFAULT SETTINGS ---
DEFAULT_SLOTS = {
    'SOLO_A': '6:00 PM', 'SOLO_B': '7:00 PM', 'SOLO_C': '8:00 PM',
    'DUO_A': '9:00 PM', 'DUO_B': '10:00 PM', 'DUO_C': '11:00 PM'
}

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mode = db.Column(db.String(10))
    slot = db.Column(db.String(20))
    p1_name = db.Column(db.String(50))
    p1_uid = db.Column(db.String(20))
    p2_name = db.Column(db.String(50))
    p2_uid = db.Column(db.String(20))
    sub_name = db.Column(db.String(50))
    sub_uid = db.Column(db.String(20))
    sender = db.Column(db.String(50))
    txn_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='PENDING')
    room_id = db.Column(db.String(20))
    room_pass = db.Column(db.String(20))
    user = db.relationship('User', backref=db.backref('registrations', lazy=True))

class SlotSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    time = db.Column(db.String(20))

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(10)) # SOLO or DUO
    name = db.Column(db.String(50))
    kills = db.Column(db.String(10))
    prize = db.Column(db.String(20))

# --- HELPERS ---
def get_slot_times():
    settings = SlotSetting.query.all()
    slots = DEFAULT_SLOTS.copy()
    for s in settings:
        slots[s.name] = s.time
    return slots

def get_leaderboards():
    solo = Leaderboard.query.filter_by(mode='SOLO').all()
    duo = Leaderboard.query.filter_by(mode='DUO').all()
    return solo, duo

# --- INITIALIZE DB ---
with app.app_context():
    db.create_all()
    if not SlotSetting.query.first():
        for name, time in DEFAULT_SLOTS.items():
            db.session.add(SlotSetting(name=name, time=time))
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- AUTH ROUTES ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        password = request.form.get('password')
        if User.query.filter_by(phone=phone).first():
            return "User already exists! <a href='/login'>Login</a>"
        new_user = User(phone=phone, name=name, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(phone=request.form.get('phone')).first()
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('index'))
        return "Invalid Credentials. <a href='/login'>Try Again</a>"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- MAIN ROUTES ---
@app.route('/')
def index():
    solo_lb, duo_lb = get_leaderboards()
    return render_template('index.html', user=current_user, slots=get_slot_times(), solo_lb=solo_lb, duo_lb=duo_lb)

@app.route('/register', methods=['POST'])
@login_required
def register():
    new_reg = Registration(
        user_id=current_user.id,
        mode=request.form.get('mode'),
        slot=request.form.get('slot'),
        p1_name=request.form.get('p1_name'),
        p1_uid=request.form.get('p1_uid'),
        p2_name=request.form.get('p2_name', '-'),
        p2_uid=request.form.get('p2_uid', '-'),
        sub_name=request.form.get('sub_name', '-'),
        sub_uid=request.form.get('sub_uid', '-'),
        sender=request.form.get('sender_name'),
        txn_id=request.form.get('txn_id'),
        status='PENDING'
    )
    db.session.add(new_reg)
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    my_regs = Registration.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', regs=my_regs)

# --- ADMIN ROUTES ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == "zeni123":
            all_regs = Registration.query.all()
            return render_template('admin.html', requests=all_regs, slots=get_slot_times())
    return render_template('admin_login.html')

@app.route('/update_slots', methods=['POST'])
def update_slots():
    for key in DEFAULT_SLOTS.keys():
        new_time = request.form.get(key)
        if new_time:
            setting = SlotSetting.query.filter_by(name=key).first()
            if setting:
                setting.time = new_time
            else:
                db.session.add(SlotSetting(name=key, time=new_time))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_leaderboard', methods=['POST'])
def update_leaderboard():
    db.session.add(Leaderboard(
        mode=request.form.get('lb_type'),
        name=request.form.get('name'),
        kills=request.form.get('kills'),
        prize=request.form.get('prize')
    ))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/approve/<int:reg_id>', methods=['POST'])
def approve(reg_id):
    reg = Registration.query.get(reg_id)
    if reg:
        reg.room_id = request.form.get('room_id')
        reg.room_pass = request.form.get('room_pass')
        reg.status = 'APPROVED'
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/clear_requests', methods=['POST'])
def clear_requests():
    db.session.query(Registration).delete()
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/broadcast', methods=['POST'])
def broadcast():
    target_slot = request.form.get('target_slot')
    room_id = request.form.get('room_id')
    room_pass = request.form.get('room_pass')
    regs = Registration.query.filter_by(slot=target_slot).all()
    for reg in regs:
        reg.room_id = room_id
        reg.room_pass = room_pass
        reg.status = 'APPROVED'
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():
    all_regs = Registration.query.all()
    return render_template('admin.html', requests=all_regs, slots=get_slot_times())

if __name__ == '__main__':
    app.run(debug=True)
