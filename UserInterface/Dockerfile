FROM node:latest
WORKDIR /app
COPY package.json ./
COPY public/ ./public
COPY src/ ./src
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]



# COPY api_folder /app
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
