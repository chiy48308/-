// 錄音相關功能
document.addEventListener('DOMContentLoaded', function() {
    const startRecordButton = document.getElementById('startRecordButton');
    const stopRecordButton = document.getElementById('stopRecordButton');
    const recordedAudio = document.getElementById('recordedAudio');
    const saveRecordingButton = document.getElementById('saveRecordingButton');
    const saveRecordingDiv = document.getElementById('saveRecordingDiv');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const recordingStatus = document.getElementById('recordingStatus');
    const timer = document.getElementById('timer');
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadedAudio = document.getElementById('uploadedAudio');
    const deleteRecordingButton = document.getElementById('deleteRecordingButton');
    
    let mediaRecorder;
    let audioChunks = [];
    let audioBlob;
    let timerInterval;
    let seconds = 0;
    
    // 錄音功能
    if (startRecordButton && stopRecordButton) {
        startRecordButton.addEventListener('click', async function() {
            try {
                // 獲取麥克風權限
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });
                
                // 使用MediaRecorder錄製音頻
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = function() {
                    // 停止計時器
                    clearInterval(timerInterval);
                    
                    // 創建音頻Blob
                    audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // 顯示錄音
                    recordedAudio.src = audioUrl;
                    recordedAudio.style.display = 'block';
                    
                    // 顯示保存按鈕
                    saveRecordingDiv.style.display = 'block';
                    
                    // 隱藏錄音指示
                    recordingIndicator.style.display = 'none';
                    timer.style.display = 'none';
                    
                    // 恢復按鈕狀態
                    startRecordButton.disabled = false;
                    stopRecordButton.disabled = true;
                    
                    recordingStatus.innerHTML = '<div class="alert alert-success">錄音完成！</div>';
                };
                
                // 開始錄音
                mediaRecorder.start(200); // 每200毫秒收集一次數據
                
                // 更新UI
                startRecordButton.disabled = true;
                stopRecordButton.disabled = false;
                recordingIndicator.style.display = 'block';
                recordingStatus.innerHTML = '';
                recordedAudio.style.display = 'none';
                saveRecordingDiv.style.display = 'none';
                
                // 啟動計時器
                seconds = 0;
                timer.textContent = '00:00';
                timer.style.display = 'block';
                
                timerInterval = setInterval(function() {
                    seconds++;
                    const minutes = Math.floor(seconds / 60);
                    const remainingSeconds = seconds % 60;
                    timer.textContent = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
                }, 1000);
                
            } catch (err) {
                console.error('錄音失敗:', err);
                recordingStatus.innerHTML = `<div class="alert alert-danger">錄音失敗: ${err.message}</div>`;
            }
        });
        
        stopRecordButton.addEventListener('click', function() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                
                // 停止所有音軌
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        });
        
        // 保存錄音
        if (saveRecordingButton) {
            saveRecordingButton.addEventListener('click', function() {
                if (!audioBlob) {
                    recordingStatus.innerHTML = '<div class="alert alert-danger">沒有可保存的錄音</div>';
                    return;
                }
                
                // 創建FormData對象
                const formData = new FormData();
                formData.append('audio_data', audioBlob, 'recording.webm');
                
                // 發送到服務器
                fetch('/save_recorded_audio', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        recordingStatus.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                        // 刷新頁面顯示保存的錄音
                        setTimeout(() => window.location.reload(), 1500);
                    } else {
                        recordingStatus.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    }
                })
                .catch(error => {
                    recordingStatus.innerHTML = `<div class="alert alert-danger">保存失敗: ${error.message}</div>`;
                });
            });
        }
    }
    
    // 文件上傳功能
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const fileInput = document.getElementById('audioFile');
            
            if (fileInput.files.length === 0) {
                uploadStatus.innerHTML = '<div class="alert alert-danger">請選擇要上傳的音頻文件</div>';
                return;
            }
            
            // 顯示上傳的文件
            const file = fileInput.files[0];
            const audioUrl = URL.createObjectURL(file);
            uploadedAudio.src = audioUrl;
            uploadedAudio.style.display = 'block';
            
            // 發送到服務器
            fetch('/upload_recording', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    // 刷新頁面顯示上傳的錄音
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    uploadStatus.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                }
            })
            .catch(error => {
                uploadStatus.innerHTML = `<div class="alert alert-danger">上傳失敗: ${error.message}</div>`;
            });
        });
    }
    
    // 刪除錄音
    if (deleteRecordingButton) {
        deleteRecordingButton.addEventListener('click', function() {
            if (confirm('確定要刪除此錄音嗎？')) {
                fetch('/delete_recording', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        // 刷新頁面
                        window.location.reload();
                    } else {
                        alert(data.error);
                    }
                })
                .catch(error => {
                    alert('刪除失敗: ' + error.message);
                });
            }
        });
    }
}); 