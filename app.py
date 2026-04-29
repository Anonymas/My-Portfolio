from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import func
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')


# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/project_images')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
limiter = Limiter(key_func=get_remote_address, app=app)
# =============================
# MODELS
# =============================

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    image1 = db.Column(db.String(255), nullable=True)
    image2 = db.Column(db.String(255), nullable=True)
    date = db.Column(db.String(50), default=lambda: datetime.utcnow().strftime('%B %Y'))
    author = db.Column(db.String(100), default='Dennis Githinji')
    comments = db.Column(db.String(50), default='24')
    views = db.relationship(
        'ProjectView',
        backref='project',
        cascade="all, delete-orphan"
    )


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=True)  
    subject = db.Column(db.String(200), nullable=True)  
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_read = db.Column(db.Boolean, default=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class ProjectDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    project = db.relationship(
    'Project',
    backref=db.backref('details', uselist=False, cascade="all, delete-orphan")
)

    # ✅ ADD THESE (copy from ProjectView)
    title = db.Column(db.String(200))
    overview = db.Column(db.Text)
    problem = db.Column(db.Text)
    solution = db.Column(db.Text)
    features = db.Column(db.Text)
    architecture = db.Column(db.Text)
    workflow = db.Column(db.Text)
    challenges = db.Column(db.Text)
    technologies = db.Column(db.String(500))
    future = db.Column(db.Text)
    takeaways = db.Column(db.Text)

    image1 = db.Column(db.String(200))
    image2 = db.Column(db.String(200))
    image3 = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    ip_address = db.Column(db.String(100))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    # Basic info
    title = db.Column(db.String(200))
    
    # Plain text fields (no HTML needed!)
    overview = db.Column(db.Text)           # Project Overview
    problem = db.Column(db.Text)            # Problem Statement
    solution = db.Column(db.Text)           # Solution
    features = db.Column(db.Text)           # Key Features (newline separated)
    architecture = db.Column(db.Text)       # System Architecture
    workflow = db.Column(db.Text)           # System Workflow (newline separated)
    challenges = db.Column(db.Text)         # Technical Challenges
    technologies = db.Column(db.String(500)) # Comma-separated tech list
    future = db.Column(db.Text)             # Future Improvements
    takeaways = db.Column(db.Text)          # Key Takeaways
    
    # Images
    image1 = db.Column(db.String(200))
    image2 = db.Column(db.String(200))
    image3 = db.Column(db.String(200))
    text2 = db.Column(db.String(500))
    text3 = db.Column(db.String(500))
    
    # Backward compatibility
    content = db.Column(db.Text)
    content2 = db.Column(db.Text)
    content4 = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    

@app.before_request
def ensure_non_www():
    # If the user visits 'www.dennisgithinji.tech'
    if request.host.startswith('www.'):
        # Build the new URL without 'www.'
        new_host = request.host.replace('www.', '', 1)
        new_url = f"{request.scheme}://{new_host}{request.full_path}"
        # Send them to the new URL with a permanent (301) status code
        return redirect(new_url, code=301)

# =============================
# AUTH ROUTES
# =============================

@app.route('/admin-login', methods=['POST'])
@limiter.limit("5 per minute")
def admin_login():
    username = request.form['username']
    password = request.form['password']

    admin = Admin.query.filter_by(username=username).first()

    if admin and check_password_hash(admin.password, password):
        session['admin'] = True
        session.permanent = True  # activates timeout

        flash("Login successful!", "success")
        return redirect(url_for('admin_dashboard'))

    flash("Invalid credentials", "error")
    return redirect(url_for('index'))

from flask import session, redirect, url_for

@app.route('/logout')
def logout():
    session.clear()  # clears user session
    return redirect(url_for('index'))

# =============================
# VIEW ROUTES
# =============================

@app.route('/')
def index():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/projects')
def projects_page():
    projects = Project.query.all()
    return render_template('projects.html', projects=projects)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')  # ADD THIS
        subject = request.form.get('subject')  # ADD THIS
        message = request.form.get('message')

        if not (name and email and message):
            flash('Please fill all required fields (Name, Email, Message)', 'error')
            return redirect(url_for('contact'))

        c = Contact(
            name=name, 
            email=email, 
            phone=phone,  # ADD THIS
            subject=subject,  # ADD THIS
            message=message
        )
        db.session.add(c)
        db.session.commit()
        flash('Message sent — thank you!', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

# =============================
# ADMIN DASHBOARD + CRUD
# =============================

@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('index'))
    
    projects = Project.query.all()
    projects_with_details = [p for p in projects if p.details]
    details = ProjectDetail.query.all()

    total_views = db.session.query(func.count(ProjectView.id)).scalar()

    return render_template(
        'admin_dashboard.html',
        projects=projects,
        projects_with_details=projects_with_details,
        details=details,  # IMPORTANT
        total_views=total_views
    )

@app.route('/add', methods=['GET', 'POST'])
def add_project():
    if not session.get('admin'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']

        # Handle Image Uploads
        image1 = request.files.get('image1')
        image2 = request.files.get('image2')

        img1_filename = None
        img2_filename = None

        if image1 and image1.filename != "":
            img1_filename = secure_filename(image1.filename)
            image1.save(os.path.join(app.config['UPLOAD_FOLDER'], img1_filename))

        if image2 and image2.filename != "":
            img2_filename = secure_filename(image2.filename)
            image2.save(os.path.join(app.config['UPLOAD_FOLDER'], img2_filename))

        new_project = Project(
            title=title,
            description=description,
            link=link,
            image1=img1_filename,
            image2=img2_filename
        )

        db.session.add(new_project)
        db.session.commit()
        flash("Project added successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('add_project.html')

@app.route('/edit_project/<int:id>', methods=['POST'])
def edit_project(id):
    if 'admin' not in session:
        return redirect(url_for('index'))

    project = Project.query.get_or_404(id)

    project.title = request.form['title']
    project.description = request.form['description']
    project.link = request.form['link']

    upload_folder = app.config['UPLOAD_FOLDER']

    # Handle images
    image1 = request.files.get('image1')
    image2 = request.files.get('image2')

    if image1 and image1.filename:
        filename1 = secure_filename(image1.filename)
        image1.save(os.path.join(upload_folder, filename1))
        project.image1 = filename1

    if image2 and image2.filename:
        filename2 = secure_filename(image2.filename)
        image2.save(os.path.join(upload_folder, filename2))
        project.image2 = filename2

    db.session.commit()

    flash("Project updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete/<int:id>')
def delete_project(id):
    if 'admin' not in session:
        return redirect(url_for('index'))

    project = Project.query.get_or_404(id)

    db.session.delete(project)  # ✅ deletes views automatically
    db.session.commit()

    flash("Project deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_detail/<int:id>')
def delete_detail(id):
    if 'admin' not in session:
        return redirect(url_for('index'))

    detail = ProjectDetail.query.get_or_404(id)
    db.session.delete(detail)
    db.session.commit()

    flash("Project detail deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# =============================
# PROJECT DETAILS (NEW VERSION)
# =============================

@app.route('/add_project_detail', methods=['POST'])
def add_project_detail():
    if not session.get('admin'):
        return redirect(url_for('index'))
    
    project_id = request.form.get('project_id')
    if not project_id:
        flash('Project ID is required', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Check if detail already exists
    detail = ProjectDetail.query.filter_by(project_id=project_id).first()
    if not detail:
        detail = ProjectDetail(project_id=project_id)
        db.session.add(detail)
    
    # Save all plain text fields
    detail.title = request.form.get('title')
    detail.overview = request.form.get('overview')
    detail.problem = request.form.get('problem')
    detail.solution = request.form.get('solution')
    detail.features = request.form.get('features')
    detail.architecture = request.form.get('architecture')
    detail.workflow = request.form.get('workflow')
    detail.challenges = request.form.get('challenges')
    detail.technologies = request.form.get('technologies')
    detail.future = request.form.get('future')
    detail.takeaways = request.form.get('takeaways')
    
    # Handle image uploads
    upload_folder = app.config['UPLOAD_FOLDER']
    
    for img_field in ['image1', 'image2', 'image3']:
        file = request.files.get(img_field)
        if file and file.filename:
            filename = secure_filename(f"{project_id}_{img_field}_{file.filename}")
            file.save(os.path.join(upload_folder, filename))
            setattr(detail, img_field, filename)
    
    db.session.commit()
    flash('Project details saved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_project_detail/<int:id>', methods=['POST'])
def edit_project_detail(id):
    if 'admin' not in session:
        return redirect(url_for('index'))

    detail = ProjectDetail.query.get_or_404(id)

    # Text fields
    detail.title = request.form.get('title')
    detail.overview = request.form.get('overview')
    detail.problem = request.form.get('problem')
    detail.solution = request.form.get('solution')
    detail.features = request.form.get('features')
    detail.architecture = request.form.get('architecture')
    detail.workflow = request.form.get('workflow')
    detail.challenges = request.form.get('challenges')
    detail.technologies = request.form.get('technologies')
    detail.future = request.form.get('future')
    detail.takeaways = request.form.get('takeaways')

    # ✅ HANDLE IMAGE UPDATES
    upload_folder = app.config['UPLOAD_FOLDER']

    for img_field in ['image1', 'image2', 'image3']:
        file = request.files.get(img_field)

        if file and file.filename:
            filename = secure_filename(f"{detail.project_id}_{img_field}_{file.filename}")
            file.save(os.path.join(upload_folder, filename))

            # overwrite ONLY if new file uploaded
            setattr(detail, img_field, filename)

    db.session.commit()

    flash("Project details updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# =============================
# MESSAGE HANDLING
# =============================

@app.route("/admin/messages")
def admin_messages():
    if "admin" not in session:
        return redirect(url_for('index'))

    search = request.args.get("search")

    if search:
        messages = Contact.query.filter(
            Contact.name.contains(search) |
            Contact.email.contains(search) |
            Contact.message.contains(search)
        ).order_by(Contact.id.desc()).all()
    else:
        messages = Contact.query.order_by(Contact.id.desc()).all()

    unread_count = Contact.query.filter_by(is_read=False).count()

    return render_template(
        "admin_messages.html",
        messages=messages,
        unread_count=unread_count
    )

@app.route("/admin/messages/read/<int:id>")
def mark_read(id):
    if "admin" not in session:
        return redirect(url_for('index'))

    message = Contact.query.get_or_404(id)
    message.is_read = True
    db.session.commit()

    flash("Message marked as read", "success")
    return redirect(url_for("admin_messages"))

@app.route("/admin/messages/delete/<int:id>")
def delete_message(id):
    if "admin" not in session:
        return redirect(url_for('index'))

    message = Contact.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()

    flash("Message deleted", "success")
    return redirect(url_for("admin_messages"))

# =============================
# PROJECT DETAIL VIEW
# =============================

@app.route("/project/<int:project_id>")
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)

    ip = request.remote_addr

    existing = ProjectView.query.filter_by(
        project_id=project_id,
        ip_address=ip
    ).first()

    if not existing:
        view = ProjectView(project_id=project_id, ip_address=ip)
        db.session.add(view)
        db.session.commit()

    details = ProjectDetail.query.filter_by(project_id=project_id).first()

    return render_template(
        "detailed_project.html",
        project=project,
        details=details
    )

# =============================
# CONTEXT PROCESSOR
# =============================

@app.context_processor
def inject_unread_messages():
    if 'admin' in session:
        unread_count = Contact.query.filter_by(is_read=False).count()
        return dict(unread_count=unread_count)
    return dict(unread_count=0)

# =============================
# site Map Route
# =============================


@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

# =============================
# Favicon Route
# =============================


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico')

# =============================
# Google Site Verification Route
# =============================


@app.route('/google706577dc96b54a38.html')
def google_verification():
    return send_from_directory('static', 'google706577dc96b54a38.html')

# =============================
# INITIALIZE DB AND CREATE ADMIN COMMAND
# =============================

with app.app_context():
    db.create_all()
    
import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

@app.cli.command("create-admin")
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin(username, password):
    """Create a new admin user"""

    existing_admin = Admin.query.filter_by(username=username).first()

    if existing_admin:
        print("❌ Admin already exists")
        return

    admin = Admin(
        username=username,
        password=generate_password_hash(password)
    )

    db.session.add(admin)
    db.session.commit()

    print("✅ Admin created successfully")


@app.before_request
def session_timeout():
    if 'admin' in session:
        session.modified = True

# =============================
#  RUN APP
# =============================

if __name__ == '__main__':
    app.run()