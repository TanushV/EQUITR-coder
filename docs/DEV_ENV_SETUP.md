# Python 3.9 Virtual Environment Setup

## 1. Create a virtual environment (Python 3.9 required)

On Unix/macOS:
```sh
python3.9 -m venv venv
source venv/bin/activate
```

On Windows:
```bat
python -m venv venv
venv\Scripts\activate
```

## 2. Install dependencies
```sh
pip install -r requirements.txt
```

## 3. Install pre-commit hooks (recommended)
```sh
pip install pre-commit
pre-commit install
```

## 4. Run the game
```sh
make run
```

## 5. Run tests
```sh
make test
```

---

For any issues, see README.md or contact the devops team.
