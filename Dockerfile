# Use official Docker-in-Docker image
FROM docker:24.0.2-cli

# Install Docker Compose
RUN apk add --no-cache docker-compose bash curl

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Make run.sh executable
RUN chmod +x run.sh

# Run your bash script on container start
CMD ["bash", "run.sh"]
