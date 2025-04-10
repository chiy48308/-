import streamlit as st
import numpy as np
import os
from pathlib import Path
import sounddevice as sd
import soundfile as sf
import time

# 設置頁面配置
st.set_page_config(
    page_title="配音練習系統",
    page_icon="🎙️",
    layout="wide"
)

# 設置標題
st.title("英語配音練習系統")

# 添加麥克風檢測功能
def get_available_devices():
    try:
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append((i, device['name']))
        return input_devices
    except Exception as e:
        return []

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
if 'selected_device' not in st.session_state:
    st.session_state.selected_device = None
if 'device_tested' not in st.session_state:
    st.session_state.device_tested = False

# 設置正確的路徑
LESSON_PATH = "datasets/lesson03"
SCRIPT_PATH = os.path.join(LESSON_PATH, "lesson03_script")
SPEECH_PATH = os.path.join(LESSON_PATH, "lesson03_speech")
RECORDING_PATH = os.path.join(LESSON_PATH, "lesson03_recording")

# 確保錄音目錄存在
os.makedirs(RECORDING_PATH, exist_ok=True)

# 音頻設備檢測和選擇
st.sidebar.title("🎙️ 麥克風設置")

# 獲取可用的輸入設備
available_devices = get_available_devices()
if available_devices:
    # 創建設備名稱到設備ID的映射
    device_options = {name: device_id for device_id, name in available_devices}
    # 設備選擇下拉框
    selected_device_name = st.sidebar.selectbox(
        "選擇麥克風設備", 
        list(device_options.keys()),
        index=0 if st.session_state.selected_device is None else list(device_options.keys()).index(next((name for device_id, name in available_devices if device_id == st.session_state.selected_device), list(device_options.keys())[0]))
    )
    # 更新選擇的設備ID
    selected_device_id = device_options[selected_device_name]
    
    # 如果選擇的設備發生變化
    if st.session_state.selected_device != selected_device_id:
        st.session_state.selected_device = selected_device_id
        st.session_state.device_tested = False
        st.rerun()
    
    # 測試麥克風按鈕
    if st.sidebar.button("測試麥克風", type="primary"):
        try:
            st.sidebar.write("🔊 正在錄製 3 秒測試音頻...")
            # 設置錄音參數
            duration = 3  # 測試錄音時長（秒）
            fs = 44100  # 採樣率
            channels = 1  # 單聲道
            
            # 開始錄音，使用選定的設備
            status_text = st.sidebar.empty()
            status_text.text("錄製中...")
            audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype=np.float32, device=st.session_state.selected_device)
            sd.wait()  # 等待錄音完成
            status_text.text("錄製完成")
            
            # 顯示測試結果
            max_amplitude = np.max(np.abs(audio_data))
            st.sidebar.write(f"最大音量: {max_amplitude:.4f}")
            
            if max_amplitude < 0.01:
                st.sidebar.error("⚠️ 未檢測到有效的音頻輸入，請檢查麥克風是否正常工作。")
            else:
                st.sidebar.success("✅ 麥克風測試成功！已檢測到音頻輸入。")
                st.session_state.device_tested = True
            
            # 創建臨時測試文件用於播放
            test_path = os.path.join(RECORDING_PATH, "device_test.wav")
            sf.write(test_path, audio_data, fs)
            
            # 播放測試錄音
            if os.path.exists(test_path) and os.path.getsize(test_path) > 0:
                st.sidebar.audio(test_path, format='audio/wav')
            
        except Exception as e:
            st.sidebar.error(f"麥克風測試失敗: {str(e)}")
    
    # 顯示麥克風狀態
    if st.session_state.device_tested:
        st.sidebar.success(f"當前使用的麥克風: {selected_device_name}")
    else:
        st.sidebar.warning("請測試您的麥克風以確保其正常工作")
else:
    st.sidebar.error("⚠️ 未檢測到任何麥克風設備。請確保您的麥克風已連接，然後重新啟動應用程序。")

st.sidebar.markdown("---")
st.sidebar.write("💡 如果錄音不工作，請嘗試:")
st.sidebar.write("1. 檢查麥克風連接")
st.sidebar.write("2. 確認瀏覽器有麥克風權限")
st.sidebar.write("3. 選擇不同的輸入設備")
st.sidebar.write("4. 在系統設置中測試麥克風")

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
    
    # 改為垂直佈局，先顯示原音頻，再顯示用戶錄音
    st.subheader("原音頻")
    # 顯示原音頻
    if os.path.exists(audio_path):
        st.audio(audio_path, format='audio/mp3')
    else:
        st.error(f"找不到音頻文件：{audio_path}")
    
    st.markdown("---")
    
    st.subheader("您的錄音")
    
    # 錄音控制按鈕
    col_rec1, col_rec2, col_rec3 = st.columns(3)
    
    # 開始錄音按鈕
    with col_rec1:
        record_button = st.button("開始錄音", type="primary")
        
        # 檢查是否有選擇麥克風
        if record_button:
            if not available_devices:
                st.error("未檢測到麥克風設備，無法錄音。請連接麥克風後重新啟動應用。")
            elif st.session_state.selected_device is None:
                st.error("請先在側邊欄選擇並測試麥克風設備。")
            else:
                try:
                    # 設置錄音參數
                    fs = 44100  # 採樣率
                    channels = 1  # 單聲道
                    
                    # 顯示錄音狀態
                    st.warning("⚠️ 正在錄音中... 請點擊「結束錄音」按鈕停止錄音")
                    st.info(f"使用麥克風: {next((name for device_id, name in available_devices if device_id == st.session_state.selected_device), '未知設備')}")
                    
                    # 儲存設備信息到session_state
                    st.session_state.fs = fs
                    st.session_state.channels = channels
                    st.session_state.device_id = st.session_state.selected_device
                    
                    # 創建一個緩衝區來存儲錄音數據
                    max_duration = 60  # 最大錄音時長（秒）
                    buffer_size = int(max_duration * fs * channels)  # 計算緩衝區大小
                    
                    # 開始錄音, 但不等待完成，只是開始記錄
                    st.session_state.recording_queue = sd.rec(buffer_size, samplerate=fs, channels=channels, dtype=np.float32, device=st.session_state.selected_device, blocking=False)
                    
                    # 記錄開始時間
                    st.session_state.recording_start_time = time.time()
                    
                    # 設置錄音狀態為真
                    st.session_state.recording = True
                    
                    # 顯示錄音按鈕的狀態
                    st.rerun()
                except Exception as e:
                    st.error(f"錄音失敗：{str(e)}")
    
    # 結束錄音按鈕
    with col_rec2:
        if st.button("結束錄音", type="primary"):
            if st.session_state.recording:
                try:
                    # 停止錄音並保存結果
                    st.write("正在停止錄音並保存...")
                    
                    # 檢查是否有錄音數據
                    if 'recording_queue' in st.session_state:
                        # 計算實際錄音時長
                        elapsed_time = time.time() - st.session_state.recording_start_time
                        fs = st.session_state.fs
                        channels = st.session_state.channels
                        
                        # 計算實際需要的幀數
                        actual_frames = int(elapsed_time * fs)
                        
                        # 獲取錄音數據（只取實際錄製的部分）
                        # 確保不超出數組邊界
                        if actual_frames > 0:
                            recorded_data = st.session_state.recording_queue[:actual_frames]
                            
                            # 確保目錄存在
                            os.makedirs(RECORDING_PATH, exist_ok=True)
                            
                            # 保存為臨時文件
                            temp_path = os.path.join(RECORDING_PATH, "temp_recording.wav")
                            sf.write(temp_path, recorded_data, fs)
                            
                            # 檢查文件是否成功創建
                            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                                # 設置臨時錄音路徑
                                st.session_state.temp_recording = temp_path
                                st.success(f"錄音已完成！長度: {elapsed_time:.1f}秒")
                            else:
                                st.error("錄音文件創建失敗或為空。請檢查麥克風設置。")
                        else:
                            st.error("錄音時間太短，無法保存。")
                    else:
                        st.error("沒有找到錄音數據。")
                except Exception as e:
                    st.error(f"停止錄音失敗: {str(e)}")
                finally:
                    # 無論如何都將錄音狀態設為False
                    st.session_state.recording = False
                    st.rerun()
            else:
                st.warning("沒有正在進行的錄音")
    
    # 儲存錄音按鈕
    with col_rec3:
        if st.button("儲存錄音", type="primary"):
            if st.session_state.temp_recording and os.path.exists(st.session_state.temp_recording):
                try:
                    # 確保臨時文件存在並不為空
                    if os.path.getsize(st.session_state.temp_recording) > 0:
                        # 讀取臨時文件
                        audio_data, sr = sf.read(st.session_state.temp_recording)
                        
                        # 確保錄音目錄存在
                        os.makedirs(RECORDING_PATH, exist_ok=True)
                        
                        # 生成新的文件名，包含時間戳以防止覆蓋
                        timestamp = int(time.time())
                        base_filename = current_script.replace('.txt', '_recording.wav')
                        recording_filename = f"{timestamp}_{st.session_state.student_id}_{base_filename}"
                        recording_path = os.path.join(RECORDING_PATH, recording_filename)
                        
                        # 保存為永久文件
                        sf.write(recording_path, audio_data, sr)
                        
                        # 驗證文件是否成功創建
                        if os.path.exists(recording_path) and os.path.getsize(recording_path) > 0:
                            st.session_state.recorded_audio = recording_path
                            st.success(f"錄音已成功儲存！文件名：{recording_filename}")
                            st.rerun()
                        else:
                            st.error(f"錄音文件創建失敗或為空文件。")
                    else:
                        st.error("臨時錄音文件為空，無法儲存。請重新錄音。")
                except Exception as e:
                    st.error(f"儲存錄音失敗：{str(e)}")
            else:
                st.warning("請先錄音才能儲存！")

    # 顯示錄音狀態
    if st.session_state.recording:
        st.warning("正在錄音中...")

    # 分隔線
    st.markdown("---")

    # 顯示剛剛錄製的聲音（直接在原音頻下方）
    if st.session_state.temp_recording and os.path.exists(st.session_state.temp_recording):
        try:
            # 檢查文件大小
            file_size = os.path.getsize(st.session_state.temp_recording)
            if file_size > 0:
                st.subheader("📝 剛錄製的聲音")
                # 讀取音頻數據
                audio_data, sr = sf.read(st.session_state.temp_recording)
                # 顯示基本信息
                st.write(f"錄音長度: {len(audio_data)/sr:.1f} 秒")
                # 播放音頻
                st.audio(st.session_state.temp_recording, format='audio/wav')
                
                # 檢查音頻內容是否有效
                if len(audio_data) > 0:
                    max_amplitude = np.max(np.abs(audio_data))
                    if max_amplitude < 0.01:
                        st.warning("⚠️ 警告：檢測到音量非常低，可能麥克風沒有收到聲音")
            else:
                st.error("錄音文件存在但為空 (0 字節)。請檢查麥克風權限。")
        except Exception as e:
            st.error(f"播放錄音時發生錯誤：{str(e)}")
    else:
        if not st.session_state.recording:  # 如果不是正在錄音中
            st.info("尚未有新錄音。點擊「開始錄音」按鈕進行錄音。")
    
    # 分隔線
    st.markdown("---")
    
    # 顯示更多錄音選項
    with st.expander("更多錄音選項"):
        col_play1, col_play2 = st.columns(2)
        
        # 顯示錄音詳細信息
        with col_play1:
            st.write("📊 當前錄音詳細信息")
            if st.session_state.temp_recording and os.path.exists(st.session_state.temp_recording):
                try:
                    # 檢查文件大小
                    file_size = os.path.getsize(st.session_state.temp_recording)
                    if file_size > 0:
                        # 讀取音頻數據
                        audio_data, sr = sf.read(st.session_state.temp_recording)
                        # 顯示詳細信息
                        st.write(f"文件路徑: {st.session_state.temp_recording}")
                        st.write(f"文件大小: {file_size} 字節")
                        st.write(f"採樣率: {sr} Hz")
                        
                        # 顯示音量信息
                        max_amplitude = np.max(np.abs(audio_data))
                        st.write(f"最大音量: {max_amplitude:.4f}")
                except Exception as e:
                    st.error(f"讀取錄音信息失敗：{str(e)}")
        
        # 顯示已儲存的錄音
        with col_play2:
            st.write("💾 已儲存的錄音")
            if st.session_state.recorded_audio and os.path.exists(st.session_state.recorded_audio):
                try:
                    audio_data, sr = sf.read(st.session_state.recorded_audio)
                    st.audio(st.session_state.recorded_audio, format='audio/wav')
                    st.write(f"文件名: {os.path.basename(st.session_state.recorded_audio)}")
                    st.write(f"錄音長度: {len(audio_data)/sr:.1f} 秒")
                except Exception as e:
                    st.error(f"播放已儲存錄音失敗：{str(e)}")
            else:
                st.info("尚未儲存任何錄音。錄音後點擊「儲存錄音」按鈕可永久保存。")
        
        # 顯示錄音歷史
        st.write("---")
        st.write("📂 錄音歷史")
        recording_files = [f for f in os.listdir(RECORDING_PATH) if f.endswith('.wav') and f != "temp_recording.wav"]
        if recording_files:
            recording_files.sort(reverse=True)  # 最新的排在前面
            selected_file = st.selectbox("選擇歷史錄音文件播放", recording_files)
            selected_path = os.path.join(RECORDING_PATH, selected_file)
            if os.path.exists(selected_path) and os.path.getsize(selected_path) > 0:
                st.audio(selected_path, format='audio/wav')
                try:
                    audio_data, sr = sf.read(selected_path)
                    st.write(f"錄音長度：{len(audio_data)/sr:.1f} 秒")
                except Exception as e:
                    st.error(f"讀取文件信息失敗：{str(e)}")
        else:
            st.info("錄音歷史中沒有保存的錄音文件")

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
