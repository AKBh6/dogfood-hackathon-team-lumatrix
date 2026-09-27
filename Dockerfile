# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npx prisma generate
RUN npm run build
EXPOSE 3000
# Ensure the DB path points to the writable directory
ENV DATABASE_URL="file:/app/data/hackathon.db"

ENTRYPOINT ["./entrypoint.sh"]
