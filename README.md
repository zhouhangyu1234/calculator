# Calculator (Lab 3 + Lab 4 + Lab 5 + Lab 6)

[![CI Calculator](https://github.com/zhouhangyu1234/calculator/actions/workflows/ci-calculator.yml/badge.svg)](https://github.com/zhouhangyu1234/calculator/actions/workflows/ci-calculator.yml)

Command line calculator built with Maven, covered by a JUnit 5 test suite,
automatically verified by a GitHub Actions CI pipeline and shipped as a Docker
image.

## Build and test locally

```bash
mvn clean compile     # compile all Java sources
mvn test              # run all JUnit 5 test cases
```

## Continuous Integration

Every push to `main` and every pull request targeting `main` triggers the
workflow defined in `.github/workflows/ci-calculator.yml`:

| Step | Command |
| --- | --- |
| Checkout | `actions/checkout@v4` |
| JDK setup | `actions/setup-java@v4` (JDK 17 + 21 matrix) |
| Dependency cache | `actions/cache@v4` on `~/.m2/repository` |
| Compile | `mvn clean compile` |
| Unit tests | `mvn test` |

The badge above always reflects the result of the latest CI run.

## Docker (Lab 6)

The image is built with a multi-stage `Dockerfile`: a Maven + JDK 17 stage
compiles the project and runs the tests, and only the resulting jar is copied
into a small JRE-Alpine runtime stage.

```bash
docker build -t calculator:lab6 .        # build the image
docker images                            # show the image and its size
docker run --rm calculator:lab6          # default: 10 / 4
docker run --rm calculator:lab6 2 + 3    # 5
docker run --rm calculator:lab6 10 / 0   # Error: Division by zero
```

Every push to `main` publishes the image to GitHub Container Registry:

```bash
docker pull ghcr.io/zhouhangyu1234/calculator:lab6
```

## Project layout

```
src/main/java/calculator/Calculator.java   # arithmetic core (bugs fixed in Lab 4)
src/main/java/calculator/Main.java         # command line entry point
src/test/java/calculator/CalculatorTest.java
src/test/java/calculator/MainTest.java
config/checkstyle.xml                      # static analysis rules
Dockerfile                                 # multi-stage container build (Lab 6)
.dockerignore                              # keeps the build context small
.github/workflows/ci-calculator.yml        # CI pipeline (Lab 5) + Docker job (Lab 6)
```
