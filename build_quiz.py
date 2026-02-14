import pandas as pd
import json
import random
import os

# --- CONFIGURATION ---
GOOGLE_SCRIPT_URL = os.environ.get("MY_SECRET_URL", "URL_MANCANTE")

# Load questions
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
    <title>IMAT Exam Simulator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; background: #f0f2f5; }}
        .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        
        /* Header & Timer */
        .header-bar {{ display: flex; justify-content: space-between; margin-bottom: 20px; color: #555; font-weight: bold; font-size: 1.1em; }}
        #timer {{ color: #d9534f; font-family: monospace; font-size: 1.3em; }}
        
        /* Answers */
        .answer-btn {{ display: block; width: 100%; padding: 15px; margin: 10px 0; border: 2px solid #e0e0e0; border-radius: 8px; background: #fff; cursor: pointer; text-align: left; transition: 0.2s; font-size: 1rem; }}
        .answer-btn:hover {{ border-color: #aaa; background: #f9f9f9; }}
        .selected {{ border-color: #007bff; background-color: #e7f1ff; color: #0056b3; font-weight: 500; }}
        
        /* Main Navigation (Prev/Next) */
        .nav-container {{ display: flex; justify-content: space-between; margin-top: 30px; }}
        .nav-btn {{ padding: 10px 25px; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem; }}
        #prev-btn {{ background: #6c757d; color: white; }}
        #prev-btn:disabled {{ background: #ccc; cursor: not-allowed; }}
        #next-btn {{ background: #007bff; color: white; }}
        #submit-btn {{ background: #28a745; color: white; display: none; }}
        
        /* --- NEW: Scrollable Question Bar --- */
        .nav-scroll {{ 
            display: flex; 
            overflow-x: auto; 
            gap: 8px; 
            padding: 15px 5px; 
            margin-top: 20px; 
            border-top: 1px solid #eee; 
            scrollbar-width: thin; /* Firefox */
        }}
        /* Scrollbar styling for Chrome/Safari */
        .nav-scroll::-webkit-scrollbar {{ height: 8px; }}
        .nav-scroll::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 4px; }}
        
        .nav-box {{ 
            flex: 0 0 40px; 
            height: 40px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            background: #f8f9fa; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 0.9em; 
            user-select: none;
            transition: all 0.2s;
        }}
        
        /* States for the squares */
        .nav-box.answered {{ background-color: #007bff; color: white; border-color: #0056b3; }}
        .nav-box.current {{ border: 2px solid #ffc107; box-shadow: 0 0 5px rgba(255, 193, 7, 0.5); transform: scale(1.1); font-weight: bold; }}
        .nav-box:hover {{ background-color: #e2e6ea; }}

        /* Loading & Input */
        #loading {{ display: none; text-align: center; color: #0056b3; }}
        input[type="email"] {{ width: 100%; padding: 12px; margin: 15px 0; border: 1px solid #ddd; border-radius: 4px; }}
        #start-btn {{ width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1.1rem; }}
    </style>
</head>
<body>

    <div class="card">
        <div id="email-gate">
            <h2>IMAT Test Simulator</h2>
            <p><strong>Rules:</strong> +1.5 Correct, -0.4 Wrong, 0 Skipped.</p>
            <p><strong>Time:</strong> 60 Minutes.</p>
            <input type="email" id="user-email" placeholder="student@example.com">
            <button id="start-btn" onclick="startQuiz()">Start Exam</button>
        </div>

        <div id="quiz-content" style="display:none;">
            <div class="header-bar">
                <span id="q-progress">Question 1/{len(quiz_data)}</span>
                <span id="timer">60:00</span>
            </div>
            
            <div id="question-container"></div>
            
            <div class="nav-container">
                <button id="prev-btn" class="nav-btn" onclick="changeQuestion(-1)">Previous</button>
                <button id="next-btn" class="nav-btn" onclick="changeQuestion(1)">Next</button>
                <button id="submit-btn" class="nav-btn" onclick="finishQuiz()">Submit Exam</button>
            </div>

            <div id="nav-scroll" class="nav-scroll">
                </div>
        </div>

        <div id="loading">
            <h3>Submitting results...</h3>
            <p>Calculating IMAT Score...</p>
        </div>
    </div>

    <script>
        const GOOGLE_URL = "{GOOGLE_SCRIPT_URL}";
        const questions = {quiz_json};
        
        let timeLeft = 3600; 
        let currentIdx = 0;
        let userEmail = "";
        let userAnswers = new Array(questions.length).fill(null);

        function startQuiz() {{
            userEmail = document.getElementById('user-email').value;
            if(!userEmail.includes('@')) return alert("Invalid Email");
            
            document.getElementById('email-gate').style.display = 'none';
            document.getElementById('quiz-content').style.display = 'block';
            
            initNavScroll(); // Create the squares
            renderQuestion();
            startTimer();
        }}

        // --- NEW: Generate the squares ---
        function initNavScroll() {{
            const navContainer = document.getElementById('nav-scroll');
            navContainer.innerHTML = '';
            
            questions.forEach((_, idx) => {{
                const box = document.createElement('div');
                box.className = 'nav-box';
                box.innerText = idx + 1;
                box.id = 'nav-box-' + idx;
                box.onclick = () => jumpToQuestion(idx);
                navContainer.appendChild(box);
            }});
        }}

        // --- NEW: Jump Logic ---
        function jumpToQuestion(idx) {{
            currentIdx = idx;
            renderQuestion();
        }}

        // --- NEW: Update colors of squares ---
        function updateNavStyles() {{
            questions.forEach((_, idx) => {{
                const box = document.getElementById('nav-box-' + idx);
                // Reset classes
                box.className = 'nav-box';
                
                // Add Answered style
                if (userAnswers[idx] !== null) {{
                    box.classList.add('answered');
                }}
                
                // Add Current style
                if (idx === currentIdx) {{
                    box.classList.add('current');
                    // Auto-scroll to keep current box in view
                    box.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
                }}
            }});
        }}

        function renderQuestion() {{
            const q = questions[currentIdx];
            const container = document.getElementById('question-container');
            
            document.getElementById('q-progress').innerText = `Question ${{currentIdx + 1}} / ${{questions.length}}`;
            
            container.innerHTML = `<h3>${{q.question}}</h3>`;
            
            q.answers.forEach(ans => {{
                const btn = document.createElement('button');
                btn.className = 'answer-btn';
                btn.innerHTML = ans.text; 
                
                const savedAns = userAnswers[currentIdx];
                if(savedAns && savedAns.text === ans.text) {{
                    btn.classList.add('selected');
                }}
                
                btn.onclick = () => selectAnswer(btn, ans);
                container.appendChild(btn);
            }});

            document.getElementById('prev-btn').disabled = (currentIdx === 0);
            
            if(currentIdx === questions.length - 1) {{
                document.getElementById('next-btn').style.display = 'none';
                document.getElementById('submit-btn').style.display = 'block';
            }} else {{
                document.getElementById('next-btn').style.display = 'block';
                document.getElementById('submit-btn').style.display = 'none';
            }}

            if (window.MathJax) MathJax.typesetPromise();
            
            // Update the navigation bar styles every time we render
            updateNavStyles();
        }}

        function selectAnswer(btn, answerObj) {{
            document.querySelectorAll('.answer-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            
            userAnswers[currentIdx] = {{
                question: questions[currentIdx].question,
                text: answerObj.text,
                isCorrect: answerObj.correct
            }};
            
            // Immediately update the nav bar color
            updateNavStyles();
        }}

        function changeQuestion(direction) {{
            currentIdx += direction;
            renderQuestion();
        }}

        function startTimer() {{
            const timerInt = setInterval(() => {{
                timeLeft--;
                const m = Math.floor(timeLeft / 60);
                const s = timeLeft % 60;
                const mDisplay = m < 10 ? '0' + m : m;
                const sDisplay = s < 10 ? '0' + s : s;
                document.getElementById('timer').innerText = `${{mDisplay}}:${{sDisplay}}`;
                
                if(timeLeft <= 0) {{
                    clearInterval(timerInt);
                    finishQuiz();
                }}
            }}, 1000);
        }}

        async function finishQuiz() {{
            document.getElementById('quiz-content').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            let finalScore = 0;
            let formattedAnswers = [];

            questions.forEach((q, idx) => {{
                const ans = userAnswers[idx];
                if (ans === null) {{
                    formattedAnswers.push({{ question: q.question, choice: "SKIPPED", isCorrect: false }});
                }} else {{
                    if (ans.isCorrect) {{ finalScore += 1.5; }} 
                    else {{ finalScore -= 0.4; }}
                    formattedAnswers.push({{ question: ans.question, choice: ans.text, isCorrect: ans.isCorrect }});
                }}
            }});
            
            finalScore = Math.round(finalScore * 10) / 10;

            const payload = {{ email: userEmail, score: finalScore, answers: formattedAnswers }};

            try {{
                await fetch(GOOGLE_URL, {{
                    method: "POST",
                    mode: "no-cors",
                    headers: {{ "Content-Type": "text/plain;charset=utf-8" }},
                    body: JSON.stringify(payload)
                }});
                alert("Exam Submitted! Your IMAT Score: " + finalScore);
            }} catch(e) {{
                alert("Error connecting. Score: " + finalScore);
            }}
            location.reload();
        }}
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
print("Updated with Scrollable Nav Bar!")