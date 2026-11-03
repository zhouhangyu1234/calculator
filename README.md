# Calculator (Lab 3 - Lab 7)

[![CI Calculator](https://github.com/zhouhangyu1234/calculator/actions/workflows/ci-calculator.yml/badge.svg)](https://github.com/zhouhangyu1234/calculator/actions/workflows/ci-calculator.yml)

Command line calculator built with Maven, covered by a JUnit 5 test suite,
verified by a GitHub Actions CI pipeline, containerised in Lab 6 and split into
a **two-container application** in Lab 7:

```
browser ──> http://127.0.0.1:8080 ──> web container (nginx :80)
                                        │  static HTML/CSS/JS
                                        │  /api/*  ──proxy_pass──> http://backend:8000
                                        ▼
                                   backend container (Java 17 :8000)
                                        └─ calculator core (Lab 3/4) + 36 JUnit tests
```

The frontend JavaScript never calls `localhost`: inside a container network
`localhost` is the container itself. It calls the relative URL `/api/calc` and
the nginx config forwards it to the Compose **service name** `backend`.

## Build and test the backend

After the Lab 7 restructuring the Maven project lives in `backend/`:

```bash
cd backend
mvn clean compile     # compile all Java sources
mvn test              # run all JUnit 5 test cases (36 tests)
```

## Continuous Integration

Every push to `main` and every pull request targeting `main` triggers the
workflow defined in `.github/workflows/ci-calculator.yml`:

| Job | What it does |
| --- | --- |
| `build` | JDK 17 + 21 matrix: `mvn clean compile`, `mvn test` in `backend/` |
| `compose` | `docker compose build` → `docker compose up -d --wait` → `docker compose ps` → HTTP smoke tests through ports 8080/8000 → `docker compose logs` → browser screenshots from inside the runner → `docker compose down -v` |

The `compose` job fails when the compose file, either Dockerfile, the nginx
proxy or the API misbehaves, so a broken stack can never reach `main`.

## Docker Compose (Lab 7)

```bash
docker compose build          # build both images from their own Dockerfiles
docker compose up -d --wait   # start backend + web, wait until healthy
docker compose ps             # show both containers and their ports
docker compose logs -f        # follow the logs of both services
curl "http://127.0.0.1:8080/api/calc?a=12&op=*&b=7"   # 84, via nginx -> backend
docker compose down -v        # stop and remove everything
```

`LOG_LEVEL=DEBUG docker compose up` overrides the log level injected into the
backend container (`environment:` in docker-compose.yml).

## Project layout

```
backend/                                   # calculation API service
  pom.xml                                  # Maven build (Lab 3/4, JaCoCo, Checkstyle)
  src/main/java/calculator/Calculator.java # arithmetic core (bugs fixed in Lab 4)
  src/main/java/calculator/Main.java       # command line entry point (Lab 6 CLI)
  src/main/java/calculator/CalcServer.java # Lab 7 HTTP API (JDK built-in HttpServer)
  src/test/java/calculator/                # 36 JUnit 5 tests
  Dockerfile                               # multi-stage build, port 8000
web/                                       # frontend service
  index.html / style.css / app.js          # static calculator UI
  default.conf.template                    # nginx reverse proxy (service name backend)
  Dockerfile                               # nginx:1.27-alpine, port 80
docker-compose.yml                         # two services, ports, depends_on, healthchecks
docs/lab6/Dockerfile.archived              # Lab 6 single-container image (kept for reference)
.github/workflows/ci-calculator.yml        # CI: build matrix + Compose smoke test
```

The single-container Lab 6 setup lives on in git history (tag `lab6-final`).
