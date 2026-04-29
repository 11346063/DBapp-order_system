# DBapp order_system

安裝套件
```
pip install -r requirements.txt
```

建資料庫
```
python manage.py makemigrations
python manage.py migrate
```

匯入資料庫
```
python manage.py shell -c "exec(open('import_menu.py', encoding='utf-8').read())"
```
<br>

產生報表測試資料
```
python manage.py seed_report_data
```

此指令會建立近 30 天與近 12 個月的測試訂單，讓管理後台報表圖表有資料。預設會先刪除前一次由此指令建立的資料再重建，避免重複執行後資料膨脹。

# DATABASE 設定

database 設定: 複製sample.env 到同目錄，名稱改為 .env，填入 database 設定
