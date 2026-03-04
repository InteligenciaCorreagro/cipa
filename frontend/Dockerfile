FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json /app/
RUN npm install

COPY . /app
ARG VITE_API_URL
ARG VITE_USE_SUBPATH
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_USE_SUBPATH=${VITE_USE_SUBPATH}
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm i -g serve
COPY --from=build /app/dist /app/dist
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "serve -s dist -l $PORT"]
