FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy bridge source
COPY . .

EXPOSE 5000

CMD ["python", "bridge.py"]
