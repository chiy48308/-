import streamlit as st
import numpy as np
import os
from pathlib import Path
import soundfile as sf
import time
import platform
from io import BytesIO
import base64
from streamlit import components

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
    
    # 使用最簡單的方式測試按鈕點擊是否正常
    st.markdown("""
    <div class="audio-controls">
        <button id="basicTest" class="record-button" onclick="alert('按鈕點擊成功！')">測試按鈕</button>
        <div style="margin-top: 15px;">
            <span>如果上面的按鈕無法點擊，請嘗試使用下面的文件上傳方式：</span>
        </div>
    </div>
    
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
    </style>
    """, unsafe_allow_html=True)
    
    # 使用Streamlit內置的文件上傳功能作為備用方案
    st.write("### 請通過以下方式上傳您的錄音")
    uploaded_file = st.file_uploader("選擇音頻文件或使用麥克風錄制", type=['mp3', 'wav', 'ogg', 'm4a', 'webm'], accept_multiple_files=False)
    
    # 或者使用camera_input (會在移動設備上自動使用麥克風)
    if uploaded_file is None:
        st.write("### 或者直接錄音（僅支持移動設備）")
        audio_bytes = st.audio_recorder(pause_threshold=3.0)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            # 保存錄音
            if st.button("保存此錄音"):
                # 保存到文件
                recording_filename = f"{st.session_state.student_id}_{st.session_state.current_index+1}.wav"
                recording_path = os.path.join(RECORDING_PATH, recording_filename)
                with open(recording_path, "wb") as f:
                    f.write(audio_bytes)
                st.success(f"錄音已保存：{recording_filename}")
    
    # 處理上傳的音頻文件
    if uploaded_file is not None:
        # 保存上傳的音頻
        recording_filename = f"{st.session_state.student_id}_{st.session_state.current_index+1}.{uploaded_file.name.split('.')[-1]}"
        recording_path = os.path.join(RECORDING_PATH, recording_filename)
        
        with open(recording_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"錄音已上傳：{recording_filename}")
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")

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
