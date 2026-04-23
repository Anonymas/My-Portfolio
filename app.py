from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/project_images/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

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
    date = db.Column(db.String(50), default='March 2025')
    author = db.Column(db.String(100), default='Dennis Githinji')
    views = db.Column(db.String(50), default='1.2k')
    comments = db.Column(db.String(50), default='24')


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
    
    # Relationship
    project = db.relationship('Project', backref=db.backref('details', uselist=False, lazy=True))

# =============================
# AUTH ROUTES
# =============================

@app.route('/admin-login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']

    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password, password):
        session['admin'] = True
        flash("Login successful!", "success")
        return redirect(url_for('admin_dashboard'))

    flash("Invalid credentials", "error")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Logged out successfully", "success")
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
    # Count projects with details
    projects_with_details = [p for p in projects if p.details]
    
    return render_template('admin_dashboard.html', 
                         projects=projects,
                         projects_with_details=projects_with_details,
                         total_views='1.2k')

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

    db.session.commit()

    flash("Project updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete/<int:id>')
def delete_project(id):
    if 'admin' not in session:
        return redirect(url_for('index'))

    project = Project.query.get_or_404(id)
    
    # Delete associated details first
    if project.details:
        db.session.delete(project.details)
    
    db.session.delete(project)
    db.session.commit()

    flash("Project deleted successfully!", "success")
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

from flask import send_from_directory

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

# =============================
# Favicon Route
# =============================

from flask import send_from_directory

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico')

# =============================
# Google Site Verification Route
# =============================

from flask import send_from_directory

@app.route('/google706577dc96b54a38.html')
def google_verification():
    return send_from_directory('static', 'google706577dc96b54a38.html')

# =============================
# INITIALIZE DB AND RUN APP
# =============================

with app.app_context():
    db.create_all()
    
    
if __name__ == '__main__':
    app.run()