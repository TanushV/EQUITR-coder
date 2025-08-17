# Generated Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps (optional: git for tools)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install package with API extras
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir .[api]

# Expose port
EXPOSE 8000

# Run the API server by default
CMD ["equitrcoder", "api", "--host", "0.0.0.0", "--port", "8000"]
