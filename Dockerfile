
FROM python:3.11-slim AS builder

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --user -r requirements.txt


COPY . .


FROM python:3.11-slim

WORKDIR /app


COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app


ENV PATH=/root/.local/bin:$PATH


ENV FLASK_ENV=production


EXPOSE 5000

CMD ["python", "app.py"]