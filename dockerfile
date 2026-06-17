FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r backend/requirements.txt

EXPOSE 7860

CMD uvicorn backend.app.main:app --host 0.0.0.0 --port 7860
