import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import whisper
import openai

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

whisper_model = whisper.load_model("small")
openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio(audio_path):
    result = whisper_model.transcribe(audio_path)
    return result['text']

def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following transcript."},
            {"role": "user", "content": text}
        ],
        max_tokens=200,
        temperature=0.5
    )
    return response['choices'][0]['message']['content']

@app.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('index.html', user=session['user'])

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/set_session', methods=['POST'])
def set_session():
    # Called from JS after Supabase login
    user = request.json.get('user')
    if user:
        session['user'] = user
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('user'):
        return redirect(url_for('login'))
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded.'}), 400
    audio_file = request.files['audio']
    audio_path = f"temp_{audio_file.filename}"
    audio_file.save(audio_path)
    transcript = transcribe_audio(audio_path)
    summary = summarize_text(transcript)
    os.remove(audio_path)
    return render_template('result.html', transcript=transcript, summary=summary, user=session['user'])

if __name__ == '__main__':
    app.run(debug=True)
