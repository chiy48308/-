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
    
    # 添加錄音組件的HTML
    # 使用st.markdown代替components.html以確保在Streamlit Cloud中正常工作
    st.markdown("""
    <div class="audio-controls">
        <button id="startRecord" class="record-button">開始錄音</button>
        <button id="stopRecord" class="record-button" disabled>停止錄音</button>
        <audio id="recordedAudio" controls style="display:none;"></audio>
        <div id="debug-info" style="margin-top: 10px; color: #666; font-family: monospace;"></div>
    </div>
    
    <script>
    // 立即執行函數，避免變量污染全局空間
    (function() {
        console.log('[初始化] 腳本開始加載...');
        
        // 調試信息顯示函數
        function showDebugInfo(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const debugDiv = document.getElementById('debug-info');
            const color = type === 'error' ? '#ff4444' : 
                         type === 'success' ? '#44ff44' : '#666666';
            
            console.log(`[${timestamp}] ${message}`);
            
            if (debugDiv) {
                const newMessage = document.createElement('div');
                newMessage.style.color = color;
                newMessage.textContent = `[${timestamp}] ${message}`;
                debugDiv.appendChild(newMessage);
                
                // 保持最新的5條消息
                while (debugDiv.children.length > 5) {
                    debugDiv.removeChild(debugDiv.firstChild);
                }
            }
        }

        // 檢查是否在Streamlit環境中運行
        function isInStreamlit() {
            try {
                return window.parent !== window;
            } catch(e) {
                showDebugInfo('檢查Streamlit環境出錯: ' + e.message, 'error');
                return true; // 假設在Streamlit中，以安全角度考慮
            }
        }

        // 檢查瀏覽器支持
        function checkBrowserSupport() {
            showDebugInfo('檢查瀏覽器API支持...');
            let allSupportMessages = [];
            
            if (!navigator.mediaDevices) {
                allSupportMessages.push('瀏覽器不支持 mediaDevices API');
                showDebugInfo('瀏覽器不支持 mediaDevices API', 'error');
                return { supported: false, messages: allSupportMessages };
            }
            
            if (!navigator.mediaDevices.getUserMedia) {
                allSupportMessages.push('瀏覽器不支持 getUserMedia');
                showDebugInfo('瀏覽器不支持 getUserMedia', 'error');
                return { supported: false, messages: allSupportMessages };
            }
            
            if (typeof MediaRecorder === 'undefined') {
                allSupportMessages.push('瀏覽器不支持 MediaRecorder');
                showDebugInfo('瀏覽器不支持 MediaRecorder', 'error');
                return { supported: false, messages: allSupportMessages };
            }
            
            // 檢查安全上下文
            if (!window.isSecureContext) {
                allSupportMessages.push('不在安全上下文中運行，某些API可能受限');
                showDebugInfo('警告：不在安全上下文中運行 (非HTTPS/localhost)', 'error');
                // 仍然返回支持，但提出警告
            }
            
            // 檢查是否在iframe中
            if (isInStreamlit()) {
                allSupportMessages.push('在Streamlit環境(iframe)中運行，某些權限可能受限');
                showDebugInfo('在Streamlit環境中運行（iframe）', 'info');
                // 仍然返回支持，但提出警告
            }
            
            // 檢查瀏覽器類型和版本
            const userAgent = navigator.userAgent;
            let browserInfo = 'Unknown browser';
            
            if (userAgent.indexOf('Chrome') > -1) {
                browserInfo = 'Chrome ' + userAgent.match(/Chrome\\/(\\d+)/)[1];
            } else if (userAgent.indexOf('Firefox') > -1) {
                browserInfo = 'Firefox ' + userAgent.match(/Firefox\\/(\\d+)/)[1];
            } else if (userAgent.indexOf('Safari') > -1) {
                browserInfo = 'Safari ' + userAgent.match(/Version\\/(\\d+)/)[1];
            } else if (userAgent.indexOf('Edge') > -1 || userAgent.indexOf('Edg') > -1) {
                browserInfo = 'Edge ' + (userAgent.match(/Edge\\/(\\d+)/) || userAgent.match(/Edg\\/(\\d+)/))[1];
            }
            
            showDebugInfo(`檢測到瀏覽器: ${browserInfo}`, 'info');
            allSupportMessages.push(`使用瀏覽器: ${browserInfo}`);
            
            showDebugInfo('瀏覽器支持所需的所有API', 'success');
            return { supported: true, messages: allSupportMessages };
        }

        // 主函數
        function initializeRecording() {
            showDebugInfo('初始化錄音功能...');
            
            const support = checkBrowserSupport();
            if (!support.supported) {
                const errorMsg = '您的瀏覽器不支持錄音功能: ' + support.messages.join(', ');
                showDebugInfo(errorMsg, 'error');
                alert(errorMsg + '\\n請使用最新版本的Chrome或Firefox瀏覽器。');
                return;
            }

            const startButton = document.querySelector('#startRecord');
            const stopButton = document.querySelector('#stopRecord');
            const audioPlayer = document.querySelector('#recordedAudio');

            if (!startButton || !stopButton || !audioPlayer) {
                showDebugInfo('無法找到必要的DOM元素', 'error');
                return;
            }

            showDebugInfo('成功找到所有必要的DOM元素', 'success');

            let mediaRecorder = null;
            let audioChunks = [];
            let isRecording = false;
            let recordingStream = null;

            // 確保在iframe中也能獲得焦點（對於Streamlit環境）
            window.addEventListener('click', function() {
                if (startButton && !startButton.classList.contains('clicked-once')) {
                    startButton.classList.add('clicked-once');
                    showDebugInfo('頁面已獲得焦點交互', 'info');
                }
            });

            // 開始錄音按鈕事件
            startButton.addEventListener('click', async function() {
                showDebugInfo('開始錄音按鈕被點擊');
                
                if (isRecording) {
                    showDebugInfo('已經在錄音中，忽略點擊', 'info');
                    return;
                }

                // 在點擊時立即顯示視覺反饋
                startButton.style.backgroundColor = '#888';
                startButton.textContent = '正在獲取麥克風...';

                try {
                    showDebugInfo('請求麥克風權限...');
                    
                    // 強制在用戶手勢（點擊）中請求權限
                    const stream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }
                    });
                    
                    recordingStream = stream;  // 保存流的引用
                    showDebugInfo('成功獲得麥克風權限', 'success');
                    
                    // 使用基本的MIME類型，提高兼容性
                    let options = {};
                    try {
                        options = { mimeType: 'audio/webm' };
                        mediaRecorder = new MediaRecorder(stream, options);
                        showDebugInfo('使用 audio/webm 格式錄音', 'success');
                    } catch (e) {
                        // 嘗試備選格式
                        try {
                            options = { mimeType: 'audio/ogg; codecs=opus' };
                            mediaRecorder = new MediaRecorder(stream, options);
                            showDebugInfo('備選: 使用 audio/ogg 格式錄音', 'success');
                        } catch (e2) {
                            // 嘗試最基本格式
                            mediaRecorder = new MediaRecorder(stream);
                            showDebugInfo('備選: 使用默認格式錄音', 'info');
                        }
                    }
                    
                    showDebugInfo('MediaRecorder 實例創建成功', 'success');
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (event) => {
                        showDebugInfo(`接收到音頻數據: ${event.data.size} bytes`);
                        if (event.data.size > 0) {
                            audioChunks.push(event.data);
                        }
                    };

                    mediaRecorder.onstart = () => {
                        showDebugInfo('錄音開始', 'success');
                        isRecording = true;
                        startButton.disabled = true;
                        stopButton.disabled = false;
                        startButton.style.backgroundColor = '#cccccc';
                        startButton.textContent = '正在錄音...';
                        stopButton.style.backgroundColor = '#ff4b4b';
                    };

                    mediaRecorder.onstop = () => {
                        showDebugInfo('錄音結束，處理音頻數據...');
                        isRecording = false;
                        
                        if (audioChunks.length === 0) {
                            showDebugInfo('警告：沒有收集到音頻數據', 'error');
                            alert('錄音過程中沒有收集到音頻數據，請檢查麥克風是否正常工作。');
                            return;
                        }
                        
                        try {
                            const audioBlob = new Blob(audioChunks, { type: options.mimeType || 'audio/webm' });
                            showDebugInfo(`創建音頻Blob: ${audioBlob.size} bytes`);
                            
                            if (audioBlob.size > 0) {
                                const audioUrl = URL.createObjectURL(audioBlob);
                                audioPlayer.src = audioUrl;
                                audioPlayer.style.display = 'block';
                                showDebugInfo('音頻處理完成，可以播放', 'success');
                                
                                // 嘗試主動播放
                                audioPlayer.oncanplay = () => {
                                    showDebugInfo('音頻已準備好播放');
                                };
                            } else {
                                showDebugInfo('創建的音頻Blob大小為0', 'error');
                            }
                        } catch (blobError) {
                            showDebugInfo(`創建音頻Blob失敗: ${blobError.message}`, 'error');
                        }
                    };

                    mediaRecorder.onerror = (event) => {
                        showDebugInfo(`錄音錯誤: ${event.error}`, 'error');
                    };

                    // 確保每200ms收集一次數據，避免潛在問題
                    mediaRecorder.start(200);
                    showDebugInfo('已調用 mediaRecorder.start(200)');
                    
                } catch (err) {
                    showDebugInfo(`錄音失敗: ${err.message}`, 'error');
                    console.error('錄音詳細錯誤:', err);
                    
                    // 還原按鈕狀態
                    startButton.disabled = false;
                    startButton.style.backgroundColor = '#ff4b4b';
                    startButton.textContent = '開始錄音';
                    
                    // 更詳細的錯誤指導
                    let errorMessage = '無法訪問麥克風，請確保:';
                    errorMessage += '\\n1. 麥克風設備已連接並工作正常';
                    errorMessage += '\\n2. 您已授予麥克風使用權限';
                    errorMessage += '\\n3. 沒有其他應用程序正在使用麥克風';
                    
                    if (isInStreamlit()) {
                        errorMessage += '\\n\\n在Streamlit環境中:';
                        errorMessage += '\\n- 確保您使用的是Chrome或Firefox瀏覽器';
                        errorMessage += '\\n- 查看地址欄是否有麥克風權限提示';
                        errorMessage += '\\n- 嘗試在新標籤頁中打開應用';
                    }
                    
                    alert(errorMessage);
                }
            });

            // 停止錄音按鈕事件
            stopButton.addEventListener('click', function() {
                showDebugInfo('停止錄音按鈕被點擊');
                
                if (!isRecording) {
                    showDebugInfo('沒有正在進行的錄音，忽略點擊');
                    return;
                }
                
                try {
                    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                        showDebugInfo('正在停止 MediaRecorder...');
                        
                        // 停止MediaRecorder
                        mediaRecorder.stop();
                        
                        // 停止所有音軌
                        if (recordingStream) {
                            recordingStream.getTracks().forEach(track => {
                                track.stop();
                                showDebugInfo(`音軌 ${track.kind} 已停止`);
                            });
                        }
                        
                        // 更新UI
                        isRecording = false;
                        startButton.disabled = false;
                        stopButton.disabled = true;
                        startButton.style.backgroundColor = '#ff4b4b';
                        startButton.textContent = '開始錄音';
                        stopButton.style.backgroundColor = '#cccccc';
                        
                        showDebugInfo('錄音已完全停止', 'success');
                    }
                } catch (err) {
                    showDebugInfo(`停止錄音失敗: ${err.message}`, 'error');
                    console.error('停止錄音詳細錯誤:', err);
                    
                    // 強制重置狀態，以免界面卡住
                    isRecording = false;
                    startButton.disabled = false;
                    stopButton.disabled = true;
                    startButton.style.backgroundColor = '#ff4b4b';
                    startButton.textContent = '開始錄音';
                    stopButton.style.backgroundColor = '#cccccc';
                    
                    alert('停止錄音時發生錯誤，請刷新頁面重試');
                }
            });

            showDebugInfo('所有事件監聽器已設置完成', 'success');
        }

        // 等待DOM加載完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeRecording);
            showDebugInfo('等待DOM加載完成...');
        } else {
            initializeRecording();
        }
        
        showDebugInfo('腳本初始化完成', 'success');
    })();
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
    .record-button:focus {
        outline: 2px solid #1e88e5;
    }
    .clicked-once {
        box-shadow: 0 0 5px rgba(0,0,0,0.2);
    }
    #recordedAudio {
        width: 100%;
        margin-top: 15px;
        border-radius: 4px;
    }
    #debug-info {
        margin-top: 10px;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        text-align: left;
        max-height: 150px;
        overflow-y: auto;
    }
    #debug-info div {
        margin: 2px 0;
        padding: 2px 5px;
        border-radius: 2px;
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
