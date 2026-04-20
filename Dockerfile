FROM python:3.13-slim

WORKDIR /app

RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "task_api:app", "--host", "0.0.0.0", "--port", "8000"]
