import os
import uuid
from collections import Counter

class HistoryManager:
    def __init__(self, session_id):
        self.filepath = f"history_{session_id}.txt"

    def save(self, expression, result):
        with open(self.filepath, mode='a') as file:
            file.write(f"{expression}|{result}\n")

    def load(self):
        try:
            with open(self.filepath, mode='r') as file:
                lines = file.readlines()

            history = []
            for line in reversed(lines):
                if "|" in line:
                    parts = line.strip().split("|", 1)
                    if len(parts) == 2:
                        exp, res = parts
                        history.append({"expression": exp, "result": res})
            return history
        except FileNotFoundError:
            return []

    def clear(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def get_stats(self):
        entries = self.load()

        if not entries:
            return {
                'total_calculations': 0,
                'most_used_operation': 'N/A',
                'average_result': 0.0,
                'largest_result': 0.0,
                'smallest_result': 0.0
            }

        results = []
        operations = []

        for entry in entries:
            try:
                expression = entry["expression"]
                result_str = entry["result"]
                
                found_op = False
                for op in ['+', '-', '*', '/', '^', '%']:
                    if op in expression:
                        operations.append(op)
                        found_op = True
                        break
                if not found_op:
                    operations.append('unknown')
                
                results.append(float(result_str))
            except (ValueError, KeyError):
                continue
        if not results:
            return {
                'total_calculations': 0,
                'most_used_operation': 'N/A',
                'average_result': 0.0,
                'largest_result': 0.0,
                'smallest_result': 0.0
            }
        
        return {
            'total_calculations': len(results),
            'most_used_operation': self._get_most_used_operation(operations),
            'average_result': round(sum(results) / len(results), 2),
            'largest_result': round(max(results), 2),
            'smallest_result': round(min(results), 2)
        }

    def _get_most_used_operation(self, operations):
        if not operations:
            return 'N/A'
        return Counter(operations).most_common(1)[0][0]