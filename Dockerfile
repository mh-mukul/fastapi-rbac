FROM python:3.10-slim

WORKDIR /app

# Copy only requirements.txt first to leverage caching
COPY requirements.txt /app/

# Install dependencies before copying source code to prevent cache busting
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy only necessary application files (avoid copying unnecessary files)
COPY . /app/

# Copy the entrypoint script separately and ensure it has execution permissions
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
