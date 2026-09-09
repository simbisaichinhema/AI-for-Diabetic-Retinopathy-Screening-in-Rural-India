# Stage 1: Build React/Vite application
FROM node:22-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci || npm install

# Copy source files
COPY . .

# Build production distribution
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# Stage 2: Run FastAPI and serve the built SPA on the Space port.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Use the CPU wheel to avoid pulling a multi-gigabyte CUDA runtime into the Space.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu --no-deps torch \
	&& pip install --no-cache-dir filelock jinja2 networkx setuptools sympy \
	&& grep -v '^torch' requirements.txt > /tmp/requirements-no-torch.txt \
	&& pip install --no-cache-dir -r /tmp/requirements-no-torch.txt

COPY backend ./backend
COPY configs ./configs
COPY explainability ./explainability
COPY inference ./inference
COPY preprocessing ./preprocessing
COPY data ./data
COPY --from=build /app/dist ./dist

ENV PYTHONUNBUFFERED=1
ENV KERAS_BACKEND=torch

EXPOSE 7860

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
