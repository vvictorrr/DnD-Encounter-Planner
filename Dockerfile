# Combined image: one process, one port, nothing for a friend to install.
# The frontend is built once here and served directly by Flask - see
# backend/app/__init__.py::_register_frontend.

FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# Lands at /app/frontend/dist, matching Config.FRONTEND_DIST_DIR's default
# of "../frontend/dist" relative to backend/ - no env var needed.
COPY --from=frontend-build /frontend/dist /app/frontend/dist

ENV FLASK_APP=run.py
EXPOSE 8080
# --preload: create_app() (and its db.create_all()) runs once in the master
# process before forking workers, instead of once per worker - without it,
# multiple workers can race to CREATE TABLE against the same SQLite file on
# a fresh boot and one of them crashes with "table already exists."
CMD ["gunicorn", "--preload", "--bind", "0.0.0.0:8080", "--workers", "2", "run:app"]
