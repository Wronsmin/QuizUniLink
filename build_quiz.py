import pandas as pd
import json
import random
import base64
import os

# --- CONFIGURATION ---
# Replace with your actual Google Web App URL from Phase 1
GOOGLE_SCRIPT_URL = os.environ.get("MY_SECRET_URL", "URL_MANCANTE")

# Load questions from your CSV
df = pd.read_csv('questions.csv')
quiz_data = []

for _, row in df.iterrows():
    answers = [
        {"text": str(row['correct']), "correct": True},
        {"text": str(row['wrong1']), "correct": False},
        {"text": str(row['wrong2']), "correct": False},
        {"text": str(row['wrong3']), "correct": False}
    ]
    random.shuffle(answers)
    quiz_data.append({
        "question": str(row['question']),
        "answers": answers
    })

quiz_json = json.dumps(quiz_data)

html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Math Quiz</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; background: #f4f7f6; }}
        .card {{ background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .answer-btn {{ display: block; width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; background: #fff; cursor: pointer; transition: 0.3s; font-size: 1.1em; }}
        .answer-btn:hover {{ background: #f0f0f0; }}
        .correct {{ background: #d4edda !important; border-color: #c3e6cb; }}
        .wrong {{ background: #f8d7da !important; border-color: #f5c6cb; }}
        #timer {{ color: #d9534f; font-weight: bold; font-size: 1.2em; float: right; }}
        #score-display {{ font-weight: bold; color: #2c3e50; }}
        input[type="email"] {{ width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }}
        button#start-btn {{ background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="card">
        <div id="email-gate">
            <h1>Math Challenge</h1>
            <p>Enter your email to begin the timed assessment.</p>
            <input type="email" id="user-email" placeholder="student@school.edu">
            <button id="start-btn" onclick="startQuiz()">Start Quiz</button>
        </div>

        <div id="quiz-content" style="display:none;">
            <div id="timer">Time: <span id="time">60</span>s</div>
            <div id="score-display">Score: <span id="current-score">0</span></div>
            <hr>
            <div id="question-container"></div>
            <button id="next-btn" onclick="nextQuestion()" style="display:none; background:#28a745; color:white; border:none; padding:10px 20px; margin-top:20px; border-radius:4px; cursor:pointer;">Next Question</button>
        </div>
        
        <div id="loading" style="display:none;"><h3>Submitting results to teacher...</h3></div>
    </div>

    <script>
        const GOOGLE_URL = "{GOOGLE_SCRIPT_URL}";
        const questions = {quiz_json};
        let currentIdx = 0, score = 0, userEmail = "", timeLeft = 60, userResponses = [];

        function startQuiz() {{
            userEmail = document.getElementById('user-email').value;
            if(!userEmail.includes('@')) return alert("Valid email required");
            document.getElementById('email-gate').style.display = 'none';
            document.getElementById('quiz-content').style.display = 'block';
            showQuestion();
            startTimer();
        }}

        function showQuestion() {{
            const q = questions[currentIdx];
            const container = document.getElementById('question-container');
            document.getElementById('next-btn').style.display = 'none';
            
            container.innerHTML = `<h3>Question ${{currentIdx + 1}}:</h3><p>${{q.question}}</p>`;
            q.answers.forEach(ans => {{
                const btn = document.createElement('button');
                btn.className = 'answer-btn';
                btn.innerHTML = ans.text; // Use innerHTML for LaTeX
                btn.onclick = () => selectAnswer(btn, ans.correct, ans.text, q.question);
                container.appendChild(btn);
            }});
            
            // Tell MathJax to look for new math symbols
            if (window.MathJax) MathJax.typesetPromise();
        }}

        function selectAnswer(btn, isCorrect, choiceText, questionText) {{
            const allBtns = document.querySelectorAll('.answer-btn');
            allBtns.forEach(b => b.disabled = true);

            userResponses.push({{ question: questionText, choice: choiceText, isCorrect: isCorrect }});

            if(isCorrect) {{ score += 10; btn.classList.add('correct'); }}
            else {{ score -= 5; btn.classList.add('wrong'); }}
            
            document.getElementById('current-score').innerText = score;
            document.getElementById('next-btn').style.display = 'block';
        }}

        function nextQuestion() {{
            currentIdx++;
            if(currentIdx < questions.length) showQuestion();
            else finishQuiz();
        }}

        function startTimer() {{
            const timerInt = setInterval(() => {{
                timeLeft--;
                document.getElementById('time').innerText = timeLeft;
                if(timeLeft <= 0) {{ clearInterval(timerInt); finishQuiz(); }}
            }}, 1000);
        }}

        async function finishQuiz() {{
            document.getElementById('quiz-content').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            const payload = {{ email: userEmail, score: score, answers: userResponses }};
            await fetch(GOOGLE_URL, {{ method: "POST", mode: "no-cors", body: JSON.stringify(payload) }});
            
            alert("Quiz Complete! Your score: " + score);
            location.reload();
        }}
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
print("index.html generated successfully!")
