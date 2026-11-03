FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY booking_bot ./booking_bot
COPY bot.py .
ENV DB_PATH=/data/bookings.db
VOLUME /data
CMD ["python", "bot.py"]
