# ใช้ Python 3.11
FROM python:3.11-slim

# ป้องกัน pyc + log realtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# โฟลเดอร์ทำงานใน container
WORKDIR /app

# ติดตั้ง dependency ที่จำเป็น (ปรับเพิ่มได้)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# คัดลอกไฟล์ requirements ก่อน (เพื่อ cache)
COPY requirements.txt .

# ติดตั้ง python package
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# คัดลอกโค้ดทั้งหมด
COPY . .

# คำสั่ง default (แก้ได้)
CMD ["python", "app/main.py"]
