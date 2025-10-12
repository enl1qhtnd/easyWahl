FROM node:alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose the port that Vite uses
EXPOSE 5173

# Start the development server
CMD ["npm", "run", "dev"]