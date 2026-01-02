# Telos Backend - Dockerfile for Cloud Run

# Use official Node.js LTS image
FROM node:18-slim

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production

# Copy application code
COPY src/ ./src/

# Expose port (Cloud Run will inject PORT env var)
EXPOSE 8080

# Set NODE_ENV to production
ENV NODE_ENV=production

# Run as non-root user for security
USER node

# Start the server
CMD ["node", "src/server.js"]

