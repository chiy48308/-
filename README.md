# 英語配音練習系統

這是一個基於Streamlit開發的英語配音練習系統，允許使用者聆聽原始音頻，然後錄製自己的配音進行英語口語練習。

## 功能特點

- 顯示英語台詞文本
- 播放原始音頻
- 錄製使用者配音
- 即時播放錄音結果
- 儲存錄音供日後參考
- 自動管理音頻文件
- 方便的錄音控制界面

## 安裝與運行

1. 克隆此倉庫:
```bash
git clone [倉庫網址]
cd Fixed_Audio_Dubbing_Website
```

2. 安裝依賴:
```bash
pip install -r requirements.txt
```

3. 運行應用:
```bash
streamlit run app.py
```

## 系統要求

- Python 3.7+
- 支持麥克風輸入的設備
- 現代網絡瀏覽器（Chrome、Edge、Firefox等）

## 使用方法

1. 在文本框中輸入學號
2. 選擇配音台詞
3. 聆聽原始音頻
4. 點擊「開始錄音」按鈕
5. 對著麥克風朗讀台詞進行配音
6. 點擊「結束錄音」按鈕
7. 即可在原音頻下方聽取剛才的錄音
8. 如果滿意，可點擊「儲存錄音」按鈕永久保存

## 文件結構

- `app.py`: 主應用程式
- `requirements.txt`: 依賴套件列表
- `datasets/`: 腳本和音頻數據
  - `lesson03/lesson03_script/`: 台詞文本
  - `lesson03/lesson03_speech/`: 原始音頻
  - `lesson03/lesson03_recording/`: 儲存使用者錄音
