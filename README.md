# 🧮 Flask Scientific Calculator

A web-based **scientific calculator** built using **Flask** and **Object-Oriented Programming (OOP)** principles.
This project demonstrates clean architecture, error handling, and file-based history tracking.

---

## Features

* Basic operations: `+`, `-`, `*`, `/`
* Scientific operations:

  * Square root (`sqrt`)
  * Power (`pow`)
  * Trigonometry (`sin`, `cos`, `tan`)
  * Logarithms (`log`, `log10`)
* Error handling (invalid input, math errors, server errors)
* Calculation history stored in a file
* Clean OOP-based structure
* Custom error pages (404, 500)

## 📁 Project Structure

```
flask_calculator/
│
├── app.py
├── calculator.py
├── history_manager.py
├── history.txt
└── templates/
    ├── index.html
    ├── history.html
    ├── 404.html
    └── 500.html
```

### 🔹 Responsibilities

* `app.py` → Flask routes only
* `calculator.py` → All math logic
* `history_manager.py` → File handling
* `templates/` → Frontend UI

---

#### Supported Operations:

```
['+', '-', '*', '/', 'sqrt', 'pow', 'sin', 'cos', 'tan', 'log', 'log10']
```

---