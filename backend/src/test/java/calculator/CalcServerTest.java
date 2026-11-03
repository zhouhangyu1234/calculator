package calculator;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Lab 7 - unit tests for the HTTP layer of the backend service.
 *
 * <p>{@link CalcServer#compute(Map)} is a pure function, so the API can be tested
 * without starting a server or a container: the transport is the only part left
 * to the compose smoke test.</p>
 */
@DisplayName("CalcServer API")
class CalcServerTest {

    private static CalcServer.ApiResult call(String a, String op, String b) {
        return CalcServer.compute(Map.of("a", a, "op", op, "b", b));
    }

    @Nested
    @DisplayName("successful calculations")
    class Success {

        @ParameterizedTest(name = "{0} {1} {2} = {3}")
        @CsvSource({
                "2,    +, 3,  5",
                "10,   -, 4,  6",
                "6,    *, 7,  42",
                "10,   /, 4,  2.5",
                "-7,   +, 3,  -4",
                "2.5,  +, 2,  4"
        })
        @DisplayName("returns 200 and the expected result")
        void computesExpectedResult(String a, String op, String b, String expected) {
            CalcServer.ApiResult result = call(a, op, b);

            assertThat(result.status()).isEqualTo(200);
            assertThat(result.body()).contains("\"ok\":true")
                    .contains("\"result\":" + expected);
        }

        @Test
        @DisplayName("accepts x as an alias for multiplication")
        void acceptsXAsMultiplication() {
            assertThat(call("6", "x", "7").body()).contains("\"result\":42");
            assertThat(call("6", "X", "7").body()).contains("\"result\":42");
        }

        @Test
        @DisplayName("prints whole numbers without a decimal part")
        void formatsWholeNumbers() {
            assertThat(CalcServer.format(5.0)).isEqualTo("5");
            assertThat(CalcServer.format(2.5)).isEqualTo("2.5");
            assertThat(CalcServer.format(-0.75)).isEqualTo("-0.75");
        }
    }

    @Nested
    @DisplayName("error handling")
    class Errors {

        @Test
        @DisplayName("division by zero is a 400, never Infinity")
        void divisionByZero() {
            CalcServer.ApiResult result = call("10", "/", "0");

            assertThat(result.status()).isEqualTo(400);
            assertThat(result.body()).contains("Division by zero")
                    .doesNotContain("Infinity")
                    .doesNotContain("NaN");
        }

        @Test
        @DisplayName("unknown operator is rejected")
        void unknownOperator() {
            assertThat(call("1", "%", "2").status()).isEqualTo(400);
            assertThat(call("1", "%", "2").body()).contains("Unknown operator");
        }

        @Test
        @DisplayName("non-numeric operands are rejected")
        void nonNumericOperands() {
            CalcServer.ApiResult result = call("abc", "+", "2");

            assertThat(result.status()).isEqualTo(400);
            assertThat(result.body()).contains("must be numbers");
        }

        @Test
        @DisplayName("missing parameters are reported by name")
        void missingParameter() {
            CalcServer.ApiResult result = CalcServer.compute(Map.of("a", "1"));

            assertThat(result.status()).isEqualTo(400);
            assertThat(result.body()).contains("a, op and b");
        }
    }

    @Nested
    @DisplayName("query parsing")
    class QueryParsing {

        @Test
        @DisplayName("decodes percent-encoded operators")
        void decodesPercentEncodedOperator() {
            Map<String, String> params = CalcServer.queryParams("a=6&op=%2A&b=7");

            assertThat(params).containsEntry("op", "*");
            assertThat(CalcServer.compute(params).body()).contains("\"result\":42");
        }

        @Test
        @DisplayName("tolerates an empty query string")
        void toleratesEmptyQuery() {
            assertThat(CalcServer.queryParams(null)).isEmpty();
            assertThat(CalcServer.queryParams("")).isEmpty();
        }

        @Test
        @DisplayName("normalises the supported operator spellings")
        void normalisesOperators() {
            assertThat(CalcServer.normaliseOperator("*")).isEqualTo("*");
            assertThat(CalcServer.normaliseOperator(" x ")).isEqualTo("*");
            assertThat(CalcServer.normaliseOperator("//")).isNull();
        }
    }
}
