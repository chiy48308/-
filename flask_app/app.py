from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
import os
import secrets
import time
from werkzeug.utils import secure_filename
import json

# 確保所有必要目錄存在
for directory in ["datasets/lesson03", 
                "datasets/lesson03/lesson03_script", 
                "datasets/lesson03/lesson03_speech", 
                "datasets/lesson03/lesson03_recording"]:
    os.makedirs(directory, exist_ok=True)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 用於session的密鑰

# 設置路徑
LESSON_PATH = "datasets/lesson03"
SCRIPT_PATH = os.path.join(LESSON_PATH, "lesson03_script")
SPEECH_PATH = os.path.join(LESSON_PATH, "lesson03_speech")
RECORDING_PATH = os.path.join(LESSON_PATH, "lesson03_recording")

# 允許上傳的音頻格式
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS

def get_script_files():
    """獲取所有腳本文件"""
    return sorted([f for f in os.listdir(SCRIPT_PATH) if f.endswith('.txt')])

def get_script_content(index):
    """獲取指定索引的腳本內容"""
    script_files = get_script_files()
    if 0 <= index < len(script_files):
        script_path = os.path.join(SCRIPT_PATH, script_files[index])
        with open(script_path, 'r', encoding='utf-8') as file:
            return file.read()
    return ""

def get_audio_path(index):
    """獲取指定索引的音頻路徑"""
    script_files = get_script_files()
    if 0 <= index < len(script_files):
        audio_filename = script_files[index].replace('.txt', '.mp3')
        return os.path.join(SPEECH_PATH, audio_filename)
    return ""

def get_existing_recording(student_id, index):
    """檢查是否已有保存的錄音"""
    for ext in ['wav', 'mp3', 'ogg', 'm4a', 'webm']:
        potential_file = os.path.join(RECORDING_PATH, f"{student_id}_{index+1}.{ext}")
        if os.path.exists(potential_file):
            return potential_file
    return None

@app.route('/')
def index():
    """主頁"""
    # 獲取學號和當前索引
    student_id = session.get('student_id', '')
    current_index = session.get('current_index', 0)
    
    script_files = get_script_files()
    total_scripts = len(script_files)
    
    if current_index >= total_scripts:
        current_index = 0
        session['current_index'] = current_index
    
    # 獲取腳本內容
    script_content = get_script_content(current_index)
    
    # 獲取原音頻路徑
    audio_path = get_audio_path(current_index)
    audio_filename = os.path.basename(audio_path) if audio_path else ""
    
    # 檢查是否已有錄音
    existing_recording = None
    if student_id:
        existing_recording = get_existing_recording(student_id, current_index)
        if existing_recording:
            existing_recording = os.path.basename(existing_recording)
    
    return render_template('index.html', 
                          student_id=student_id,
                          current_index=current_index,
                          total_scripts=total_scripts,
                          script_content=script_content,
                          audio_filename=audio_filename,
                          existing_recording=existing_recording)

@app.route('/set_student_id', methods=['POST'])
def set_student_id():
    """設置學號"""
    student_id = request.form.get('student_id', '')
    if student_id:
        session['student_id'] = student_id
    return redirect(url_for('index'))

@app.route('/navigate', methods=['POST'])
def navigate():
    """導航到上一句或下一句"""
    direction = request.form.get('direction', '')
    current_index = session.get('current_index', 0)
    script_files = get_script_files()
    
    if direction == 'prev' and current_index > 0:
        session['current_index'] = current_index - 1
    elif direction == 'next' and current_index < len(script_files) - 1:
        session['current_index'] = current_index + 1
    
    return redirect(url_for('index'))

@app.route('/upload_recording', methods=['POST'])
def upload_recording():
    """上傳錄音"""
    student_id = session.get('student_id', '')
    current_index = session.get('current_index', 0)
    
    if not student_id:
        return jsonify({'error': '請先輸入學號'}), 400
    
    if 'audio_file' not in request.files:
        return jsonify({'error': '沒有檔案'}), 400
    
    file = request.files['audio_file']
    
    if file.filename == '':
        return jsonify({'error': '沒有選擇檔案'}), 400
    
    if file and allowed_file(file.filename):
        # 保存上傳的音頻
        file_extension = file.filename.split('.')[-1].lower()
        recording_filename = f"{student_id}_{current_index+1}.{file_extension}"
        recording_path = os.path.join(RECORDING_PATH, recording_filename)
        
        file.save(recording_path)
        
        return jsonify({
            'success': True,
            'message': f'錄音已保存為：{recording_filename}',
            'filename': recording_filename
        })
    
    return jsonify({'error': '不支持的檔案格式'}), 400

@app.route('/save_recorded_audio', methods=['POST'])
def save_recorded_audio():
    """保存通過JavaScript錄製的音頻"""
    student_id = session.get('student_id', '')
    current_index = session.get('current_index', 0)
    
    if not student_id:
        return jsonify({'error': '請先輸入學號'}), 400
    
    if 'audio_data' not in request.files:
        return jsonify({'error': '沒有音頻數據'}), 400
    
    audio_data = request.files['audio_data']
    
    if audio_data:
        # 保存錄製的音頻
        recording_filename = f"{student_id}_{current_index+1}.webm"
        recording_path = os.path.join(RECORDING_PATH, recording_filename)
        
        audio_data.save(recording_path)
        
        return jsonify({
            'success': True,
            'message': f'錄音已保存為：{recording_filename}',
            'filename': recording_filename
        })
    
    return jsonify({'error': '保存錄音失敗'}), 400

@app.route('/delete_recording', methods=['POST'])
def delete_recording():
    """刪除錄音"""
    student_id = session.get('student_id', '')
    current_index = session.get('current_index', 0)
    
    if not student_id:
        return jsonify({'error': '請先輸入學號'}), 400
    
    existing_recording = get_existing_recording(student_id, current_index)
    
    if existing_recording and os.path.exists(existing_recording):
        os.remove(existing_recording)
        return jsonify({
            'success': True,
            'message': '錄音已刪除'
        })
    
    return jsonify({'error': '找不到要刪除的錄音'}), 404

@app.route('/audio/<path:filename>')
def get_audio(filename):
    """獲取音頻文件"""
    return send_from_directory(SPEECH_PATH, filename)

@app.route('/recording/<path:filename>')
def get_recording(filename):
    """獲取錄音文件"""
    return send_from_directory(RECORDING_PATH, filename)

if __name__ == '__main__':
    app.run(debug=True) 