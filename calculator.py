import math

class Calculator:
    """Handles all mathematical operations."""

    SUPPORTED_OPERATIONS = ['+', '-', '*', '/', 'sqrt', 'pow', 'sin', 'cos', 'tan', 'log', 'log10']

    def calculate(self, operation, num1, num2=None):
        if operation not in self.SUPPORTED_OPERATIONS:
            raise ValueError("Unsupported operation")
       
        num1 = float(num1)
        binary_ops = ['+', '-', '*', '/', 'pow']
        
        if operation in binary_ops:
            if num2 is None:
                raise ValueError("Second number is required for this operation")
            num2 = float(num2)

        operations = {
            '+': lambda: num1 + num2,
            '-': lambda: num1 - num2,
            '*': lambda: num1 * num2,
            '/': lambda: num1 / num2 if num2 != 0 else (_ for _ in ()).throw(ZeroDivisionError("Cannot divide by zero")),
            'pow': lambda: math.pow(num1, num2),

            'sqrt': lambda: math.sqrt(num1) if num1 >= 0 else (_ for _ in ()).throw(ValueError("Cannot take sqrt of negative number")),
            'sin': lambda: math.sin(math.radians(num1)),
            'cos': lambda: math.cos(math.radians(num1)),
            'tan': lambda: math.tan(math.radians(num1)),
            'log': lambda: math.log(num1) if num1 > 0 else (_ for _ in ()).throw(ValueError("Log undefined for non-positive numbers")),
            'log10': lambda: math.log10(num1) if num1 > 0 else (_ for _ in ()).throw(ValueError("Log10 undefined for non-positive numbers")),
        }

        return operations[operation]()

    def format_expression(self, operation, num1, num2=None):
        if operation in ['+', '-', '*', '/', 'pow']:
            symbol = '^' if operation == 'pow' else operation
            return f"{num1} {symbol} {num2}"
        
        return f"{operation}({num1})"