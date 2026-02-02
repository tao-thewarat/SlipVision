
# SlipVision – Backend (Python + FastAPI + RapidOCR)

SlipVision คือ backend สำหรับระบบ OCR ใบเสร็จ / slip สินค้า
ใช้ **RapidOCR** แปลงภาพเป็นข้อความ และให้ **FastAPI** เป็น API สำหรับ frontend

## โครงสร้างโปรเจกต์ (Project Structure)

```
SlipVision/
├── app/                     # โค้ดหลักของ backend
│   ├── main.py              # จุดเริ่มต้นของ FastAPI
│   │
│   ├── api/                 # รวมไฟล์ API (router)
│   │   └── ocr.py           # API สำหรับ OCR slip
│   │
│   ├── services/            # business logic / service layer
│   │   └── ocr_service.py   # เรียกใช้ RapidOCR
│   │
│   ├── models/              # model / schema (เตรียมไว้ใช้กับ DB)
│   │   └── slip.py
│   │
│   └── core/                # config หรือ setting ต่าง ๆ
│       └── config.py
│
├── .venv/                   # virtual environment (สร้างโดย uv)
├── pyproject.toml           # รายชื่อ dependency และ config
├── .python-version          # เวอร์ชัน Python ที่ใช้
├── .env                     # environment variables
└── README.md                # ไฟล์อธิบายโปรเจกต์
```

### อธิบายแบบสั้น ๆ

| โฟลเดอร์         | หน้าที่                  |
| ---------------- | ------------------------ |
| `main.py`        | สร้าง FastAPI app        |
| `api/`           | รับ request จาก frontend |
| `services/`      | ประมวลผล OCR / logic     |
| `models/`        | โครงสร้างข้อมูล          |
| `.venv`          | Python environment       |
| `pyproject.toml` | จัดการ library           |

---

## สิ่งที่ต้องติดตั้งก่อน

### 1. Python

แนะนำ **Python 3.11**

ตรวจสอบ:

```bash
python --version
```

---

### 2. ติดตั้ง `uv`

`uv` คือเครื่องมือจัดการ dependency ที่เร็วกว่า pip

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell)

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

ตรวจสอบ:

```bash
uv --version
```

---

## วิธีรันโปรเจกต์

### เข้าโฟลเดอร์โปรเจกต์

```bash
cd SlipVision
```

---

### สร้าง virtual environment

```bash
uv venv
```

activate environment

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```powershell
.venv\Scripts\activate
```

---

### ติดตั้ง dependencies

```bash
uv sync
```

> คำสั่งนี้จะติดตั้ง library ทั้งหมดจาก `pyproject.toml`

---

### รัน FastAPI server

```bash
uv run uvicorn app.main:app --reload
```

ถ้าเห็นข้อความประมาณนี้ แปลว่ารันสำเร็จ

```
Uvicorn running on http://127.0.0.1:8000
```

---

### เปิดเว็บทดสอบ API

* หน้า API docs (แนะนำมาก):
  [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

* health check:
  [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## ทดลอง OCR Slip

ไปที่:

```
POST /api/ocr/slip
```

ขั้นตอน:

1. กด **Try it out**
2. อัปโหลดไฟล์รูป slip (`.jpg`, `.png`)
3. กด **Execute**
4. ดูผลลัพธ์ OCR ที่เป็น JSON

---

## คำสั่ง uv ที่ใช้บ่อย

```bash
uv add fastapi          # เพิ่ม library
uv remove fastapi       # ลบ library
uv sync                 # sync environment
uv run <command>        # รันคำสั่ง
```

---

## ปัญหาที่พบบ่อย

### OCR ช้า

* เป็นเรื่องปกติสำหรับครั้งแรก (โหลด model)
* แนะนำรันบนเครื่องที่มี RAM ≥ 8GB

### เปิด server แล้วเข้าไม่ได้

* ตรวจสอบว่า port 8000 ไม่ถูกใช้อยู่
* ลองเปลี่ยน port:

```bash
uv run uvicorn app.main:app --port 8080
```
