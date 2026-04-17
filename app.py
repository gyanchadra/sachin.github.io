from flask import Flask, request, redirect, session, send_from_directory, jsonify
import mysql.connector
from pypdf import PdfReader
from docx import Document
import io
import os
import re
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "secret123"

# ================= GEMINI SETUP =================
genai.configure(api_key="Gemini")
model = genai.GenerativeModel("gemini-1.5-flash")

# ================= MYSQL CONNECTION =================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sachin@123",
    database="resume_db"
)

cursor = db.cursor()

# ================= HOME PAGE =================
@app.route('/')
def home():
    return send_from_directory('HTML', 'index.html')

# ================= LOGIN PAGE =================
@app.route('/login-page')
def login_page():
    return send_from_directory('HTML', 'login.html')

# ================= ABOUT PAGE =================
@app.route('/about')
def about():
    return send_from_directory('HTML', 'about.html')

# ================= CONTACT PAGE =================
@app.route('/contact')
def contact():
    return send_from_directory('HTML', 'contact.html')

# ================= ANALYZER PAGE =================
@app.route('/analyzer')
def analyzer():
    if 'user' in session:
        return send_from_directory('HTML', 'analyzer.html')
    return redirect('/login-page')

# ================= JOB MATCH PAGE =================
@app.route('/jobmatch')
def jobmatch():
    if 'user' in session:
        return send_from_directory('HTML', 'jobmatch.html')
    return redirect('/login-page')

# ================= BUILDER PAGE =================
@app.route('/builder')
def builder():
    if 'user' in session:
        return send_from_directory('HTML', 'builder.html')
    return redirect('/login-page')

# ================= SETTINGS PAGE =================
@app.route('/setting')
def setting():
    if 'user' in session:
        return send_from_directory('HTML', 'setting.html')
    return redirect('/login-page')

# ================= USER NAME API =================
@app.route('/get-user-name')
def get_user_name():
    if 'name' in session:
        return jsonify({"name": session['name']})
    return jsonify({"name": "User"})

# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return send_from_directory('HTML', 'index.html')
    return redirect('/login-page')

# ================= RESUME FORM PAGE =================
@app.route('/resume-form')
def resume_form():
    if 'user' in session:
        return send_from_directory('HTML', 'resumeform.html')
    return redirect('/login-page')

# ================= STATIC FILES =================
@app.route('/CSS/<path:filename>')
def css_files(filename):
    return send_from_directory('CSS', filename)

@app.route('/JS/<path:filename>')
def js_files(filename):
    return send_from_directory('JS', filename)

@app.route('/IMAGES/<path:filename>')
def image_files(filename):
    return send_from_directory('IMAGES', filename)

# ================= RESUME UPLOAD =================
@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    file = request.files.get('file')

    if not file or file.filename == '':
        return """
        <div class="result-card error">
            <h3>❌ No File Selected</h3>
            <div class="result-content">Please select a file first.</div>
        </div>
        """

    filename = file.filename.lower()
    file_ext = filename.split('.')[-1]

    allowed_extensions = ['pdf', 'docx', 'doc']
    if file_ext not in allowed_extensions:
        return """
        <div class="result-card error">
            <h3>❌ Invalid File Type</h3>
            <div class="result-content">Only PDF, DOCX, and DOC files are allowed.</div>
        </div>
        """

    def is_resume_text(text: str) -> bool:
        text = text.lower()

        resume_keywords = [
            "education", "skills", "experience", "projects",
            "objective", "summary", "internship", "languages",
            "email", "phone", "address", "career"
        ]

        found = sum(1 for word in resume_keywords if word in text)
        return found >= 3

    # PDF check
    if file_ext == 'pdf':
        try:
            file_bytes = file.read()
            pdf = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(pdf.pages)

            if total_pages != 1:
                return f"""
                <div class="result-card error">
                    <h3>❌ Invalid Resume Length</h3>
                    <div class="result-content">
                        Resume must be exactly 1 page.<br>
                        Your PDF has <strong>{total_pages}</strong> pages.
                    </div>
                </div>
                """

            text = ""
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + " "

            if not text.strip():
                return """
                <div class="result-card error">
                    <h3>❌ Unreadable PDF</h3>
                    <div class="result-content">
                        Could not read text from PDF. Please upload a text-based PDF resume.
                    </div>
                </div>
                """

            if not is_resume_text(text):
                return """
                <div class="result-card error">
                    <h3>❌ Invalid Resume</h3>
                    <div class="result-content">
                        Uploaded PDF does not look like a resume.
                    </div>
                </div>
                """

            prompt = f"""
You are an ATS resume analyzer.

Analyze the following resume and return in clean HTML format using only simple tags like:
<h4>, <p>, <ul>, <li>, <strong>

Return:
1. ATS Score out of 100
2. 3 strengths
3. 3 weaknesses
4. Missing skills
5. 3 improvement suggestions

Keep it short, professional, and easy to read.

Resume:
{text}
"""

            response = model.generate_content(prompt)
            analysis = response.text

            return f"""
            <div class="result-card success">
                <h3>✅ Resume Verified Successfully</h3>
                <div class="result-content">
                    {analysis}
                </div>
            </div>
            """

        except Exception as e:
            return f"""
            <div class="result-card error">
                <h3>❌ PDF Error</h3>
                <div class="result-content">
                    {str(e)}
                </div>
            </div>
            """

    # DOCX check
    elif file_ext == 'docx':
        try:
            file_bytes = file.read()
            doc = Document(io.BytesIO(file_bytes))

            text = " ".join([para.text for para in doc.paragraphs if para.text.strip()])

            if not text.strip():
                return """
                <div class="result-card error">
                    <h3>❌ Unreadable DOCX</h3>
                    <div class="result-content">DOCX file is empty or unreadable.</div>
                </div>
                """

            if not is_resume_text(text):
                return """
                <div class="result-card error">
                    <h3>❌ Invalid Resume</h3>
                    <div class="result-content">Uploaded DOCX does not look like a resume.</div>
                </div>
                """

            word_count = len(re.findall(r'\w+', text))

            if word_count > 700:
                return """
                <div class="result-card error">
                    <h3>❌ Resume Too Long</h3>
                    <div class="result-content">
                        DOCX file looks longer than 1 page. Please upload a 1-page resume.
                    </div>
                </div>
                """

            prompt = f"""
You are an ATS resume analyzer.

Analyze the following resume and return in clean HTML format using only simple tags like:
<h4>, <p>, <ul>, <li>, <strong>

Return:
1. ATS Score out of 100
2. 3 strengths
3. 3 weaknesses
4. Missing skills
5. 3 improvement suggestions

Keep it short, professional, and easy to read.

Resume:
{text}
"""

            response = model.generate_content(prompt)
            analysis = response.text

            return f"""
            <div class="result-card success">
                <h3>✅ Resume Verified Successfully</h3>
                <div class="result-content">
                    {analysis}
                </div>
            </div>
            """

        except Exception as e:
            return f"""
            <div class="result-card error">
                <h3>❌ DOCX Error</h3>
                <div class="result-content">
                    {str(e)}
                </div>
            </div>
            """

    # DOC check
    elif file_ext == 'doc':
        return """
        <div class="result-card error">
            <h3>❌ Unsupported Verification</h3>
            <div class="result-content">
                DOC format selected, but strict page/resume verification is not supported.<br>
                Please upload PDF or DOCX.
            </div>
        </div>
        """

# ================= REGISTER =================
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    sql = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
    values = (name, email, password)

    try:
        cursor.execute(sql, values)
        db.commit()

        session['user'] = email
        session['name'] = name
        return redirect('/builder')

    except mysql.connector.IntegrityError:
        return redirect('/login-page?error=exists')

# ================= LOGIN =================
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    sql = "SELECT name, email FROM users WHERE email=%s AND password=%s"
    values = (email, password)

    cursor.execute(sql, values)
    user = cursor.fetchone()

    if user:
        session['name'] = user[0]
        session['user'] = user[1]
        return redirect('/builder')
    else:
        return redirect('/login-page?error=invalid')

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    email = session.get('user')

    if email:
        sql = "DELETE FROM users WHERE email=%s"
        values = (email,)
        cursor.execute(sql, values)
        db.commit()

    session.pop('user', None)
    session.pop('name', None)

    return redirect('/')

# ================= RUN APP =================
if __name__ == "__main__":
    app.run(debug=True)