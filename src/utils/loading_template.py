"""
HTML templates for loading screens in the browser.
"""

def get_loading_template(language="English"):
    """
    Get the HTML template for the loading screen.
    
    Args:
        language (str): The language to use for the loading screen
        
    Returns:
        str: The HTML template for the loading screen
    """
    # Get the appropriate messages based on language
    if language == "Italiano":
        title = "Generazione del PDF in corso..."
        processing = "Elaborazione in corso"
        please_wait = "Attendere prego"
        generating = "Generazione del documento"
        formatting = "Formattazione del contenuto"
        optimizing = "Ottimizzazione del layout"
        finalizing = "Finalizzazione del PDF"
    else:  # Default to English
        title = "PDF Generation in Progress..."
        processing = "Processing"
        please_wait = "Please wait"
        generating = "Generating document"
        formatting = "Formatting content"
        optimizing = "Optimizing layout"
        finalizing = "Finalizing PDF"
    
    # HTML template with CSS animations
    return f"""
    <!DOCTYPE html>
    <html lang="{language.lower()[:2]}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                color: #333;
            }}
            
            .container {{
                text-align: center;
                background-color: white;
                border-radius: 10px;
                padding: 40px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                width: 80%;
                max-width: 600px;
            }}
            
            h1 {{
                color: #2c3e50;
                margin-bottom: 30px;
                font-weight: 500;
            }}
            
            .loader {{
                margin: 30px auto;
                position: relative;
                width: 80px;
                height: 80px;
            }}
            
            .loader div {{
                position: absolute;
                top: 33px;
                width: 13px;
                height: 13px;
                border-radius: 50%;
                background: #3498db;
                animation-timing-function: cubic-bezier(0, 1, 1, 0);
            }}
            
            .loader div:nth-child(1) {{
                left: 8px;
                animation: loader1 0.6s infinite;
            }}
            
            .loader div:nth-child(2) {{
                left: 8px;
                animation: loader2 0.6s infinite;
            }}
            
            .loader div:nth-child(3) {{
                left: 32px;
                animation: loader2 0.6s infinite;
            }}
            
            .loader div:nth-child(4) {{
                left: 56px;
                animation: loader3 0.6s infinite;
            }}
            
            @keyframes loader1 {{
                0% {{ transform: scale(0); }}
                100% {{ transform: scale(1); }}
            }}
            
            @keyframes loader3 {{
                0% {{ transform: scale(1); }}
                100% {{ transform: scale(0); }}
            }}
            
            @keyframes loader2 {{
                0% {{ transform: translate(0, 0); }}
                100% {{ transform: translate(24px, 0); }}
            }}
            
            .progress-container {{
                width: 100%;
                background-color: #e0e0e0;
                border-radius: 5px;
                margin: 20px 0;
                overflow: hidden;
            }}
            
            .progress-bar {{
                height: 10px;
                background-color: #3498db;
                width: 0%;
                border-radius: 5px;
                transition: width 0.5s ease;
                animation: progress 30s linear forwards;
            }}
            
            @keyframes progress {{
                0% {{ width: 0%; }}
                20% {{ width: 20%; }}
                40% {{ width: 40%; }}
                60% {{ width: 60%; }}
                80% {{ width: 80%; }}
                100% {{ width: 95%; }}
            }}
            
            .status {{
                font-size: 18px;
                margin: 20px 0;
                color: #555;
            }}
            
            .steps {{
                text-align: left;
                margin: 30px auto;
                max-width: 400px;
            }}
            
            .step {{
                margin: 15px 0;
                padding: 10px;
                border-radius: 5px;
                background-color: #f8f9fa;
                display: flex;
                align-items: center;
                opacity: 0.5;
                transition: opacity 0.3s, background-color 0.3s;
            }}
            
            .step.active {{
                opacity: 1;
                background-color: #e8f4fd;
                border-left: 4px solid #3498db;
            }}
            
            .step-icon {{
                margin-right: 15px;
                color: #3498db;
                font-size: 20px;
            }}
            
            .step-text {{
                font-size: 16px;
            }}
            
            .completed-icon {{
                display: none;
                color: #2ecc71;
            }}
            
            .step.completed .completed-icon {{
                display: inline;
            }}
            
            .step.completed {{
                background-color: #e8f8f5;
                border-left: 4px solid #2ecc71;
            }}
            
            .timer {{
                font-size: 14px;
                color: #777;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            
            <div class="loader">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
            </div>
            
            <div class="status">{processing}... <span id="status-text">{please_wait}</span></div>
            
            <div class="progress-container">
                <div class="progress-bar" id="progress-bar"></div>
            </div>
            
            <div class="steps">
                <div class="step active" id="step1">
                    <div class="step-icon">⚙️</div>
                    <div class="step-text">{generating}</div>
                    <div class="completed-icon">✓</div>
                </div>
                <div class="step" id="step2">
                    <div class="step-icon">📝</div>
                    <div class="step-text">{formatting}</div>
                    <div class="completed-icon">✓</div>
                </div>
                <div class="step" id="step3">
                    <div class="step-icon">🔧</div>
                    <div class="step-text">{optimizing}</div>
                    <div class="completed-icon">✓</div>
                </div>
                <div class="step" id="step4">
                    <div class="step-icon">📄</div>
                    <div class="step-text">{finalizing}</div>
                    <div class="completed-icon">✓</div>
                </div>
            </div>
            
            <div class="timer" id="timer">00:00</div>
        </div>
        
        <script>
            // Timer functionality
            let seconds = 0;
            const timerElement = document.getElementById('timer');
            
            setInterval(() => {{
                seconds++;
                const minutes = Math.floor(seconds / 60);
                const remainingSeconds = seconds % 60;
                timerElement.textContent = `${{minutes.toString().padStart(2, '0')}}:${{remainingSeconds.toString().padStart(2, '0')}}`;
            }}, 1000);
            
            // Simulate progress through steps
            setTimeout(() => {{
                document.getElementById('step1').classList.add('completed');
                document.getElementById('step2').classList.add('active');
            }}, 5000);
            
            setTimeout(() => {{
                document.getElementById('step2').classList.add('completed');
                document.getElementById('step3').classList.add('active');
            }}, 15000);
            
            setTimeout(() => {{
                document.getElementById('step3').classList.add('completed');
                document.getElementById('step4').classList.add('active');
            }}, 25000);
        </script>
    </body>
    </html>
    """
