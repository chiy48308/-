# 英語配音練習系統

這是一個基於Flask的英語配音練習系統，旨在幫助用戶通過練習配音來提升英語口語能力。

## 功能特點

- 提供英語台詞文本和原音頻
- 支持用戶錄製自己的配音
- 支持上傳已錄製的音頻文件
- 多個配音練習句子切換
- 用戶進度保存
- 音頻回放和比較
- 響應式設計，適配各種設備

## 技術棧

- **後端**: Flask (Python Web框架)
- **前端**: HTML, CSS, JavaScript, Bootstrap 5
- **用戶界面**: Bootstrap 5 組件和樣式
- **音頻處理**: Web Audio API, MediaRecorder API
- **會話管理**: Flask Session
- **部署**: Heroku

## 安裝和運行

1. 克隆此倉庫
```
git clone https://github.com/your-username/english-dubbing-practice.git
cd english-dubbing-practice
```

2. 安裝依賴
```
pip install -r requirements.txt
```

3. 運行應用
```
python run.py
```

4. 訪問應用
打開瀏覽器，訪問 http://localhost:5000

## 部署到Heroku

1. 創建Heroku應用
```
heroku create your-app-name
```

2. 推送代碼到Heroku
```
git push heroku main
```

3. 打開應用
```
heroku open
```

## 使用說明

1. 輸入學號並確認
2. 系統將顯示台詞和原音頻
3. 選擇"錄製音頻"或"上傳音頻"選項
4. 完成錄音或上傳後，可以回放比較
5. 使用導航按鈕切換不同的台詞和音頻
6. 所有錄音將自動保存，並與學號關聯

## 文件結構

```
/
├── flask_app/
│   ├── static/                 # 靜態資源
│   │   ├── css/                # 樣式表
│   │   ├── js/                 # JavaScript文件
│   │   └── uploads/            # 上傳文件存儲
│   │       └── recordings/     # 用戶錄音存儲
│   ├── templates/              # HTML模板
│   │   └── index.html          # 主頁模板
│   └── app.py                  # Flask應用程序
├── datasets/                   # 課程數據集
│   └── lesson03/              # 課程03資料
│       ├── lesson03_script/    # 台詞文本
│       ├── lesson03_speech/    # 原音頻
│       └── lesson03_recording/ # 用戶錄音(在運行時創建)
├── run.py                      # 應用入口點
├── requirements.txt            # 依賴列表
├── Procfile                    # Heroku部署配置
└── README.md                   # 項目說明
```

## 授權

本項目採用MIT許可證授權。
