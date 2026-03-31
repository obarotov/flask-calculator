from flask import Flask, render_template, request, redirect, url_for
from calculator import Calculator
from history_manager import HistoryManager

app = Flask(__name__)
calc = Calculator()
history = HistoryManager()


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    expression = None
    error = None

    if request.method == 'POST':
        try:
            operation = request.form.get('operation')
            num1_raw = request.form.get('num1')
            num2_raw = request.form.get('num2')

            if not num1_raw:
                raise ValueError("First number is required")
            num1 = float(num1_raw)
            num2 = float(num2_raw) if num2_raw else None

            result = calc.calculate(operation, num1, num2)
            expression = calc.format_expression(operation, num1, num2)

            if result is not None:
                history.save(expression, result)

        except ZeroDivisionError:
            error = "Division by zero is not allowed."
        except ValueError as e:
            error = str(e)
        except Exception:
            error = "An unexpected error occured"

    return render_template('index.html',
                           result=result,
                           expression=expression,
                           error=error,
                           operations=Calculator.SUPPORTED_OPERATIONS)


@app.route('/history')
def history_page():
    manager = HistoryManager()
    entries = manager.load()
    return render_template('history.html', entries=entries)


@app.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        history.clear()
        return redirect(url_for('history_page'))
    except Exception as e:
        return redirect(url_for('history_page'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)