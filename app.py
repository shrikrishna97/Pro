from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
TIMEZONE = pytz.utc  # Change to your region (e.g., 'Asia/Kolkata')

# Database Models
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)

class UserResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    user_answer = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

# Initialize Database
with app.app_context():
    db.create_all()
    
    # Add sample questions
    # how many questions

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form.get("question_text")
        correct_answer = request.form.get("correct_answer")
        
        if question_text and correct_answer:
            new_question = Question(question_text=question_text, correct_answer=correct_answer)
            db.session.add(new_question)
            db.session.commit()
            return redirect(url_for('add_question'))

    questions = Question.query.all()
    return render_template('add_question.html', questions=questions)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        duration_minutes = int(request.form.get('duration', 10))
        start_time = datetime.now(TIMEZONE)
        session['quiz_start_time'] = start_time.isoformat()
        session['quiz_duration'] = duration_minutes
        session['user_id'] = str(datetime.timestamp(start_time))  # Unique session-based ID
        return redirect(url_for('quiz_page'))

    return render_template('quiz.html')

@app.route('/quiz/page', methods=['GET', 'POST'])
def quiz_page():
    if 'quiz_start_time' not in session:
        return redirect(url_for('quiz'))

    start_time = datetime.fromisoformat(session['quiz_start_time']).astimezone(TIMEZONE)
    duration = session['quiz_duration']
    end_time = start_time + timedelta(minutes=duration)
    now = datetime.now(TIMEZONE)

    if now >= end_time:
        return redirect(url_for('quiz_submit'))

    questions = Question.query.all()  # Fetch all questions

    if request.method == 'POST':
        user_id = session['user_id']
        for q in questions:
            user_answer = request.form.get(f"q{q.id}")
            if user_answer:
                is_correct = user_answer.strip().lower() == q.correct_answer.strip().lower()
                response = UserResponse(user_id=user_id, question_id=q.id, user_answer=user_answer, is_correct=is_correct)
                db.session.add(response)
        db.session.commit()
        return redirect(url_for('quiz_submit'))

    return render_template('quiz_timer.html', remaining_time=end_time - now, questions=questions)

@app.route('/quiz/submit', methods=['GET'])
def quiz_submit():
    return render_template('submit.html')

@app.route('/quiz/result', methods=['GET'])
def quiz_result():
    user_id = session.get('user_id')
    responses = UserResponse.query.filter_by(user_id=user_id).all()
    
    result_data = []
    for r in responses:
        question = Question.query.get(r.question_id)
        result_data.append({
            "question": question.question_text,
            "your_answer": r.user_answer,
            "correct_answer": question.correct_answer,
            "is_correct": r.is_correct
        })

    return render_template('result.html', results=result_data)

if __name__ == '__main__':
    app.run(debug=True)
