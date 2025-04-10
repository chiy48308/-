import streamlit as st
import numpy as np
import os
from pathlib import Path
import soundfile as sf
import time
import platform
from io import BytesIO
import base64

# 設置頁面配置
st.set_page_config(
    page_title="配音練習系統",
    page_icon="🎙️",
    layout="wide"
)

# 設置標題
st.title("英語配音練習系統")

# 檢測運行環境
is_cloud = os.environ.get('STREAMLIT_CLOUD', False)

# 添加JavaScript代碼來檢測麥克風
st.markdown("""
<script>
async function checkMicrophone() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        return true;
    } catch (err) {
        return false;
    }
}

// 檢測麥克風並更新頁面狀態
checkMicrophone().then(hasPermission => {
    if (hasPermission) {
        window.parent.postMessage({type: 'mic-status', status: 'available'}, '*');
    } else {
        window.parent.postMessage({type: 'mic-status', status: 'unavailable'}, '*');
    }
});
</script>
""", unsafe_allow_html=True)

# 初始化 session state
if 'student_id' not in st.session_state:
    st.session_state.student_id = ""
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'temp_recording' not in st.session_state:
    st.session_state.temp_recording = None
if 'recorded_audio' not in st.session_state:
    st.session_state.recorded_audio = None
if 'recording' not in st.session_state:
    st.session_state.recording = False

# 設置正確的路徑
LESSON_PATH = "datasets/lesson03"
SCRIPT_PATH = os.path.join(LESSON_PATH, "lesson03_script")
SPEECH_PATH = os.path.join(LESSON_PATH, "lesson03_speech")
RECORDING_PATH = os.path.join(LESSON_PATH, "lesson03_recording")

# 確保錄音目錄存在
os.makedirs(RECORDING_PATH, exist_ok=True)

# 麥克風設置提示
st.sidebar.title("🎙️ 麥克風設置")
st.sidebar.info("""
### 麥克風使用說明
1. 請確保您的瀏覽器支持音頻錄製
2. 點擊瀏覽器地址欄的鎖定圖標
3. 授予麥克風訪問權限
4. 如果看不到錄音按鈕，請刷新頁面
""")

st.sidebar.markdown("---")
st.sidebar.write("💡 如果錄音不工作，請嘗試:")
st.sidebar.write("1. 使用Chrome或Firefox瀏覽器")
st.sidebar.write("2. 確認瀏覽器有麥克風權限")
st.sidebar.write("3. 檢查系統麥克風設置")
st.sidebar.write("4. 重新載入頁面")

# 學號輸入
student_id = st.text_input("請輸入學號：", value=st.session_state.student_id)
if student_id != st.session_state.student_id:
    st.session_state.student_id = student_id
    st.rerun()

if not st.session_state.student_id:
    st.warning("請先輸入學號才能開始配音練習")
    st.stop()

# 獲取所有腳本文件
script_files = sorted([f for f in os.listdir(SCRIPT_PATH) if f.endswith('.txt')])

# 顯示進度
st.write(f"進度：{st.session_state.current_index + 1}/{len(script_files)}")

# 顯示當前腳本
if script_files:
    current_script = script_files[st.session_state.current_index]
    script_path = os.path.join(SCRIPT_PATH, current_script)
    
    # 讀取並顯示腳本內容
    with open(script_path, 'r', encoding='utf-8') as file:
        script_content = file.read()
    st.text_area("當前台詞：", script_content, height=100)

    # 對應的音頻文件
    audio_filename = current_script.replace('.txt', '.mp3')
    audio_path = os.path.join(SPEECH_PATH, audio_filename)
    
    # 顯示原音頻
    st.subheader("原音頻")
    if os.path.exists(audio_path):
        st.audio(audio_path, format='audio/mp3')
    else:
        st.error(f"找不到音頻文件：{audio_path}")
    
    st.markdown("---")
    
    # 錄音部分
    st.subheader("您的錄音")
    
    # 添加錄音組件的HTML
    st.markdown("""
    <div class="audio-controls">
        <button id="startRecord" class="record-button">開始錄音</button>
        <button id="stopRecord" class="record-button" disabled>停止錄音</button>
        <audio id="recordedAudio" controls style="display:none;"></audio>
    </div>
    
    <script>
    // 初始化錄音功能
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    // 等待DOM加載完成
    window.addEventListener('load', function() {
        // 獲取按鈕元素
        const startButton = document.querySelector('#startRecord');
        const stopButton = document.querySelector('#stopRecord');
        const audioPlayer = document.querySelector('#recordedAudio');

        // 為開始錄音按鈕添加事件監聽器
        startButton.addEventListener('click', async function() {
            if (isRecording) return;
            
            try {
                console.log('請求麥克風權限...');
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                console.log('麥克風權限已獲得');
                
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = () => {
                    console.log('錄音已停止，處理數據...');
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audioPlayer.src = audioUrl;
                    audioPlayer.style.display = 'block';
                };
                
                mediaRecorder.start();
                isRecording = true;
                startButton.disabled = true;
                stopButton.disabled = false;
                console.log('開始錄音');
                
            } catch (err) {
                console.error('錄音失敗:', err);
                alert('無法訪問麥克風，請確保已授予權限並使用支持的瀏覽器（Chrome/Firefox）');
            }
        });

        // 為停止錄音按鈕添加事件監聽器
        stopButton.addEventListener('click', function() {
            if (!isRecording) return;
            
            try {
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                    isRecording = false;
                    startButton.disabled = false;
                    stopButton.disabled = true;
                    console.log('錄音已停止');
                }
            } catch (err) {
                console.error('停止錄音失敗:', err);
                alert('停止錄音時發生錯誤，請刷新頁面重試');
            }
        });
    });
    </script>
    
    <style>
    .audio-controls {
        margin: 20px 0;
        padding: 15px;
        background-color: #f0f2f6;
        border-radius: 8px;
        text-align: center;
    }
    .record-button {
        margin: 0 10px;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        background-color: #ff4b4b;
        color: white;
        cursor: pointer;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .record-button:hover {
        background-color: #ff3333;
        transform: scale(1.05);
    }
    .record-button:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
        transform: none;
    }
    #recordedAudio {
        width: 100%;
        margin-top: 15px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 導航按鈕
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_index > 0:
            if st.button("上一句"):
                st.session_state.current_index -= 1
                st.session_state.temp_recording = None
                st.session_state.recorded_audio = None
                st.rerun()
    
    with col2:
        st.write(f"當前第 {st.session_state.current_index + 1} 句，共 {len(script_files)} 句")
    
    with col3:
        if st.session_state.current_index < len(script_files) - 1:
            if st.button("下一句"):
                st.session_state.current_index += 1
                st.session_state.temp_recording = None
                st.session_state.recorded_audio = None
                st.rerun()

# 添加頁面樣式
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .st-emotion-cache-16idsys {
        padding: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
