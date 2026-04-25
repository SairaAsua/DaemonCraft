FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

ENV MC_HOST=localhost
ENV MC_PORT=25565
ENV MC_USERNAME=DaemonBot
ENV MC_AUTH=offline
ENV API_PORT=3000
ENV API_HOST=0.0.0.0
ENV AUTO_RECONNECT=true

CMD ["node", "server.js"]
