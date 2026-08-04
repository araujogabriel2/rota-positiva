# Usar a imagem oficial do Python slim (leve e segura para produção)
FROM python:3.11-slim

# Evitar que o Python gere arquivos .pyc e garantir logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências de sistema recomendadas (como curl para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas as dependências primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .

# Instalar as dependências do projeto e adicionar o Gunicorn (servidor de produção)
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copiar o restante dos arquivos do projeto para o container
COPY . .

# Expor a porta em que a aplicação Flask está configurada para rodar
EXPOSE 5000

# Executar a aplicação usando Gunicorn em ambiente de produção
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
