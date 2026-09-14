# Gunakan image Python slim untuk ukuran yang lebih kecil
FROM python:3.11-slim

# Set timezone ke WIB (Asia/Jakarta)
ENV TZ=Asia/Jakarta

# Set working directory
WORKDIR /app

# Install dependencies terlebih dahulu (memanfaatkan Docker cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code
COPY . .

# Jalankan bot
CMD ["python", "src/main.py"]
