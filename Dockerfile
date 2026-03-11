FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . .

# Create a folder for the SQLite database so we can mount a volume to it
RUN mkdir -p /app/data

# Tell SQLAlchemy where to find the DB via an environment variable
# Your code should use: os.getenv("DATABASE_URL", "sqlite:///./data/ecommerce.db")
ENV DATABASE_URL=sqlite:///./data/ecommerce.db

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]