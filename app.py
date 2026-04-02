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

@app.route('/clear-session')
def clear_session():
    if 'session_id' in session:
        manager = HistoryManager(session['session_id'])
        manager.clear()
        session.clear()
    return redirect(url_for('index'))

@app.route('/stats/chart')
def stats_chart():
    import matplotlib.patches as mpatches
    import numpy as np

    manager = HistoryManager(session['session_id'])
    entries = manager.load()

    results = []
    for entry in entries:
        try:
            results.append(float(entry["result"]))
        except (ValueError, KeyError):
            continue

    BG    = '#0a0a0a'
    CARD  = '#161616'
    GREEN = '#1DB954'
    AMBER = '#f59e0b'
    MUTED = '#6b6b6b'
    SOFT  = '#a0a0a0'
    WHITE = '#f0f0f0'
    GRID  = '#1e1e1e'

    fig = plt.figure(figsize=(12, 6), facecolor=BG)
    if not results:
        ax = fig.add_axes([0.08, 0.14, 0.88, 0.72], facecolor=CARD)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.55, 'No data yet',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=16, fontweight='bold', color=SOFT)
        ax.text(0.5, 0.42, 'Make some calculations and come back!',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=10, color=MUTED)
        fig.text(0.08, 0.93, 'Calculation Results Over Time',
                 fontsize=14, fontweight='bold', color=WHITE)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=BG)
        buf.seek(0)
        plt.close(fig)
        return send_file(buf, mimetype='image/png')

    x       = list(range(1, len(results) + 1))
    avg     = sum(results) / len(results)
    rolling = [
        sum(results[max(0, i - 2):i + 1]) / len(results[max(0, i - 2):i + 1])
        for i in range(len(results))
    ]

    ax = fig.add_axes([0.08, 0.14, 0.88, 0.72], facecolor=CARD)

    ax.fill_between(x, results, alpha=0.15, color=GREEN, linewidth=0)

    ax.plot(x, results, color=GREEN, linewidth=2.5, zorder=4,
            solid_capstyle='round')

    dot_size = 55 if len(results) <= 30 else 20
    ax.scatter(x, results, color=GREEN, s=dot_size, zorder=5,
               edgecolors=BG, linewidths=1.8)

    ax.plot(x, rolling, color=AMBER, linewidth=1.5,
            linestyle='--', dashes=(5, 4), zorder=3, alpha=0.85)

    ax.axhline(avg, color=MUTED, linewidth=1, linestyle=':', alpha=0.5)

    ax.annotate(f'{results[-1]:g}',
                xy=(x[-1], results[-1]),
                xytext=(7, 0), textcoords='offset points',
                color=GREEN, fontsize=9, fontweight='bold', va='center')

    if len(results) >= 3:
        max_i = results.index(max(results))
        min_i = results.index(min(results))
        for idx, label, offset in [(max_i, f'↑ {results[max_i]:g}', (0, 10)),
                                   (min_i, f'↓ {results[min_i]:g}', (0, -14))]:
            ax.annotate(label,
                        xy=(x[idx], results[idx]),
                        xytext=offset, textcoords='offset points',
                        color=SOFT, fontsize=8, ha='center')

    ax.grid(True, which='major', color=GRID, linewidth=0.8, linestyle='-')
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=SOFT, labelsize=9, length=0, pad=6)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(SOFT)

    if len(results) <= 20:
        ax.set_xticks(x)
        ax.set_xticklabels([str(i) for i in x], fontsize=8)
    else:
        step = max(1, len(results) // 10)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([str(i) for i in x[::step]], fontsize=8)

    ax.set_xlabel('Calculation #', fontsize=10, color=SOFT, labelpad=10)
    ax.set_ylabel('Result Value',  fontsize=10, color=SOFT, labelpad=10)


    fig.text(0.08, 0.93, 'Calculation Results Over Time',
             fontsize=14, fontweight='bold', color=WHITE)
    fig.text(0.08, 0.885,
             f'Session  ·  {len(results)} calculation{"s" if len(results) != 1 else ""}  '
             f'·  avg {avg:.4g}  ·  '
             f'min {min(results):g}  ·  max {max(results):g}',
             fontsize=8.5, color=MUTED)
    
    leg_items = [
        mpatches.Patch(color=GREEN, label='Result'),
        mpatches.Patch(color=AMBER, label='Rolling avg (3)'),
        mpatches.Patch(color=MUTED, label=f'Mean: {avg:.4g}'),
    ]
    ax.legend(handles=leg_items, loc='upper left', frameon=True,
              facecolor=CARD, edgecolor='#2a2a2a', labelcolor=SOFT,
              fontsize=8.5, borderpad=0.9, handlelength=1.4)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=BG)
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