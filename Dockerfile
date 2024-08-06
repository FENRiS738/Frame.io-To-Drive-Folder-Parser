FROM python:3.12-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV FRAME_TOKEN=fio-u-VoXH2kofS0nGMuBt0FN8j_LZQZA_UicPvFK8WpYs257fcQCzL-55gkFJMJfOkVL2
ENV WEBHOOK_URL=https://hook.us1.make.com/bdybh58lqnvv08tz5a7h0dl7qq7a71qz

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--timeout-keep-alive", "120"]