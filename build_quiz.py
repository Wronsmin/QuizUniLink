import pandas as pd
import json
import random
import os
import glob

# --- CONFIGURATION ---
GOOGLE_SCRIPT_URL = os.environ.get("MY_SECRET_URL", "URL_MISSING")

def process_csv(filename):
    try:
        df = pd.read_csv(filename)
        if df.empty: return []
        data = []
        for _, row in df.iterrows():
            answers = [
                {"text": str(row['correct']), "correct": True},
                {"text": str(row['wrong1']), "correct": False},
                {"text": str(row['wrong2']), "correct": False},
                {"text": str(row['wrong3']), "correct": False}
            ]
            random.shuffle(answers)
            data.append({
                "question": str(row['question']),
                "answers": answers
            })
        return data
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

# --- FILE SCANNING ---
csv_files = glob.glob("*.csv")
quiz_library = {}

for filename in csv_files:
    # Example: "math_algebra.csv" -> "math_algebra"
    clean_name = filename.replace('.csv', '')
    content = process_csv(filename)
    if content:
        quiz_library[clean_name] = content

# Dump JSON ensuring ASCII characters are preserved correctly
json_output = json.dumps(quiz_library, ensure_ascii=False)

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Student Portal</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f4f7f6; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1, h2 { color: #2c3e50; text-align: center; }
        
        /* LOGIN STYLES */
        input[type="email"] { width: 100%; padding: 15px; margin: 15px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        .btn-primary { width: 100%; padding: 15px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1.1rem; }
        .btn-primary:disabled { background: #ccc; cursor: wait; }
        .error-msg { color: #d9534f; display: none; text-align: center; margin-top: 15px; padding: 10px; background: #fde8e8; border-radius: 4px; }

        /* DASHBOARD LAYOUT */
        .dashboard-container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 20px; }
        @media (max-width: 700px) { .dashboard-container { grid-template-columns: 1fr; } }
        
        .column-header { font-size: 1.5rem; color: #555; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }
        
        /* QUIZ CARDS */
        .quiz-card { 
            border: 1px solid #e0e0e0; 
            border-left: 5px solid #007bff; 
            padding: 15px; margin-bottom: 15px; border-radius: 6px; 
            background: white; cursor: pointer; 
            transition: transform 0.2s, box-shadow 0.2s; 
            display: flex; justify-content: space-between; align-items: center;
        }
        .quiz-card:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        
        .type-math { border-left-color: #007bff; }
        .type-physics { border-left-color: #e83e8c; }
        .quiz-card.completed { border-left-color: #28a745; background-color: #f0fff4; opacity: 0.9; cursor: default; }
        
        .card-content { display: flex; flex-direction: column; }
        .quiz-score { font-size: 0.9em; color: #28a745; font-weight: bold; margin-top: 5px; }
        
        .status-badge { font-size: 0.8rem; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .badge-todo { background: #e7f1ff; color: #007bff; }
        .badge-done { background: #d4edda; color: #28a745; }

        /* QUIZ INTERFACE */
        .nav-scroll { display: flex; overflow-x: auto; gap: 5px; padding: 10px 0; border-top: 1px solid #eee; margin-top: 20px; }
        .nav-box { min-width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; background: #eee; border-radius: 4px; cursor: pointer; font-size: 0.9em; }
        .nav-box.answered { background: #007bff; color: white; }
        .nav-box.current { border: 2px solid #ffc107; }
        
        .answer-btn { display: block; width: 100%; padding: 15px; margin: 10px 0; border: 2px solid #eee; border-radius: 6px; background: white; cursor: pointer; text-align: left; }
        .answer-btn.selected { border-color: #007bff; background: #e7f1ff; }
        
        .nav-container { display: flex; justify-content: space-between; margin-top: 20px; }
        #timer { font-family: monospace; font-size: 1.5rem; color: #d9534f; float: right; }
        #loading { display: none; text-align: center; }
    </style>
</head>
<body>

    <div id="view-login" class="card">
        <h1>Student Portal</h1>
        <p style="text-align:center">Please log in with your school email.</p>
        <input type="email" id="input-email" placeholder="name.surname@school.edu">
        <button id="btn-login" class="btn-primary" onclick="attemptLogin()">Login</button>
        <div id="login-error" class="error-msg"></div>
    </div>

    <div id="view-dashboard" class="card" style="display:none; max-width: 1200px;">
        <h2 id="welcome-msg">Welcome</h2>
        <div class="dashboard-container">
            <div>
                <div class="column-header">📐 Mathematics</div>
                <div id="list-math"></div>
            </div>
            <div>
                <div class="column-header">⚛️ Physics</div>
                <div id="list-physics"></div>
            </div>
        </div>
    </div>

    <div id="view-quiz" class="card" style="display:none;">
        <div style="overflow:hidden; margin-bottom:15px;">
            <span id="quiz-title" style="font-weight:bold; font-size:1.2em;">Title</span>
            <span id="timer">60:00</span>
        </div>
        <div id="question-container"></div>
        <div class="nav-container">
            <button id="prev-btn" class="btn-primary" style="background:#6c757d; width:auto;" onclick="move(-1)">Back</button>
            <button id="next-btn" class="btn-primary" style="width:auto;" onclick="move(1)">Next</button>
            <button id="submit-btn" class="btn-primary" style="background:#28a745; width:auto; display:none;" onclick="submitQuiz()">Submit Exam</button>
        </div>
        <div id="nav-scroll" class="nav-scroll"></div>
    </div>
    
    <div id="loading" class="card"><h3>Saving results...</h3></div>

    <script>
        const LIBRARY = __JSON_DATA__; 
        const GOOGLE_URL = "__GOOGLE_URL__";

        let currentUser = "";
        let currentQuizId = "";
        let questions = [];
        let answers = [];
        let currentIdx = 0;
        let timeLeft = 3600;
        let timerInterval;

        async function attemptLogin() {
            const email = document.getElementById('input-email').value.trim();
            const btn = document.getElementById('btn-login');
            
            if(!email.includes('@')) return showError("Invalid email address.");
            btn.disabled = true;
            btn.innerText = "Checking...";
            
            try {
                const response = await fetch(GOOGLE_URL + "?email=" + encodeURIComponent(email));
                const result = await response.json();

                if (!result.allowed) {
                    showError("Access denied. Email not found in whitelist.");
                    btn.disabled = false;
                    btn.innerText = "Login";
                    return;
                }

                currentUser = email;
                document.getElementById('welcome-msg').innerText = "Student: " + email;
                
                renderDashboard(result.completed); 

                document.getElementById('view-login').style.display = 'none';
                document.getElementById('view-dashboard').style.display = 'block';

            } catch (e) {
                console.error(e);
                showError("Connection error or invalid Script URL.");
                btn.disabled = false;
                btn.innerText = "Login";
            }
        }

        function renderDashboard(completedObj) {
            const mathList = document.getElementById('list-math');
            const physList = document.getElementById('list-physics');
            mathList.innerHTML = "";
            physList.innerHTML = "";
            
            if (!completedObj || Array.isArray(completedObj)) completedObj = {}; 

            const quizIds = Object.keys(LIBRARY).sort();

            if(quizIds.length === 0) {
                mathList.innerHTML = "<p>No quizzes available.</p>";
                return;
            }

            quizIds.forEach(quizId => {
                const parts = quizId.split('_');
                const subject = parts[0]; 
                const topic = parts.slice(1).join(' ').toUpperCase(); 
                
                const resultData = completedObj[quizId]; 
                const isDone = !!resultData;
                
                const card = document.createElement('div');
                card.className = `quiz-card type-${subject} ${isDone ? 'completed' : ''}`;
                
                let scoreText = "";
                if (isDone) {
                    const s = resultData.score !== undefined ? resultData.score : "?";
                    const m = resultData.maxScore ? resultData.maxScore : "?";
                    scoreText = `<div class="quiz-score">Score: ${s} / ${m}</div>`;
                }

                card.innerHTML = `
                    <div class="card-content">
                        <strong>${topic}</strong>
                        ${scoreText}
                    </div>
                    <div class="status-badge ${isDone ? 'badge-done' : 'badge-todo'}">
                        ${isDone ? 'COMPLETED' : 'START'}
                    </div>
                `;

                if (!isDone) {
                    card.onclick = () => startQuiz(quizId);
                } else {
                    card.title = "You have already completed this quiz";
                }

                if (subject === 'math') mathList.appendChild(card);
                else if (subject === 'physics') physList.appendChild(card);
                else mathList.appendChild(card); 
            });
        }

        function startQuiz(quizId) {
            currentQuizId = quizId;
            questions = LIBRARY[quizId];
            answers = new Array(questions.length).fill(null);
            currentIdx = 0;
            timeLeft = 3600;

            document.getElementById('view-dashboard').style.display = 'none';
            document.getElementById('view-quiz').style.display = 'block';
            
            const parts = quizId.split('_');
            const prettyTitle = parts[0].toUpperCase() + ": " + parts.slice(1).join(' ').toUpperCase();
            document.getElementById('quiz-title').innerText = prettyTitle;
            
            setupNavScroll();
            renderQuestion();
            startTimer();
        }

        function showError(msg) { 
            const el = document.getElementById('login-error'); 
            el.innerText = msg; 
            el.style.display = 'block'; 
        }

        function renderQuestion() {
            const q = questions[currentIdx];
            const container = document.getElementById('question-container');
            container.innerHTML = `<h3>Question ${currentIdx + 1}</h3><p>${q.question}</p>`;
            
            q.answers.forEach(ans => {
                const btn = document.createElement('button');
                btn.className = 'answer-btn';
                btn.innerHTML = ans.text;
                const saved = answers[currentIdx];
                if(saved && saved.text === ans.text) btn.classList.add('selected');
                btn.onclick = () => selectAnswer(btn, ans);
                container.appendChild(btn);
            });

            document.getElementById('prev-btn').disabled = (currentIdx === 0);
            if(currentIdx === questions.length - 1) {
                document.getElementById('next-btn').style.display = 'none';
                document.getElementById('submit-btn').style.display = 'inline-block';
            } else {
                document.getElementById('next-btn').style.display = 'inline-block';
                document.getElementById('submit-btn').style.display = 'none';
            }
            updateNavScroll();
            if(window.MathJax) MathJax.typesetPromise();
        }

        function selectAnswer(btn, ansObj) {
            document.querySelectorAll('.answer-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            answers[currentIdx] = { 
                question: questions[currentIdx].question, 
                choice: ansObj.text, 
                isCorrect: ansObj.correct 
            };
            updateNavScroll();
        }

        function move(dir) { currentIdx += dir; renderQuestion(); }
        
        function setupNavScroll() { 
            const box = document.getElementById('nav-scroll'); box.innerHTML = ""; 
            questions.forEach((_, i) => { 
                const d = document.createElement('div'); d.className = 'nav-box'; d.innerText = i + 1; d.id = `nav-${i}`; 
                d.onclick = () => { currentIdx = i; renderQuestion(); }; 
                box.appendChild(d); 
            }); 
        }
        
        function updateNavScroll() { 
            questions.forEach((_, i) => { 
                const el = document.getElementById(`nav-${i}`); el.className = 'nav-box'; 
                if(answers[i]) el.classList.add('answered'); 
                if(i === currentIdx) el.classList.add('current'); 
            }); 
            document.getElementById(`nav-${currentIdx}`).scrollIntoView({ behavior: 'smooth', inline: 'center' }); 
        }

        function startTimer() {
            clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                timeLeft--;
                const m = Math.floor(timeLeft / 60).toString().padStart(2, '0');
                const s = (timeLeft % 60).toString().padStart(2, '0');
                document.getElementById('timer').innerText = `${m}:${s}`;
                if(timeLeft <= 0) { clearInterval(timerInterval); submitQuiz(); }
            }, 1000);
        }

        async function submitQuiz() {
            clearInterval(timerInterval);
            document.getElementById('view-quiz').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            let score = 0;
            // 1.5 points per question
            let maxScore = questions.length * 1.5; 

            let formattedAnswers = [];
            questions.forEach((q, i) => {
                const a = answers[i];
                if(!a) formattedAnswers.push({question: q.question, choice: "SKIPPED"});
                else {
                    if(a.isCorrect) score += 1.5; else score -= 0.4;
                    formattedAnswers.push({question: a.question, choice: a.choice});
                }
            });
            score = Math.round(score * 10) / 10;

            const payload = { 
                email: currentUser, 
                subject: currentQuizId, 
                score: score, 
                maxScore: maxScore,
                answers: formattedAnswers 
            };

            try { 
                await fetch(GOOGLE_URL, { 
                    method: 'POST', 
                    mode: 'no-cors', 
                    body: JSON.stringify(payload) 
                }); 
            } catch(e) {}
            
            alert("Quiz Completed!\\n\\nScore: " + score + " / " + maxScore);
            location.reload();
        }
    </script>
</body>
</html>
"""

# --- SAFE DATA INJECTION ---
final_html = html_template.replace("__JSON_DATA__", json_output)
final_html = final_html.replace("__GOOGLE_URL__", GOOGLE_SCRIPT_URL)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Site generated in English!")