FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
# For sandbox demo (small sample):
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
# For full ranking: docker run <image> python rank.py --candidates /data/candidates.jsonl --out /out/submission.csv
