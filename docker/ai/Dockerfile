FROM python:3.10-slim 
WORKDIR /app 
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && apt-get clean && rm -rf /var/lib/apt/lists/* 
COPY requirements.txt . 
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt 
RUN mkdir -p /app/src 
COPY ./src/ /app/src/ 
COPY ./api.py /app/ 
ENV PYTHONPATH=/app 
ENV PYTHONUNBUFFERED=1 
EXPOSE 8000 
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 

