FROM node:24-alpine AS build

WORKDIR /workspace/apps/web

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web ./

ARG VITE_TRUST_LEDGER_API_BASE_URL
ENV VITE_TRUST_LEDGER_API_BASE_URL=${VITE_TRUST_LEDGER_API_BASE_URL}

RUN npm run build

FROM nginx:1.27-alpine

COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html

EXPOSE 80
