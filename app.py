import os
import uuid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from calculator import Calculator
from history_manager import HistoryManager
from converter import UnitConverter

app = Flask(__name__)
app.secret_key = os.urandom(24)

calc = Calculator()
unit_converter = UnitConverter()

@app.before_request
def ensure_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

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
                manager = HistoryManager(session['session_id'])
                manager.save(expression, result)

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

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({
                "success": False,
                "error": "Invalid JSON or missing Content-Type header"
            }), 400
        
        operation = data.get('operation')
        num1_raw = data.get('num1')
        num2_raw = data.get('num2')
        
        if operation is None:
            return jsonify({
                "success": False,
                "error": "Missing 'operation' field"
            }), 400
        
        if num1_raw is None:
            return jsonify({
                "success": False,
                "error": "Missing 'num1' field"
            }), 400
        
        try:
            num1 = float(num1_raw)
            num2 = float(num2_raw) if num2_raw is not None else None
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Invalid numeric values"
            }), 400
        
        try:
            result = calc.calculate(operation, num1, num2)
            expression = calc.format_expression(operation, num1, num2)
            
            if result is not None:
                manager = HistoryManager(session['session_id'])
                api_expression = f"[API] {expression}"
                manager.save(api_expression, result)
            
            return jsonify({
                "success": True,
                "expression": expression,
                "result": result
            })
            
        except ZeroDivisionError:
            return jsonify({
                "success": False,
                "error": "Division by zero is not allowed"
            }), 400
        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "An unexpected error occurred"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Server error"
        }), 500

@app.route('/history')
def history_page():
    manager = HistoryManager(session['session_id'])
    entries = manager.load()
    return render_template('history.html', entries=entries)

@app.route('/clear-history')
def clear_history():
    if 'session_id' in session:
        manager = HistoryManager(session['session_id'])
        manager.clear()
    return redirect(url_for('index'))

@app.route('/stats/chart')
def stats_chart():
    manager = HistoryManager(session['session_id'])
    entries = manager.load()
    
    results = []
    for entry in entries:
        try:
            result_value = float(entry["result"])
            results.append(result_value)
        except (ValueError, KeyError):
            continue
    
    if not results:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No calculation data available yet.\nMake some calculations first!', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14, color='gray')
        ax.set_title('Calculation Results Over Time')
        ax.set_xlabel('Calculation #')
        ax.set_ylabel('Result')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    else:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x_values = list(range(1, len(results) + 1))
        ax.plot(x_values, results, marker='o', linewidth=2, markersize=6, color='blue')
        
        ax.grid(True, alpha=0.3)
        
        ax.fill_between(x_values, results, alpha=0.2, color='blue')
        
        ax.set_title('Calculation Results Over Time', fontsize=16, fontweight='bold')
        ax.set_xlabel('Calculation # (in chronological order)', fontsize=12)
        ax.set_ylabel('Result Value', fontsize=12)
        
        if len(results) <= 20:
            ax.set_xticks(x_values)
        else:
            step = max(1, len(results) // 10)
            ax.set_xticks(x_values[::step])
        
        if len(results) <= 15:
            for i, value in enumerate(results, 1):
                ax.annotate(f'{value:.2f}', (i, value), 
                           textcoords="offset points", xytext=(0, 10), 
                           ha='center', fontsize=8)
        
        plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    return send_file(buf, mimetype='image/png')

@app.route('/stats')
def stats():
    manager = HistoryManager(session['session_id'])
    stats_data = manager.get_stats()
    return render_template('stats.html', stats=stats_data)

@app.route('/converter', methods=['GET', 'POST'])
def converter():
    categories = ['length', 'weight', 'temperature']
    result = None
    error = None
    
    selected_category = request.form.get('category', 'length')
    try:
        available_units = unit_converter.get_units(selected_category)
    except ValueError as e:
        available_units = []
        error = str(e)

    if request.method == 'POST':
        if request.form.get('value'):
            try:
                val_raw = request.form.get('value')
                val = float(val_raw)
                
                from_u = request.form.get('from_unit')
                to_u = request.form.get('to_unit')

                if not from_u or not to_u:
                    raise ValueError("Please select both units.")

                converted_val = unit_converter.convert(selected_category, val, from_u, to_u)
                result = converted_val 
                
            except ValueError as e:
                error = str(e)
            except Exception as e:
                error = f"Calculation error: {str(e)}"
    
    return render_template('converter.html', 
                         categories=categories,
                         selected_category=selected_category,
                         available_units=available_units,
                         result=result,
                         error=error)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)