FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --user-group --create-home --shell /usr/sbin/nologin lab

COPY --chown=lab:lab ftp_lab.py ./ftp_lab.py
COPY --chown=lab:lab data/ ./data/

USER lab

EXPOSE 2121/tcp 8080/tcp 6000-6009/tcp

CMD ["python3", "ftp_lab.py", "--host", "0.0.0.0", "--port", "2121", "--http-port", "8080"]
