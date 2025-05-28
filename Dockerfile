# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your code to the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
