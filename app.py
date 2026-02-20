from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
from sheets_handler import SheetsHandler
from utils import generate_uuid, generate_qr_code
import pandas as pd
import io
import zipfile
from functools import wraps
import datetime
import traceback

app = Flask(__name__)
app.secret_key = 'super_secret_key' # Change this in production

# Configuration
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

CREDENTIALS_FILE = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
SHEET_ID = os.environ.get('SHEET_ID', 'your_sheet_id')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'secret')

print(f"\n--- ENV DEBUG ---")
print(f"Working Dir: {os.getcwd()}")
print(f"Env Path: {env_path} (Exists: {os.path.exists(env_path)})")
print(f"Sheet ID: {'...' + SHEET_ID[-5:] if SHEET_ID else 'None'}")
print(f"Credentials File: {CREDENTIALS_FILE}")
print(f"------------------\n")

# Initialize Sheets Handler
sheets_handler = SheetsHandler(CREDENTIALS_FILE, SHEET_ID)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            from flask import session
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    from flask import session
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def dashboard():
    stats = sheets_handler.get_stats()
    students = sheets_handler.get_all_records()
    return render_template('dashboard.html', stats=stats, students=students)

@app.route('/admin/upload', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('dashboard'))
    
    if file:
        try:
            # Read CSV with fallback for different encodings and automatic separator detection
            try:
                # First attempt with default settings
                df = pd.read_csv(file)
            except (UnicodeDecodeError, pd.errors.ParserError):
                try:
                    # Second attempt with latin-1 and auto-separator detection
                    file.seek(0)
                    df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python')
                except Exception as e:
                    # Final attempt if still failing, try skipping bad lines
                    file.seek(0)
                    df = pd.read_csv(file, encoding='latin-1', sep=None, engine='python', on_bad_lines='skip')
                    flash('Some lines were skipped due to formatting issues.')
            
            # Check required columns
            required_cols = ['Student_ID', 'Name', 'Reg_No', 'Section']
            if not all(col in df.columns for col in required_cols):
                flash(f'CSV must contain columns: {", ".join(required_cols)}')
                return redirect(url_for('dashboard'))

            # Generate Ticket IDs and Status
            df['Ticket_ID'] = [generate_uuid() for _ in range(len(df))]
            df['Status'] = 'NOT_ENTERED'
            df['Entry_Time'] = ''

            # Generate QR Codes
            base_dir = os.path.dirname(os.path.abspath(__file__))
            qr_folder = os.path.join(base_dir, 'static', 'qrcodes')
            if not os.path.exists(qr_folder):
                os.makedirs(qr_folder)

            for index, row in df.iterrows():
                qr_path = os.path.join(qr_folder, f"{row['Ticket_ID']}.png")
                generate_qr_code(
                    row['Ticket_ID'], 
                    output_path=qr_path, 
                    name=row['Name'], 
                    reg_no=row['Reg_No'], 
                    student_id=row['Student_ID'],
                    section=row['Section']
                )
            
            # Convert to list of lists for Sheets
            students_data = df[['Student_ID', 'Name', 'Reg_No', 'Section', 'Ticket_ID', 'Status', 'Entry_Time']].values.tolist()
            
            # Upload to Sheets
            sheets_handler.add_students(students_data)
            
            flash('Students uploaded successfully!')
        except Exception as e:
            error_msg = str(e)
            print(f"\n{'='*60}")
            print(f"UPLOAD ERROR DETAILS:")
            traceback_str = traceback.format_exc()
            print(traceback_str)
            print(f"{'='*60}\n")
            flash(f'Error Processing Upload: {error_msg}')
            return redirect(url_for('dashboard'))
            
    return redirect(url_for('dashboard'))

@app.route('/admin/download_qrs')
@login_required
def download_qrs():
    students = sheets_handler.get_all_records()
    
    if not students:
        flash('No students found to generate QR codes.')
        return redirect(url_for('dashboard'))
        
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for student in students:
            ticket_id = student.get('Ticket_ID')
            name = student.get('Name')
            reg_no = student.get('Reg_No')
            student_id = student.get('Student_ID')
            
            if ticket_id:
                # Generate labeled QR
                img = generate_qr_code(
                    ticket_id, 
                    name=name, 
                    reg_no=reg_no, 
                    student_id=student_id,
                    section=student.get('Section')
                )
                
                # Save image to buffer to add to zip
                img_io = io.BytesIO()
                img.save(img_io, 'PNG')
                img_io.seek(0)
                
                # Use name in filename for better usability
                filename = f"{name.replace(' ', '_')}_{ticket_id}.png" if name else f"{ticket_id}.png"
                zipf.writestr(filename, img_io.getvalue())
    
    memory_file.seek(0)
    return send_file(memory_file, download_name='labeled_qrcodes.zip', as_attachment=True)

@app.route('/admin/qr/<ticket_id>')
@login_required
def download_single_qr(ticket_id):
    # Fetch student details to get labels
    student, _ = sheets_handler.get_student_by_ticket(ticket_id)
    
    if student:
        # Generate QR code on the fly with labels
        img = generate_qr_code(
            ticket_id, 
            name=student.get('Name'), 
            reg_no=student.get('Reg_No'), 
            student_id=student.get('Student_ID'),
            section=student.get('Section')
        )
        
        # Save to buffer
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        # Determine a safe filename
        filename = f"qr_{student.get('Name', ticket_id).replace(' ', '_')}.png"
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=filename)
    
    flash(f'Student records not found for ID: {ticket_id}')
    return redirect(url_for('dashboard'))

@app.route('/admin/export/logs')
@login_required
def export_logs():
    logs = sheets_handler.get_scan_logs()
    if not logs:
        flash('No scan logs available to export')
        return redirect(url_for('dashboard'))
    
    df = pd.DataFrame(logs)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    # Convert to bytes for sending
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'scan_logs_{timestamp}.csv'
    )

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/api/verify', methods=['POST'])
def verify_ticket():
    data = request.json
    ticket_id = data.get('ticket_id')
    gate_type = data.get('gate_type')
    
    if not ticket_id or not gate_type:
        return jsonify({'status': 'error', 'message': 'Missing ticket_id or gate_type'}), 400
        
    student, row_index = sheets_handler.get_student_by_ticket(ticket_id)
    
    if not student:
        sheets_handler.log_scan(ticket_id, gate_type, 'INVALID')
        return jsonify({'status': 'invalid', 'message': 'Invalid Ticket'}), 200 # Return 200 so frontend handles it gracefully
        
    current_status = student.get('Status')
    
    # Logic
    if gate_type == 'IN':
        if current_status == 'NOT_ENTERED':
            sheets_handler.update_status(row_index, 'IN', 'IN')
            sheets_handler.log_scan(ticket_id, gate_type, 'SUCCESS')
            return jsonify({
                'status': 'valid',
                'student': {
                    'student_id': student.get('Student_ID'),
                    'name': student.get('Name'),
                    'reg_no': student.get('Reg_No'),
                    'section': student.get('Section')
                }
            })
        elif current_status == 'IN':
            sheets_handler.log_scan(ticket_id, gate_type, 'DUPLICATE')
            return jsonify({
                'status': 'already_used',
                'message': 'Already Entered',
                'entry_time': student.get('Entry_Time')
            })
            

    return jsonify({'status': 'error', 'message': 'Unknown error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
