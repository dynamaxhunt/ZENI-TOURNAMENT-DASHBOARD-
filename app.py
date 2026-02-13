from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "zeni_secret_key"

# --- DATABASE SETUP ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zeni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- LOGIN MANAGER SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False) # In real app, hash this!

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mode = db.Column(db.String(10))
    slot = db.Column(db.String(20))
    p1_uid = db.Column(db.String(20))
    p2_name = db.Column(db.String(50))
    p2_uid = db.Column(db.String(20))
    status = db.Column(db.String(20), default='PENDING')
    room_id = db.Column(db.String(20))
    room_pass = db.Column(db.String(20))
    # Relationship to link reg to user
    user = db.relationship('User', backref=db.backref('registrations', lazy=True))

# Create Database tables
with app.app_context():
    db.create_all()

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

        # Check if user exists
        user = User.query.filter_by(phone=phone).first()
        if user:
            return "User already exists! Go Login."
        
        # Create new user
        new_user = User(phone=phone, name=name, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        user = User.query.filter_by(phone=phone).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "Invalid Phone or Password"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- MAIN ROUTES ---
@app.route('/')
def index():
    # Only logged in users can see their dashboard properly
    return render_template('index.html', user=current_user)

@app.route('/register', methods=['POST'])
@login_required
def register():
    new_reg = Registration(
        user_id=current_user.id,
        mode=request.form.get('mode'),
        slot=request.form.get('slot'),
        p1_uid=request.form.get('p1_uid'),
        p2_name=request.form.get('p2_name', '-'),
        p2_uid=request.form.get('p2_uid', '-'),
        status='PENDING'
    )
    db.session.add(new_reg)
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    # Get registrations ONLY for this user
    my_regs = Registration.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', regs=my_regs)

# --- ADMIN ROUTES ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == "zeni123":
            all_regs = Registration.query.all()
            return render_template('admin.html', requests=all_regs)
    return render_template('admin_login.html')

@app.route('/approve/<int:reg_id>', methods=['POST'])
def approve(reg_id):
    reg = Registration.query.get(reg_id)
    if reg:
        reg.room_id = request.form.get('room_id')
        reg.room_pass = request.form.get('room_pass')
        reg.status = 'APPROVED'
        db.session.commit()
    return redirect(url_for('admin_dashboard')) # Simplified redirect

# Helper for admin to refresh
@app.route('/admin_dashboard')
def admin_dashboard():
    # In real app, protect this route too!
    all_regs = Registration.query.all()
    return render_template('admin.html', requests=all_regs)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    target_slot = request.form.get('target_slot')
    room_id = request.form.get('room_id')
    room_pass = request.form.get('room_pass')
    
    # Update all matching slots
    regs = Registration.query.filter_by(slot=target_slot).all()
    for reg in regs:
        reg.room_id = room_id
        reg.room_pass = room_pass
        reg.status = 'APPROVED'
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
