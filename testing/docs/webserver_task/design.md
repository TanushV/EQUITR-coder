# design.md

## 1. System Architecture

The system is a **single-process, single-threaded HTTP/1.1 server** built on Python’s built-in `socketserver.TCPServer`.  
It uses a custom `BaseHTTPRequestHandler` subclass to parse the request line, dispatch to route handlers, and emit responses.  
All state is kept in memory; there is no persistence layer.

```
┌────────────────────────────┐
│  CLI Argument Parser       │
│  (argparse)                │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│  HTTP Server               │
│  socketserver.TCPServer    │
│  + RequestHandler          │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│  Router                    │
│  • exact match table       │
│  • parametric match table  │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│  Handlers                  │
│  • /                       │
│  • /health                 │
│  • /echo/<param>           │
└────────────┬───────────────┘
             │
┌────────────┴───────────────┐
│  Logger                    │
│  (stdout, ISO-8601)        │
└────────────────────────────┘
```

## 2. Components

| Component | Responsibility | Python Artifact |
|---|---|---|
| **CLI Parser** | Parse `--port` argument, validate, and pass to server | `parse_cli()` |
| **HTTPServer** | Bind TCP socket, listen loop, graceful shutdown | `HTTPServer` (subclass of `socketserver.TCPServer`) |
| **RequestHandler** | Parse request line, headers, route, call handler, send response | `HTTPRequestHandler` (subclass of `BaseHTTPRequestHandler`) |
| **Router** | Map `(method, path)` → handler function | `Router` class with two dicts |
| **Handlers** | Generate response body & headers | `handle_root()`, `handle_health()`, `handle_echo(param)` |
| **Logger** | Format and print access log line | `log_request()` |

## 3. Data Flow

1. **Startup**  
   `python server.py [--port 8080]`  
   → `parse_cli()` → `port`  
   → instantiate `HTTPServer(('', port), HTTPRequestHandler)`  
   → `server.serve_forever()`

2. **Request**  
   Client → TCP SYN → accept() → `HTTPRequestHandler.handle()`  
   → `self.parse_request()` (built-in)  
   → `Router.dispatch(method, path)`  
   → handler returns `(status, headers, body)`  
   → `self.send_response(status)`  
   → `self.send_header(...)`  
   → `self.end_headers()`  
   → `self.wfile.write(body)`  
   → Logger prints `<timestamp> <method> <path> <status>`

3. **Shutdown**  
   SIGINT → `KeyboardInterrupt` → `server.shutdown()` → `server.server_close()` → exit 0.

## 4. Implementation Plan

| Step | Task | Deliverable |
|---|---|---|
| 1 | Scaffold `server.py` with shebang, imports, constants | `server.py` skeleton |
| 2 | Implement CLI parser (`argparse`) | `parse_cli()` |
| 3 | Create `Router` class with `add_route()` and `dispatch()` | `Router` |
| 4 | Implement three handlers returning tuples | `handle_root()`, `handle_health()`, `handle_echo()` |
| 5 | Subclass `BaseHTTPRequestHandler` | `HTTPRequestHandler` |
| 6 | Override `do_GET()` and `do_POST()` (and others) to call router | `do_GET`, `do_POST`, `do_PUT`, … |
| 7 | Add logging in `HTTPRequestHandler.log_message()` override | `log_request()` |
| 8 | Subclass `socketserver.TCPServer` to handle SIGINT gracefully | `HTTPServer` |
| 9 | Wire everything together in `if __name__ == "__main__"` block | `main()` |
| 10 | Manual testing with `curl` against success criteria | README section |

## 5. File Structure

```
.
└── server.py          # single-file implementation
```

Inside `server.py`:

```
0-20   #!/usr/bin/env python3
       import argparse, datetime, json, re, signal, socketserver, sys
       from http import HTTPStatus
       from http.server import BaseHTTPRequestHandler

21-40  # Constants
       DEFAULT_PORT = 8080
       ENCODING = 'utf-8'

41-80  # Router class
       class Router:
           def __init__(self):
               self.exact = {}
               self.param = []
           def add_route(self, pattern, handler):
               ...
           def dispatch(self, method, path):
               ...

81-120 # Handlers
       def handle_root():
           ...
       def handle_health():
           ...
       def handle_echo(param):
           ...

121-180 # HTTPRequestHandler
       class HTTPRequestHandler(BaseHTTPRequestHandler):
           router = Router()
           def do_GET(self):
               ...
           def log_message(self, fmt, *args):
               ...

181-220 # HTTPServer
       class HTTPServer(socketserver.TCPServer):
           allow_reuse_address = True
           def __init__(self, *args, **kwargs):
               super().__init__(*args, **kwargs)
               signal.signal(signal.SIGINT, self._signal_handler)
           def _signal_handler(self, signum, frame):
               print("\nShutting down gracefully...")
               self.shutdown()

221-250 # CLI parser
       def parse_cli():
           ...

251-270 # main()
       def main():
           ...
       if __name__ == "__main__":
           main()
```

No additional files, directories, or external dependencies are required.