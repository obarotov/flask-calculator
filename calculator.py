import math

class Calculator:
    """Handles all mathematical operations."""

    SUPPORTED_OPERATIONS = ['+', '-', '*', '/', 'sqrt', 'pow', 'sin', 'cos', 'tan', 'log', 'log10']

    def calculate(self, operation, num1, num2=None):
        if operation == "+":
            return num1 + num2
        elif operation == "-":
            return num1 - num2
        elif operation == "*":  
            return num1 * num2
        elif operation == "/" and num2 != 0:
            return num1 / num2
        elif operation == "sqrt":
            return math.sqrt(num1)
        elif operation == "pow":
            return math.pow(num1,num2)
        elif operation == "sin":
            ans = math.radians(num1)
            return math.sin(ans)
        elif operation == "cos":
            ans = math.radians(num1)
            return math.cos(ans)
        elif operation == "tan":
            ans = math.radians(num1)
            return math.tan(ans)
        elif operation == "log":
            return math.log(num1)
        elif operation == "log10":
            return math.log10(num1)
    def format_expression(self, operation, num1, num2=None):
        """
        Return a human-readable string of the expression.
        Example: "sqrt(25)", "10 + 5", "sin(90)"
        """
        # TODO: Task 1 — implement this method
        pass




c = Calculator()
print(c.calculate('sqrt', 144))       # 12.0
print(c.calculate('+', 10, 5))        # 15.0
print(c.calculate('sin', 90))         # 1.0
print(c.format_expression('pow', 2, 8))  # "2 ^ 8"