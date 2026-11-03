package calculator;

/**
 * Command line entry point of the packaged calculator jar.
 *
 * <p>Usage: java -jar calculator-1.0.0.jar &lt;number&gt; &lt;+|-|*|/&gt; &lt;number&gt;</p>
 */
public final class Main {

    private Main() {
    }

    /**
     * Parses the arguments, performs the calculation and prints the result.
     *
     * @param args command line arguments: a, operator, b
     */
    public static void main(String[] args) {
        if (args.length != 3) {
            System.out.println("Usage: java -jar calculator-1.0.0.jar <a> <op> <b>");
            System.out.println("Operators: + - * /");
            return;
        }

        Calculator cal = new Calculator();
        double a = Double.parseDouble(args[0]);
        double b = Double.parseDouble(args[2]);
        String op = args[1];

        try {
            switch (op) {
                case "+" -> System.out.println("Result: " + cal.add((int) a, (int) b));
                case "-" -> System.out.println("Result: " + cal.subtract((int) a, (int) b));
                case "*" -> System.out.println("Result: " + cal.multiply((int) a, (int) b));
                case "/" -> System.out.println("Result: " + cal.divide(a, b));
                default -> System.out.println("Unknown operator: " + op);
            }
        } catch (ArithmeticException e) {
            System.out.println("Error: " + e.getMessage());
        }
    }
}
