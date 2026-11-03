# =============================================================================
# Lab 6 - Containerised Java calculator (multi-stage build)
#
# Stage 1 (builder) : a full Maven + JDK image, used only to compile and package
# Stage 2 (runtime) : a small JRE-only image, containing nothing but the jar
#
# The two stages are built from the same Dockerfile, but only stage 2 becomes the
# final image. Everything Maven downloaded (hundreds of MB) stays behind in
# stage 1 and is never shipped to the user.
# =============================================================================


# -----------------------------------------------------------------------------
# STAGE 1 - build
# -----------------------------------------------------------------------------
# FROM selects the base image and names this stage "builder".
# maven:3.9-eclipse-temurin-17 already contains Maven 3.9 and JDK 17, which is
# exactly the toolchain the project declares in pom.xml (maven.compiler.release=17).
FROM maven:3.9-eclipse-temurin-17 AS builder

# WORKDIR sets (and creates) the working directory for every following step, so
# no instruction has to repeat an absolute path.
WORKDIR /build

# COPY the POM alone, before the sources. Docker reuses a cached layer as long as
# its input files did not change; separating pom.xml from src/ means the slow
# dependency download below is skipped whenever only Java code changed.
COPY pom.xml .

# RUN executes a command inside the image during the build.
# It downloads every dependency into ~/.m2 so that the next step can work offline.
RUN mvn -B -q dependency:go-offline

# Now copy the actual sources (this layer busts the cache on every code change,
# which is fine because it is cheap compared to the dependency download).
COPY src ./src

# Package the application: compile, run all JUnit tests, and produce
# target/calculator-1.0.0.jar. Tests are deliberately NOT skipped here - the
# image can only be produced if the test suite passes, so a broken build never
# turns into a broken image.
RUN mvn -B clean package


# -----------------------------------------------------------------------------
# STAGE 2 - runtime
# -----------------------------------------------------------------------------
# A JRE-only Alpine image: no Maven, no JDK, no compiler, ~180 MB instead of
# ~800 MB. Smaller images pull faster and expose a smaller attack surface,
# because a compiler inside a production container is a tool an attacker can use.
FROM eclipse-temurin:17-jre-alpine

# Documentation only - records who maintains the image.
LABEL maintainer="zhouhangyu1234" \
      description="Lab 6 calculator, multi-stage build"

WORKDIR /app

# Run as a non-root user. A process inside a container is still a process on the
# host kernel; if it is ever compromised, root inside the container is a far
# better starting point for an attacker than an unprivileged user.
RUN addgroup -S app && adduser -S -G app app

# COPY --from=builder takes ONE file out of stage 1: the packaged jar. Nothing
# else survives the stage boundary, which is the entire point of a multi-stage
# build - the 800 MB toolchain is discarded.
COPY --from=builder /build/target/calculator-1.0.0.jar /app/calculator.jar

# Hand ownership of the jar to the unprivileged user created above.
RUN chown app:app /app/calculator.jar

USER app

# ENTRYPOINT is the fixed command that always runs; it cannot be replaced by
# arguments passed to `docker run`, only appended to.
ENTRYPOINT ["java", "-jar", "/app/calculator.jar"]

# CMD supplies the DEFAULT arguments, which `docker run <image> 2 + 3` replaces.
# A bare `docker run` therefore still demonstrates the calculator instead of
# printing the usage message.
CMD ["10", "/", "4"]
