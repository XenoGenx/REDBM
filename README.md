# THE RED FRONTIER

เว็บบันทึกงานกีฬาสีคณะสีแดง ใช้ Django, SQLite, Bootstrap 5 และ Pillow

## เริ่มใช้งานบน Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

เปิดเว็บที่ `http://127.0.0.1:8000/`

## ตั้งรหัสประธานและวันงาน

แก้ค่า `PRESIDENT_PASSWORD` และ `EVENT_DATE` ในไฟล์ `.env` โดยวันงานใช้รูปแบบ `YYYY-MM-DD` จากนั้นรีสตาร์ตเซิร์ฟเวอร์ วันงานจะแสดงเป็นปี พ.ศ. ในหน้าเว็บ

อย่าเผยแพร่ไฟล์ `.env` และเปลี่ยน `SECRET_KEY` ก่อนนำเว็บขึ้นใช้งานจริง

## เตรียม deploy บน Linux/VPS

1. คัดลอก `.env.example` เป็น `.env` แล้วตั้ง `DEBUG=False`, `SECRET_KEY` แบบสุ่ม, `PRESIDENT_PASSWORD`, `ALLOWED_HOSTS` และ `CSRF_TRUSTED_ORIGINS` ให้ตรงกับโดเมนจริง
2. ตั้ง `DATABASE_PATH` และ `MEDIA_ROOT` ให้อยู่บน persistent disk ของเครื่อง/แพลตฟอร์ม เพื่อไม่ให้ฐานข้อมูลและรูปหายเมื่อ deploy ใหม่
3. ติดตั้งและเตรียมฐานข้อมูลกับ static files:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

4. ตั้งคำสั่ง start ของบริการเป็น:

```bash
waitress-serve --listen=0.0.0.0:${PORT:-8000} redfrontier.wsgi:application
```

ให้ reverse proxy (เช่น Nginx) จัดการ HTTPS และเสิร์ฟไฟล์ใน `MEDIA_ROOT` ที่ URL `/media/`; WhiteNoise จัดการไฟล์ static ให้แล้ว ห้ามใช้ `runserver` ใน production

เว็บนี้ใช้ SQLite และ media บน filesystem จึงต้องเลือกบริการที่มี persistent disk หรือย้ายฐานข้อมูล/รูปไปบริการถาวรก่อนใช้บนแพลตฟอร์มที่ลบไฟล์ทุกครั้งที่ deploy# RedBm
# REDBM
