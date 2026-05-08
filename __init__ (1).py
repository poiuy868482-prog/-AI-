# 個人網站部署教學

這個版本可以部署成你的個人網站。

## 方式 A：Render 部署，最簡單

1. 建立 GitHub 帳號。
2. 新增一個 Repository，例如 `sgmdtx-battle-sim`。
3. 把整個專案上傳到 GitHub。
4. 到 Render 建立 New Web Service。
5. 選你的 GitHub Repository。
6. 設定：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. 部署完成後，Render 會給你一個網址。

## 方式 B：Railway

1. 建立 Railway 專案。
2. 連接 GitHub Repository。
3. Railway 會偵測 Python 專案。
4. Start Command 使用：
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 方式 C：Docker / VPS

```bash
docker build -t sgmdtx-battle-sim .
docker run -p 8000:8000 -e PORT=8000 sgmdtx-battle-sim
```

然後打開：

```text
http://你的伺服器IP:8000
```

## 本機測試

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打開：

```text
http://127.0.0.1:8000
```

## 手機使用

只要網站部署到雲端，手機直接開網址即可。  
手機不負責模擬運算，運算由伺服器做。

## 效能建議

免費主機建議：

- 普通勝率模擬：1000～3000 次
- AI 配隊：100～500 次/隊
- 不建議公開給大量玩家同時使用

## 改網站名稱

編輯：

```text
app/site_config.py
```

可以修改：

```python
SITE_TITLE = "你的網站名稱"
SITE_DESCRIPTION = "你的網站說明"
```
