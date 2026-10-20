# Calculator (Lab 3 + Lab 4 + Lab 5)

[![CI Calculator](https://github.com/zhouhangyu1234/calculator/actions/workflows/ci-calculator.yml/badge.svg)](https://github.com/zhouhangyu1234/calculator/actions/workflows/ci-calculator.yml)

Command line calculator built with Maven, covered by a JUnit 5 test suite and
automatically verified by a GitHub Actions CI pipeline.

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

## Project layout

```
src/main/java/calculator/Calculator.java   # arithmetic core (bugs fixed in Lab 4)
src/main/java/calculator/Main.java         # command line entry point
src/test/java/calculator/CalculatorTest.java
src/test/java/calculator/MainTest.java
config/checkstyle.xml                      # static analysis rules
.github/workflows/ci-calculator.yml        # CI pipeline (Lab 5)
```
