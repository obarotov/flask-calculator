class HistoryManager:
    def __init__(self, filepath='history.txt'):
        self.filepath = filepath

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
                    exp, res = line.strip().split("|")
                    history.append({"expression": exp, "result": res})
            return history
        except FileNotFoundError:
            return []

    def clear(self):
        open(self.filepath, 'w').close()