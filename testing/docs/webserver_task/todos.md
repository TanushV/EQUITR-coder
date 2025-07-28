# Project Tasks

## Core Server Setup & CLI
- [ ] Create server.py file structure and imports
  - Set up the basic server.py file with proper shebang, imports (argparse, datetime, json, re, signal, socketserver, sys, http modules), and constants (DEFAULT_PORT=8080, ENCODING='utf-8')
- [ ] Implement CLI argument parser (can work in parallel)
  - Create parse_cli() function using argparse to handle --port argument with default 8080, validate port number is valid (1-65535), and return parsed port
- [ ] Create HTTPServer class with graceful shutdown (can work in parallel)
  - Subclass socketserver.TCPServer to create HTTPServer class with allow_reuse_address=True, implement __init__ with signal handler for SIGINT, and add _signal_handler method for graceful shutdown

## Routing System
- [ ] Implement Router class with exact and parametric matching
  - Create Router class with __init__ method initializing self.exact (dict) and self.param (list), add add_route method to register routes, and dispatch method to match (method, path) to appropriate handler
- [ ] Register all required routes (can work in parallel)
  - In Router initialization, register exact routes: ('GET', '/') → handle_root, ('GET', '/health') → handle_health, and parametric route: ('GET', '/echo/<param>') → handle_echo

## Request Handlers
- [ ] Implement handle_root() function (can work in parallel)
  - Create handle_root() function that returns tuple (200, {'Content-Type': 'text/plain; charset=utf-8'}, 'Hello, World!') with proper UTF-8 encoding
- [ ] Implement handle_health() function (can work in parallel)
  - Create handle_health() function that returns tuple (200, {'Content-Type': 'application/json; charset=utf-8'}, JSON string {"status":"ok"}) with proper UTF-8 encoding
- [ ] Implement handle_echo(param) function (can work in parallel)
  - Create handle_echo(param) function that takes URL parameter and returns tuple (200, {'Content-Type': 'text/plain; charset=utf-8'}, param) with proper UTF-8 encoding

## HTTP Request Handler
- [ ] Create HTTPRequestHandler class structure
  - Subclass BaseHTTPRequestHandler to create HTTPRequestHandler class, initialize router as class variable, and set up basic structure for handling HTTP methods
- [ ] Implement do_GET method with routing (can work in parallel)
  - Override do_GET() method to parse request path, call router.dispatch('GET', path), handle returned tuple (status, headers, body), send response with proper headers including Content-Length, and handle 404 for unmatched routes
- [ ] Implement other HTTP methods for 405 responses (can work in parallel)
  - Override do_POST(), do_PUT(), do_DELETE(), do_PATCH(), etc. methods to return 405 Method Not Allowed for any non-GET requests on any path
- [ ] Implement request logging (can work in parallel)
  - Override log_message() method to format and print access logs in format: <ISO-8601 timestamp> <method> <path> <status> to stdout

## Integration & Testing
- [ ] Create main() function to wire everything together
  - Implement main() function that calls parse_cli() to get port, creates HTTPServer instance with HTTPRequestHandler, prints 'Listening on http://localhost:{port} ...', and calls serve_forever() with proper exception handling
- [ ] Add __main__ block and final integration (can work in parallel)
  - Add if __name__ == '__main__': main() block at end of file, ensure all components are properly connected and server starts correctly
- [ ] Manual testing against success criteria (can work in parallel)
  - Test all success criteria: server starts on 8080, GET / returns 200 with 'Hello, World!', GET /health returns JSON, GET /echo/test returns 'test', GET /missing returns 404, POST / returns 405, logs appear in stdout, Ctrl-C shuts down gracefully

