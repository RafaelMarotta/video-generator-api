# Usa uma imagem leve do Python
FROM python:3.11-slim

# Define diretório de trabalho no container
WORKDIR /app

# Copia o requirements e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
  && pip install gunicorn

# Copia o restante do código
COPY . .

# Expõe a porta usada pela aplicação
EXPOSE 8000

# Comando de produção: Gunicorn com UvicornWorker
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:8000"]
