# Use the official Python base image
FROM python:3.11-slim

# Install system dependencies (curl might be useful depending on your actual use cases, but keeping it minimal is best practice)

# Set the working directory
WORKDIR /app

# Copy the dependency files first to leverage Docker cache
COPY requirements.txt .

# Install dependencies directly using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Install the application logic
RUN pip install -e .

# Define the entrypoint for the CLI
ENTRYPOINT ["paper-cli"]
CMD ["--help"]
