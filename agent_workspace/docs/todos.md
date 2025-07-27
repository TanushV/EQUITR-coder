# todos.md

- [ ] Create project directory `hello-world/`
- [ ] Initialize git repository in `hello-world/`
- [ ] Create `.gitignore` file with Python cache patterns
- [ ] Create empty file `hello.py` in project root
- [ ] Open `hello.py` in text editor with UTF-8 encoding
- [ ] Add shebang line `#!/usr/bin/env python3` as first line
- [ ] Add newline after shebang line
- [ ] Add `print("Hello, World!")` as second line
- [ ] Save file and verify encoding is UTF-8
- [ ] Run `python hello.py` and verify output is exactly `Hello, World!`
- [ ] Run `echo $?` (Unix) or `echo %ERRORLEVEL%` (Windows) to verify exit code 0
- [ ] Run `chmod +x hello.py` on Unix-like systems
- [ ] Run `./hello.py` and verify same output
- [ ] Run `wc -c hello.py` and verify file size ≤ 100 bytes
- [ ] Install flake8 if not present: `pip install flake8`
- [ ] Run `flake8 hello.py` and verify no warnings or errors
- [ ] Run `python -m py_compile hello.py` to verify syntax
- [ ] Create `README.md` with usage instructions
- [ ] Add content to README:
  ```markdown
  # Hello World
  
  A minimal Python script that prints "Hello, World!"
  
  ## Usage
  ```bash
  python hello.py
  ```
  
  ## Direct execution (Unix)
  ```bash
  chmod +x hello.py
  ./hello.py
  ```
  ```
- [ ] Stage all files: `git add .`
- [ ] Commit with message: "feat: add hello world script"
- [ ] Create tag: `git tag -a v1.0.0 -m "Initial release"`