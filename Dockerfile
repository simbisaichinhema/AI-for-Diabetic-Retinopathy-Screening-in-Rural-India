# Stage 1: Build React/Vite Application
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

# Stage 2: Serve with Nginx on Port 7860 (Hugging Face Spaces Requirement)
FROM nginx:alpine

# Remove default nginx configs
RUN rm -rf /etc/nginx/conf.d/*

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts to nginx root
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 7860
EXPOSE 7860

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
