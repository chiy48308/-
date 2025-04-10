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
st.sidebar.title("🎧 錄音指南")
st.sidebar.info("""
### 使用外部錄音應用
1. 使用手機或電腦的錄音應用
2. 保存錄音為支持的格式（mp3, wav, ogg等）
3. 上傳錄音文件到系統
""")

st.sidebar.markdown("---")
st.sidebar.write("💡 建議的錄音應用:")
st.sidebar.write("1. Voice Recorder（Windows 10/11內置）")
st.sidebar.write("2. 語音備忘錄（iPhone內置）")
st.sidebar.write("3. 錄音機（Android內置）")
st.sidebar.write("4. Audacity（免費桌面軟件）")

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
    
    # 顯示錄音說明
    st.info("""
    ### 錄音步驟：
    1. 使用您設備上的錄音應用錄製音頻
    2. 保存音頻文件（mp3, wav, ogg等格式）
    3. 點擊下方"選擇文件"上傳您的錄音
    """)
    
    # 文件上傳功能
    uploaded_file = st.file_uploader("上傳您的錄音文件", type=['mp3', 'wav', 'ogg', 'm4a', 'webm'])
    
    if uploaded_file is not None:
        # 獲取文件類型
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # 顯示文件信息
        file_details = {
            "檔案名稱": uploaded_file.name,
            "檔案大小": f"{uploaded_file.size / 1024:.1f} KB",
            "檔案類型": file_extension.upper()
        }
        st.write("**檔案信息：**")
        st.json(file_details)
        
        # 顯示上傳的音頻
        st.write("**預覽錄音：**")
        st.audio(uploaded_file, format=f"audio/{file_extension}")
        
        # 保存上傳的音頻
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("保存此錄音"):
                recording_filename = f"{st.session_state.student_id}_{st.session_state.current_index+1}.{file_extension}"
                recording_path = os.path.join(RECORDING_PATH, recording_filename)
                
                with open(recording_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"錄音已保存為：{recording_filename}")
        
        with col2:
            st.write("👆 點擊保存按鈕將錄音保存到系統")

    # 檢查是否已有保存的錄音
    existing_recording = None
    for ext in ['wav', 'mp3', 'ogg', 'm4a', 'webm']:
        potential_file = os.path.join(RECORDING_PATH, f"{st.session_state.student_id}_{st.session_state.current_index+1}.{ext}")
        if os.path.exists(potential_file):
            existing_recording = potential_file
            break
    
    # 顯示已保存的錄音（如果有）
    if existing_recording:
        st.markdown("---")
        st.subheader("您已保存的錄音")
        
        # 顯示文件信息
        file_size = os.path.getsize(existing_recording) / 1024  # KB
        file_ext = os.path.splitext(existing_recording)[1][1:].upper()
        
        st.write(f"**檔案名稱:** {os.path.basename(existing_recording)}")
        st.write(f"**檔案類型:** {file_ext}")
        st.write(f"**檔案大小:** {file_size:.1f} KB")
        
        # 顯示音頻
        st.audio(existing_recording)
        
        # 添加刪除選項
        if st.button("刪除此錄音"):
            os.remove(existing_recording)
            st.success("錄音已刪除")
            st.rerun()

    # 導航按鈕
    st.markdown("---")
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
