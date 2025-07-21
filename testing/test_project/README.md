# Calculator Project

## Project Overview
This project is a Python-based calculator application with a command-line interface. It supports basic arithmetic operations such as addition, subtraction, multiplication, and division, while handling errors for invalid inputs and division by zero.

## Installation Guide
To set up the project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd calculator_project
   ```

2. **Set up a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage Instructions
Run the calculator application from the command line:

```bash
python cli.py
```

### Examples
- **Addition:**  `5 + 3`
- **Subtraction:** `10 - 2`
- **Multiplication:** `4 * 7`
- **Division:** `8 / 2`

### Error Handling
- Invalid inputs result in error messages.
- Division by zero will prompt a meaningful error message.

## Design and Architecture
The project follows a modular design:

- **Calculator Class:** Contains methods for arithmetic operations, input validation, and error handling.
- **CLI Interface:** Manages user interaction, input parsing, and output formatting.
- **Test Suite:** Includes unit tests for all methods and integration tests for the CLI.

### File Structure
```
calculator_project/
├── calculator.py          # Main calculator class
├── cli.py                # Command-line interface
├── test_calculator.py    # Unit tests
├── requirements.txt      # Dependencies
└── README.md            # Usage instructions
```

## Testing
Ensure all tests pass with:
```bash
pytest
```
The goal is to achieve at least 80% code coverage.

## Contribution Guidelines
If you wish to contribute, please fork the repository and submit a pull request. Ensure all new code is well-documented and tested.
