FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
  && pip install gunicorn

# Copia o restante dos arquivos
COPY . .

# Expõe a porta
EXPOSE 8000

# Define variáveis de ambiente básicas
ENV PYTHONPATH=/app/src

# Comando de produção
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:8000"]
