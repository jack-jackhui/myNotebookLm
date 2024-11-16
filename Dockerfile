# Use an official Python runtime as a parent image
FROM python:3.12
LABEL authors="jackhui"

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /mynotebooklm

# Install system dependencies, including ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /mynotebooklm
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /mynotebooklm/
RUN chown -R www-data:www-data /mynotebooklm

# Expose the port the app runs on
EXPOSE 8501

# Run streamlit
CMD ["streamlit", "run", "webui.py", "--server.port=8501"]


