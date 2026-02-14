import pandas as pd
import json
import random
import os
import glob  # Serve per cercare i file

# --- CONFIGURAZIONE ---
GOOGLE_SCRIPT_URL = os.environ.get("MY_SECRET_URL", "URL_MANCANTE")

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
    except: return []

# --- SCANSIONE AUTOMATICA DEI FILE ---
# Cerca tutti i file che finiscono con .csv
csv_files = glob.glob("*.csv")

quiz_library = {}

for filename in csv_files:
    # Esempio filename: "math_algebra.csv"
    clean_name = filename.replace('.csv', '') # "math_algebra"
    
    # Carica i dati
    content = process_csv(filename)
    
    if content:
        # Salva nel dizionario con il nome del file come ID univoco
        quiz_library[clean_name] = content
        print(f"Caricato: {clean_name} ({len(content)} domande)")

json_output = json.dumps(quiz_library)

html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Archivio Verifiche</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f4f7f6; }}
        .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        h1, h2 {{ color: #2c3e50; text-align: center; }}
        
        /* LOGIN */
        input[type="email"] {{ width: 100%; padding: 15px; margin: 15px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }}
        .btn-primary {{ width: 100%; padding: 15px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1.1rem; }}
        .btn-primary:disabled {{ background: #ccc; cursor: wait; }}
        .error-msg {{ color: #d9534f; display: none; text-align: center; margin-top: 15px; padding: 10px; background: #fde8e8; border-radius: 4px; }}

        /* DASHBOARD COLUMNS */
        .dashboard-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 20px; }}
        @media (max-width: 700px) {{ .dashboard-container {{ grid-template-columns: 1fr; }} }}
        
        .column-header {{ font-size: 1.5rem; color: #555; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }}
        
        .quiz-card {{ 
            border: 1px solid #e0e0e0; 
            border-left: 5px solid #007bff; 
            padding: 15px; 
            margin-bottom: 15px; 
            border-radius: 6px; 
            background: white; 
            cursor: pointer; 
            transition: transform 0.2s, box-shadow 0.2s; 
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .quiz-card:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        
        /* Stili per card Math vs Physics */
        .type-math {{ border-left-color: #007bff; }}
        .type-physics {{ border-left-color: #e83e8c; }}
        
        .quiz-card.completed {{ border-left-color: #28a745; background-color: #f0fff4; opacity: 0.8; }}
        .status-badge {{ font-size: 0.8rem; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
        .badge-todo {{ background: #e7f1ff; color: #007bff; }}
        .badge-done {{ background: #d4edda; color: #28a745; }}

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
        <h1>Portale Studenti</h1>
        <p style="text-align:center">Accedi per vedere le verifiche disponibili.</p>
        <input type="email" id="input-email" placeholder="email@scuola.it">
        <button id="btn-login" class="btn-primary" onclick="attemptLogin()">Entra</button>
        <div id="login-error" class="error-msg"></div>
    </div>

    <div id="view-dashboard" class="card" style="display:none; max-width: 1200px;">
        <h2 id="welcome-msg">Benvenuto</h2>
        
        <div class="dashboard-container">
            <div>
                <div class="column-header">📐 Matematica</div>
                <div id="list-math"></div>
            </div>
            
            <div>
                <div class="column-header">⚛️ Fisica</div>
                <div id="list-physics"></div>
            </div>
        </div>
    </div>

    <div id="view-quiz" class="card" style="display:none;">
        <div style="overflow:hidden; margin-bottom:15px;">
            <span id="quiz-title" style="font-weight:bold; font-size:1.2em;">Titolo</span>
            <span id="timer">60:00</span>
        </div>
        <div id="question-container"></div>
        <div class="nav-container">
            <button id="prev-btn" class="btn-primary" style="background:#6c757d; width:auto;" onclick="move(-1)">Indietro</button>
            <button id="next-btn" class="btn-primary" style="width:auto;" onclick="move(1)">Avanti</button>
            <button id="submit-btn" class="btn-primary" style="background:#28a745; width:auto; display:none;" onclick="submitQuiz()">Consegna</button>
        </div>
        <div id="nav-scroll" class="nav-scroll"></div>
    </div>
    
    <div id="loading" class="card" style="display:none; text-align:center;"><h3>Salvataggio in corso...</h3></div>

    <script>
        const LIBRARY = {json_output}; // Contiene tutti i quiz caricati
        const GOOGLE_URL = "{GOOGLE_SCRIPT_URL}";

        let currentUser = "";
        let currentQuizId = "";
        let questions = [];
        let answers = [];
        let currentIdx = 0;
        let timeLeft = 3600;
        let timerInterval;

        async function attemptLogin() {{
            const email = document.getElementById('input-email').value.trim();
            const btn = document.getElementById('btn-login');
            
            if(!email.includes('@')) return showError("Email non valida.");
            btn.disabled = true;
            btn.innerText = "Caricamento...";
            
            try {{
                const response = await fetch(GOOGLE_URL + "?email=" + encodeURIComponent(email));
                const result = await response.json();

                if (!result.allowed) {{
                    showError("Accesso negato.");
                    btn.disabled = false;
                    btn.innerText = "Entra";
                    return;
                }}

                currentUser = email;
                document.getElementById('welcome-msg').innerText = "Studente: " + email;
                
                // GENERAZIONE DINAMICA DASHBOARD
                renderDashboard(result.completed);

                document.getElementById('view-login').style.display = 'none';
                document.getElementById('view-dashboard').style.display = 'block';

            }} catch (e) {{
                console.error(e);
                showError("Errore connessione.");
                btn.disabled = false;
                btn.innerText = "Entra";
            }}
        }}

        function renderDashboard(completedList) {{
            const mathList = document.getElementById('list-math');
            const physList = document.getElementById('list-physics');
            mathList.innerHTML = "";
            physList.innerHTML = "";

            // Ordina i quiz alfabeticamente
            const quizIds = Object.keys(LIBRARY).sort();

            quizIds.forEach(quizId => {{
                // quizId è tipo "math_algebra" o "physics_cinematica"
                const parts = quizId.split('_');
                const subject = parts[0]; // "math" o "physics"
                const topic = parts.slice(1).join(' ').toUpperCase(); // "ALGEBRA"
                
                const isDone = completedList.includes(quizId);
                
                // Creiamo la card HTML
                const card = document.createElement('div');
                card.className = `quiz-card type-${{subject}} ${{isDone ? 'completed' : ''}}`;
                
                card.innerHTML = `
                    <div>
                        <strong>${{topic}}</strong>
                    </div>
                    <div class="status-badge ${{isDone ? 'badge-done' : 'badge-todo'}}">
                        ${{isDone ? 'COMPLETATO' : 'AVVIA'}}
                    </div>
                `;

                if (!isDone) {{
                    card.onclick = () => startQuiz(quizId);
                }} else {{
                    card.style.cursor = "default";
                    card.title = "Hai già completato questa verifica";
                }}

                // Smistamento nelle colonne
                if (subject === 'math') mathList.appendChild(card);
                else if (subject === 'physics') physList.appendChild(card);
                // Se hai file tipo "chimica_...", puoi aggiungere un 'else' qui
            }});
        }}

        function startQuiz(quizId) {{
            currentQuizId = quizId;
            questions = LIBRARY[quizId];
            answers = new Array(questions.length).fill(null);
            currentIdx = 0;
            timeLeft = 3600;

            document.getElementById('view-dashboard').style.display = 'none';
            document.getElementById('view-quiz').style.display = 'block';
            
            // Formatta il titolo (es. math_algebra -> MATEMATICA: ALGEBRA)
            const parts = quizId.split('_');
            const prettyTitle = parts[0].toUpperCase() + ": " + parts.slice(1).join(' ').toUpperCase();
            document.getElementById('quiz-title').innerText = prettyTitle;
            
            setupNavScroll();
            renderQuestion();
            startTimer();
        }}
        
        // --- FUNZIONI STANDARD (Render, Move, Timer, Submit) ---
        function showError(msg) {{ const el = document.getElementById('login-error'); el.innerText = msg; el.style.display = 'block'; }}
        
        function renderQuestion() {{
            const q = questions[currentIdx];
            const container = document.getElementById('question-container');
            container.innerHTML = `<h3>Domanda ${{currentIdx + 1}}</h3><p>${{q.question}}</p>`;
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
            answers[currentIdx] = {{ question: questions[currentIdx].question, choice: ansObj.text, isCorrect: ansObj.correct }};
            updateNavScroll();
        }}

        function move(dir) {{ currentIdx += dir; renderQuestion(); }}
        function setupNavScroll() {{ const box = document.getElementById('nav-scroll'); box.innerHTML = ""; questions.forEach((_, i) => {{ const d = document.createElement('div'); d.className = 'nav-box'; d.innerText = i + 1; d.id = `nav-${{i}}`; d.onclick = () => {{ currentIdx = i; renderQuestion(); }}; box.appendChild(d); }}); }}
        function updateNavScroll() {{ questions.forEach((_, i) => {{ const el = document.getElementById(`nav-${{i}}`); el.className = 'nav-box'; if(answers[i]) el.classList.add('answered'); if(i === currentIdx) el.classList.add('current'); }}); document.getElementById(`nav-${{currentIdx}}`).scrollIntoView({{ behavior: 'smooth', inline: 'center' }}); }}
        
        function startTimer() {{
            clearInterval(timerInterval);
            timerInterval = setInterval(() => {{
                timeLeft--;
                const m = Math.floor(timeLeft / 60).toString().padStart(2, '0');
                const s = (timeLeft % 60).toString().padStart(2, '0');
                document.getElementById('timer').innerText = `${{m}}:${{s}}`;
                if(timeLeft <= 0) {{ clearInterval(timerInterval); submitQuiz(); }}
            }}, 1000);
        }}

        async function submitQuiz() {{
            clearInterval(timerInterval);
            document.getElementById('view-quiz').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            let score = 0;
            // CALCOLO DEL PUNTEGGIO MASSIMO
            // Ogni domanda vale 1.5 punti se corretta.
            // Quindi il max possibile è: numero_domande * 1.5
            let maxScore = questions.length * 1.5;

            let formattedAnswers = [];
            questions.forEach((q, i) => {{
                const a = answers[i];
                if(!a) formattedAnswers.push({{question: q.question, choice: "SKIPPED"}});
                else {{
                    if(a.isCorrect) score += 1.5; else score -= 0.4;
                    formattedAnswers.push({{question: a.question, choice: a.choice}});
                }}
            }});
            // Arrotonda a 1 decimale
            score = Math.round(score * 10) / 10;

            const payload = {{
                email: currentUser,
                subject: currentQuizId,
                score: score,
                maxScore: maxScore, // <--- INVIO DEL MAX SCORE
                answers: formattedAnswers
            }};
            
            try {{ 
                await fetch(GOOGLE_URL, {{ 
                    method: 'POST', 
                    mode: 'no-cors', 
                    body: JSON.stringify(payload) 
                }}); 
            }} catch(e) {{}}
            
            // CALCOLO VOTO IN DECIMI (Opzionale per visualizzazione)
            // Se vuoi mostrare anche il voto in decimi subito:
            // let voto = (score / maxScore) * 10;
            // voto = Math.round(voto * 10) / 10; // Arrotonda
            
            // MESSAGGIO FINALE AGGIORNATO
            alert("Verifica Completata!\n\nPunteggio: " + score + " / " + maxScore);
            
            location.reload();
        }}
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
    