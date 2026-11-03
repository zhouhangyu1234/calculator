package calculator;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.LocalTime;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Executors;

/**
 * Lab 7 - HTTP front door of the calculator backend service.
 *
 * <p>The class reuses the {@link Calculator} core written in Lab 3 and tested in
 * Lab 4; it adds nothing but a transport layer. No third-party web framework is
 * used: the JDK ships with {@code com.sun.net.httpserver}, which keeps the image
 * small and the build reproducible (no dependency download inside the image).</p>
 *
 * <p>Endpoints:</p>
 * <ul>
 *   <li>{@code GET /health} - liveness probe used by Docker's HEALTHCHECK and by
 *       {@code depends_on: condition: service_healthy}. It also echoes the
 *       LOG_LEVEL that was injected by docker-compose, which proves that the
 *       environment variable reached the container.</li>
 *   <li>{@code GET /api/calc?a=10&op=/&b=4} - performs one calculation and
 *       returns JSON.</li>
 * </ul>
 *
 * <p>Configuration is read from the environment only, never hard-coded:
 * {@code PORT} (default 8000) and {@code LOG_LEVEL} (default INFO).</p>
 */
public final class CalcServer {

    /** Port used when the PORT environment variable is absent. */
    static final int DEFAULT_PORT = 8000;

    /** Shared calculator core; the class is stateless, so one instance is enough. */
    private static final Calculator CALC = new Calculator();

    /** Minimum level that is printed: DEBUG &lt; INFO &lt; WARN. */
    private static volatile String logLevel = "INFO";

    /** Port actually bound by the running server, reported by /health. */
    private static volatile int port = DEFAULT_PORT;

    private CalcServer() {
    }

    /** Result of one API call: HTTP status plus JSON body. */
    public record ApiResult(int status, String body) {
    }

    /**
     * Starts the HTTP server and blocks forever (the container is the process supervisor).
     *
     * @param args ignored
     * @throws IOException when the port cannot be bound
     */
    public static void main(String[] args) throws IOException {
        port = Integer.parseInt(env("PORT", String.valueOf(DEFAULT_PORT)));
        logLevel = env("LOG_LEVEL", "INFO").trim().toUpperCase();

        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
        server.createContext("/health", CalcServer::handleHealth);
        server.createContext("/api/calc", CalcServer::handleCalc);
        server.setExecutor(Executors.newFixedThreadPool(4));

        server.start();
        log("INFO", "calculator-backend started on 0.0.0.0:" + port);
        log("INFO", "log level: " + logLevel);
    }

    // ------------------------------------------------------------------ routes

    /** {@code GET /health} - always 200 while the process is alive. */
    static void handleHealth(HttpExchange exchange) throws IOException {
        String body = "{\"status\":\"ok\",\"service\":\"calculator-backend\","
                + "\"logLevel\":\"" + logLevel + "\",\"port\":" + port + "}";
        send(exchange, 200, body);
    }

    /** {@code GET /api/calc?a=10&op=/&b=4} */
    static void handleCalc(HttpExchange exchange) throws IOException {
        ApiResult result = compute(queryParams(exchange.getRequestURI().getRawQuery()));
        if (result.status() == 200) {
            log("INFO", "calc ok: " + result.body());
        } else {
            log("WARN", "calc failed: " + result.body());
        }
        send(exchange, result.status(), result.body());
    }

    // ------------------------------------------------------------------- logic

    /**
     * Pure function behind {@code /api/calc}. Kept free of I/O so that it can be
     * unit-tested without opening a socket (Lab 4 discipline applied to Lab 7).
     *
     * @param params a, op, b as received from the query string
     * @return status code and JSON payload
     */
    public static ApiResult compute(Map<String, String> params) {
        String rawA = params.get("a");
        String rawB = params.get("b");
        String op = params.get("op");

        if (rawA == null || rawB == null || op == null) {
            return error(400, "Missing parameter: a, op and b are all required");
        }

        double a;
        double b;
        try {
            a = Double.parseDouble(rawA.trim());
            b = Double.parseDouble(rawB.trim());
        } catch (NumberFormatException e) {
            return error(400, "Operands must be numbers");
        }

        String operator = normaliseOperator(op);
        if (operator == null) {
            return error(400, "Unknown operator: " + op);
        }

        try {
            double value = switch (operator) {
                case "+" -> CALC.add((int) a, (int) b);
                case "-" -> CALC.subtract((int) a, (int) b);
                case "*" -> CALC.multiply((int) a, (int) b);
                default -> CALC.divide(a, b);
            };
            String body = "{\"ok\":true,\"a\":" + format(a)
                    + ",\"op\":\"" + operator + "\",\"b\":" + format(b)
                    + ",\"result\":" + format(value) + "}";
            return new ApiResult(200, body);
        } catch (ArithmeticException e) {
            return error(400, e.getMessage());
        }
    }

    /** Accepts the four operators plus the ASCII-safe aliases used in URLs. */
    static String normaliseOperator(String op) {
        String value = op.trim();
        return switch (value) {
            case "+", "-", "/" -> value;
            case "*", "x", "X" -> "*";
            default -> null;
        };
    }

    /** Prints whole numbers without a trailing ".0" (12 instead of 12.0). */
    static String format(double value) {
        if (!Double.isNaN(value) && !Double.isInfinite(value) && value == Math.rint(value)) {
            return String.valueOf((long) value);
        }
        return String.valueOf(value);
    }

    // ----------------------------------------------------------------- plumbing

    private static ApiResult error(int status, String message) {
        return new ApiResult(status, "{\"ok\":false,\"error\":\"" + message.replace("\"", "'") + "\"}");
    }

    static Map<String, String> queryParams(String rawQuery) {
        Map<String, String> params = new HashMap<>();
        if (rawQuery == null || rawQuery.isEmpty()) {
            return params;
        }
        for (String pair : rawQuery.split("&")) {
            int eq = pair.indexOf('=');
            if (eq > 0) {
                params.put(decode(pair.substring(0, eq)), decode(pair.substring(eq + 1)));
            }
        }
        return params;
    }

    private static String decode(String value) {
        return java.net.URLDecoder.decode(value, StandardCharsets.UTF_8);
    }

    private static void send(HttpExchange exchange, int status, String body) throws IOException {
        byte[] payload = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
        exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(status, payload.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(payload);
        }
    }

    private static String env(String name, String fallback) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? fallback : value;
    }

    /** Very small logger: the level filter is the point, not the formatting. */
    static void log(String level, String message) {
        if (rank(level) < rank(logLevel)) {
            return;
        }
        System.out.printf("%s [%s] %s%n", LocalTime.now().withNano(0), level, message);
    }

    private static int rank(String level) {
        return switch (level) {
            case "DEBUG" -> 0;
            case "INFO" -> 1;
            default -> 2;
        };
    }
}
