# ============================================================
# Lab 7 - web container: static calculator UI served by nginx
# Build:  docker build -t calculator-web:lab7 web/
# Port:   80 (published as 8080 by docker-compose.yml)
# ============================================================
FROM nginx:1.27-alpine

# Provenance labels (visible with `docker inspect`).
LABEL org.opencontainers.image.title="calculator-web" \
      org.opencontainers.image.description="Lab 7 static frontend + reverse proxy for the calculator" \
      org.opencontainers.image.source="https://github.com/zhouhangyu1234/calculator"

# 1. Reverse-proxy template. The nginx image renders /etc/nginx/templates/*.template
#    with envsubst at start-up, so ${BACKEND_HOST} is replaced by the value that
#    docker-compose injects - the Compose service name "backend".
COPY default.conf.template /etc/nginx/templates/default.conf.template

# 2. Static assets of the calculator UI. No build step is needed: plain HTML,
#    CSS and JavaScript can be served as they are, which keeps the image ~50 MB
#    (vs hundreds of MB for a Node-based build).
COPY index.html /usr/share/nginx/html/index.html
COPY style.css  /usr/share/nginx/html/style.css
COPY app.js     /usr/share/nginx/html/app.js

# 3. Defaults for a standalone `docker run`; compose overrides them.
ENV BACKEND_HOST=backend \
    BACKEND_PORT=8000

# 4. Document the port the container listens on.
EXPOSE 80

# 5. Container-level liveness check. wget is part of BusyBox in Alpine, so no
#    extra package (and no curl) has to be installed.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

# nginx:alpine already has a correct default CMD ("nginx -g 'daemon off;'"),
# so no CMD/ENTRYPOINT override is required here.
