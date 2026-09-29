# ==========================================
# Stage 1: Build React/Vite application
# ==========================================

FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files first
# This improves Docker layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY . .

# Backend API URL
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Build React application
RUN npm run build


# ==========================================
# Stage 2: Serve with Nginx
# ==========================================

FROM nginx:alpine

# Remove default Nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy React production build
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]