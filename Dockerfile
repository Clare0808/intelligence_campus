FROM node:22-bookworm-slim AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src ./src
COPY frontend/public ./public
RUN npm run build

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CAMPUS_DATA_DIR=/data \
    CAMPUS_START_CONSTRUCTION_FEED=1 \
    CAMPUS_DISABLE_LEGACY_REFRESH=1

WORKDIR /app
COPY backend/requirements.txt backend/requirements-campus.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/app.py ./backend/
COPY backend/api ./backend/api
COPY backend/data ./backend/data
COPY frontend/public/data/buildings.geojson ./frontend/public/data/buildings.geojson
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

RUN mkdir -p /data && addgroup --system campus && adduser --system --ingroup campus campus \
    && chown campus:campus /data
COPY docker/start.sh /app/start.sh

WORKDIR /app/backend
EXPOSE 10000
CMD ["sh", "/app/start.sh"]