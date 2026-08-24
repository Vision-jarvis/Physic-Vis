# Manim Community (Latest)
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  pkg-config \
  ffmpeg \
  libcairo2-dev \
  libpango1.0-dev \
  texlive \
  texlive-latex-extra \
  texlive-fonts-extra \
  texlive-latex-recommended \
  texlive-science \
  texlive-fonts-recommended \
  cm-super \
  dvipng \
  && rm -rf /var/lib/apt/lists/*

# Force UTF-8 environment
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

# Install Manim (Latest) and Agent Dependencies
RUN pip install --no-cache-dir \
  manim \
  ipython \
  langchain \
  langchain-google-genai \
  langchain-pinecone \
  pinecone-client \
  google-generativeai \
  python-dotenv \
  langgraph \
  opencv-python-headless

# Set working directory
WORKDIR /app

# Default Manim config
ENV MANIM_QUALITY=medium_quality
ENV MANIM_FRAME_RATE=30

CMD ["python", "-u"]
