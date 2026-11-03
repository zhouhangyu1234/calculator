# ============================================================
# Lab 7 - backend container: calculator REST API (Java 17)
# Build:  docker build -t calculator-backend:lab7 backend/
# Port:   8000
# ============================================================
# ---------- stage 1: build the jar -------------------------
# The Maven + JDK image is only needed while compiling; it is thrown away at
# the stage boundary, exactly like Lab 6's single-container image.
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build

# Copy the POM first and resolve dependencies on their own layer: the slow
# download is only repeated when pom.xml changes, not when a .java file does.
COPY pom.xml .
RUN mvn -B -q dependency:go-offline

# Compile, run the 36 JUnit 5 tests and package the jar. Tests are NOT skipped:
# a broken commit must never turn into a runnable image.
COPY src ./src
RUN mvn -B -q clean package

# ---------- stage 2: runtime -------------------------------
FROM eclipse-temurin:17-jre-alpine

# Run as an unprivileged user instead of root.
RUN addgroup -S app && adduser -S -G app app

WORKDIR /app

# Only the jar crosses the stage boundary; no Maven, no compiler, no source.
COPY --from=builder /build/target/calculator-1.0.0.jar /app/calculator.jar
RUN chown -R app:app /app

USER app

# Configuration is injected, never hard-coded: compose supplies the same
# values, and the service reads them at start-up.
ENV PORT=8000 \
    LOG_LEVEL=INFO

# Document the API port.
EXPOSE 8000

# Liveness probe consumed by `depends_on: condition: service_healthy`.
# wget comes from BusyBox, so the JRE image needs no extra package.
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD wget -qO- http://127.0.0.1:8000/health > /dev/null || exit 1

# The jar's default main class is the Lab 3 command line calculator (kept for
# Lab 6); the Lab 7 service is started explicitly instead.
ENTRYPOINT ["java", "-cp", "/app/calculator.jar", "calculator.CalcServer"]
