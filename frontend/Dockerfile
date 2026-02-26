# ---- Base image ----
FROM node:20-alpine AS base
WORKDIR /app

# ---- Install dependencies ----
FROM base AS deps
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# ---- Build ----
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- Production image ----
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy only necessary files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]

# sudo docker build -t dfm-app-frontend .
# sudo docker run -p 3000:3000 dfm-app-frontend 
# sudo docker tag dfm-app-frontend anwaarnoaman/dfm-app-frontend:1.0.0
# sudo docker push anwaarnoaman/dfm-app-frontend:1.0.0
 