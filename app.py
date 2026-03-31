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
        pass  # TODO: Task 2 — handle form submission

    return render_template('index.html',
                           result=result,
                           expression=expression,
                           error=error,
                           operations=Calculator.SUPPORTED_OPERATIONS)


@app.route('/history')
def history_page():
    entries = history.load()
    return render_template('history.html', entries=entries)


@app.route('/clear-history', methods=['POST'])
def clear_history():
    # TODO: Bonus
    pass


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)