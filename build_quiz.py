import pandas as pd
import json
import random
import os

# --- CONFIGURATION ---
GOOGLE_SCRIPT_URL = os.environ.get("MY_SECRET_URL", "URL_MANCANTE")

# Function to safely read CSVs
def process_csv(filename):
    if not os.path.exists(filename):
        print(f"NOTICE: {filename} not found. This subject will be hidden.")
        return [] # Return empty list if file missing
    
    try:
        df = pd.read_csv(filename)
        if df.empty:
            return []
            
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

# Load Subjects (Will be empty list [] if file doesn't exist)
math_data = process_csv('math.csv')
physics_data = process_csv('physics.csv')

master_data = {
    "math": math_data,
    "physics": physics_data
}
json_output = json.dumps(master_data)

html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Secure Assessment Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f4f7f6; }}
        .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        h1, h2 {{ color: #2c3e50; text-align: center; }}
        
        /* LOGIN */
        input[type="email"] {{ width: 100%; padding: 15px; margin: 15px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }}
        .btn-primary {{ width: 100%; padding: 15px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1.1rem; }}
        .btn-primary:disabled {{ background: #ccc; cursor: wait; }}
        
        .error-msg {{ color: #d9534f; display: none; text-align: center; margin-top: 15px; padding: 10px; background: #fde8e8; border-radius: 4px; }}

        /* DASHBOARD */
        .subject-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }}
        .subject-card {{ border: 2px solid #eee; padding: 20px; border-radius: 8px; text-align: center; cursor: pointer; transition: 0.3s; display: none; /* Hidden by default */ }}
        .subject-card:hover {{ border-color: #007bff; background: #f8f9fa; }}
        .subject-card.completed {{ border-color: #28a745; background: #e9f7ef; cursor: not-allowed; opacity: 0.7; }}
        .subject-icon {{ font-size: 3rem; margin-bottom: 10px; display: block; }}
        
        /* QUIZ UI */
        .nav-scroll {{ display: flex; overflow-x: auto; gap: 5px; padding: 10px 0; border-top: 1px solid #eee; margin-top: 20px; }}
        .nav-box {{ min-width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; background: #eee; border-radius: 4px; cursor: pointer; font-size: 0.9em; }}
        .nav-box.answered {{ background: #007bff; color: white; }}
        .nav-box.current {{ border: 2px solid #ffc107; }}
        
        .answer-btn {{ display: block; width: 100%; padding: 15px; margin: 10px 0; border: 2px solid #eee; border-radius: 6px; background: white; cursor: pointer; text-align: left; }}
        .answer-btn.selected {{ border-color: #007bff; background: #e7f1ff; }}
        .nav-container {{ display: flex; justify-content: space-between; margin-top: 20px; }}
        #timer {{ font-family: monospace; font-size: 1.5rem; color: #d9534f; float: right; }}
    </style>
</head>
<body>

    <div id="view-login" class="card">
        <h1>Student Assessment Portal</h1>
        <p style="text-align:center">Enter your email to verify eligibility.</p>
        <input type="email" id="input-email" placeholder="student@school.edu">
        <button id="btn-login" class="btn-primary" onclick="attemptLogin()">Verify & Login</button>
        <div id="login-error" class="error-msg"></div>
    </div>

    <div id="view-dashboard" class="card" style="display:none;">
        <h2 id="welcome-msg">Welcome</h2>
        <div class="subject-grid">
            <div id="card-math" class="subject-card" onclick="startSubject('math')">
                <span class="subject-icon">📐</span>
                <h3>Mathematics</h3>
                <div id="status-math">Status: <b>Ready</b></div>
            </div>
            <div id="card-physics" class="subject-card" onclick="startSubject('physics')">
                <span class="subject-icon">⚛️</span>
                <h3>Physics</h3>
                <div id="status-physics">Status: <b>Ready</b></div>
            </div>
        </div>
        <p id="no-exams-msg" style="display:none; text-align:center; color:#777; margin-top:20px;">No assessments are currently available.</p>
    </div>

    <div id="view-quiz" class="card" style="display:none;">
        <div style="overflow:hidden; margin-bottom:15px;">
            <span id="subject-title" style="font-weight:bold; font-size:1.2em;">Subject</span>
            <span id="timer">60:00</span>
        </div>
        <div id="question-container"></div>
        <div class="nav-container">
            <button id="prev-btn" class="btn-primary" style="background:#6c757d; width:auto;" onclick="move(-1)">Prev</button>
            <button id="next-btn" class="btn-primary" style="width:auto;" onclick="move(1)">Next</button>
            <button id="submit-btn" class="btn-primary" style="background:#28a745; width:auto; display:none;" onclick="submitSubject()">Submit Subject</button>
        </div>
        <div id="nav-scroll" class="nav-scroll"></div>
    </div>

    <div id="loading" class="card" style="display:none; text-align:center;">
        <h3>Processing...</h3>
    </div>

    <script>
        const DATA = {json_output};
        const GOOGLE_URL = "{GOOGLE_SCRIPT_URL}";
        
        let currentUser = "";
        let currentSubject = "";
        let questions = [];
        let answers = [];
        let currentIdx = 0;
        let timeLeft = 3600;
        let timerInterval;

        async function attemptLogin() {{
            const email = document.getElementById('input-email').value.trim();
            const btn = document.getElementById('btn-login');
            
            if(!email.includes('@')) return showError("Please enter a valid email.");

            btn.disabled = true;
            btn.innerText = "Checking Database...";
            document.getElementById('login-error').style.display = 'none';

            try {{
                // 1. Check Google Database
                const response = await fetch(GOOGLE_URL + "?email=" + encodeURIComponent(email));
                const result = await response.json();

                if (!result.allowed) {{
                    showError("Access Denied: Email not authorized.");
                    btn.disabled = false;
                    btn.innerText = "Verify & Login";
                    return;
                }}

                // 2. Login Success
                currentUser = email;
                document.getElementById('welcome-msg').innerText = "Student: " + email;
                
                // 3. Configure Dashboard (Show only available subjects)
                let visibleCount = 0;
                
                // Setup MATH
                if (DATA.math && DATA.math.length > 0) {{
                    document.getElementById('card-math').style.display = 'block';
                    if (result.math_done) markCardComplete('math');
                    visibleCount++;
                }}
                
                // Setup PHYSICS
                if (DATA.physics && DATA.physics.length > 0) {{
                    document.getElementById('card-physics').style.display = 'block';
                    if (result.physics_done) markCardComplete('physics');
                    visibleCount++;
                }}
                
                if (visibleCount === 0) {{
                    document.getElementById('no-exams-msg').style.display = 'block';
                }}

                document.getElementById('view-login').style.display = 'none';
                document.getElementById('view-dashboard').style.display = 'block';

            }} catch (e) {{
                console.error(e);
                showError("Connection Error: Could not reach database.");
                btn.disabled = false;
                btn.innerText = "Verify & Login";
            }}
        }}

        function showError(msg) {{
            const el = document.getElementById('login-error');
            el.innerText = msg;
            el.style.display = 'block';
        }}

        function markCardComplete(subj) {{
            const card = document.getElementById(`card-${{subj}}`);
            card.classList.add('completed');
            card.onclick = null;
            document.getElementById(`status-${{subj}}`).innerHTML = "<b style='color:green'>COMPLETED</b>";
        }}

        function startSubject(subject) {{
            currentSubject = subject;
            questions = DATA[subject];
            
            answers = new Array(questions.length).fill(null);
            currentIdx = 0;
            timeLeft = 3600;

            document.getElementById('view-dashboard').style.display = 'none';
            document.getElementById('view-quiz').style.display = 'block';
            document.getElementById('subject-title').innerText = subject.toUpperCase();
            
            setupNavScroll();
            renderQuestion();
            startTimer();
        }}

        function renderQuestion() {{
            const q = questions[currentIdx];
            const container = document.getElementById('question-container');
            container.innerHTML = `<h3>Question ${{currentIdx + 1}}</h3><p>${{q.question}}</p>`;
            
            q.answers.forEach(ans => {{
                const btn = document.createElement('button');
                btn.className = 'answer-btn';
                btn.innerHTML = ans.text;
                
                const saved = answers[currentIdx];
                if(saved && saved.text === ans.text) btn.classList.add('selected');
                
                btn.onclick = () => selectAnswer(btn, ans);
                container.appendChild(btn);
            }});

            document.getElementById('prev-btn').disabled = (currentIdx === 0);
            if(currentIdx === questions.length - 1) {{
                document.getElementById('next-btn').style.display = 'none';
                document.getElementById('submit-btn').style.display = 'inline-block';
            }} else {{
                document.getElementById('next-btn').style.display = 'inline-block';
                document.getElementById('submit-btn').style.display = 'none';
            }}

            updateNavScroll();
            if(window.MathJax) MathJax.typesetPromise();
        }}

        function selectAnswer(btn, ansObj) {{
            document.querySelectorAll('.answer-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            answers[currentIdx] = {{
                question: questions[currentIdx].question,
                choice: ansObj.text,
                isCorrect: ansObj.correct
            }};
            updateNavScroll();
        }}

        function move(dir) {{
            currentIdx += dir;
            renderQuestion();
        }}

        function setupNavScroll() {{
            const box = document.getElementById('nav-scroll');
            box.innerHTML = "";
            questions.forEach((_, i) => {{
                const d = document.createElement('div');
                d.className = 'nav-box';
                d.innerText = i + 1;
                d.id = `nav-${{i}}`;
                d.onclick = () => {{ currentIdx = i; renderQuestion(); }};
                box.appendChild(d);
            }});
        }}

        function updateNavScroll() {{
            questions.forEach((_, i) => {{
                const el = document.getElementById(`nav-${{i}}`);
                el.className = 'nav-box';
                if(answers[i]) el.classList.add('answered');
                if(i === currentIdx) el.classList.add('current');
            }});
            document.getElementById(`nav-${{currentIdx}}`).scrollIntoView({{ behavior: 'smooth', inline: 'center' }});
        }}

        function startTimer() {{
            clearInterval(timerInterval);
            timerInterval = setInterval(() => {{
                timeLeft--;
                const m = Math.floor(timeLeft / 60).toString().padStart(2, '0');
                const s = (timeLeft % 60).toString().padStart(2, '0');
                document.getElementById('timer').innerText = `${{m}}:${{s}}`;
                
                if(timeLeft <= 0) {{
                    clearInterval(timerInterval);
                    submitSubject();
                }}
            }}, 1000);
        }}

        async function submitSubject() {{
            clearInterval(timerInterval);
            document.getElementById('view-quiz').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            let score = 0;
            let formattedAnswers = [];
            questions.forEach((q, i) => {{
                const a = answers[i];
                if(!a) {{
                    formattedAnswers.push({{question: q.question, choice: "SKIPPED"}});
                }} else {{
                    if(a.isCorrect) score += 1.5; else score -= 0.4;
                    formattedAnswers.push({{question: a.question, choice: a.choice}});
                }}
            }});
            score = Math.round(score * 10) / 10;

            const payload = {{
                email: currentUser,
                subject: currentSubject,
                score: score,
                answers: formattedAnswers
            }};

            try {{
                await fetch(GOOGLE_URL, {{
                    method: 'POST',
                    mode: 'no-cors',
                    body: JSON.stringify(payload)
                }});
                alert("Subject Submitted Successfully!");
            }} catch(e) {{
                alert("Submission sent.");
            }}
            
            location.reload();
        }}
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)