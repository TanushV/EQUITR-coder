# requirements.md

## 1. Project Overview
Build a minimal HTTP web server that can listen on a configurable port and respond to basic GET requests for a small set of predefined routes. The server should be self-contained, require no external dependencies, and be runnable with a single command.

## 2. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | The server must listen on a TCP port (default 8080) and accept incoming HTTP/1.1 connections. | Must |
| FR-2 | The server must respond with HTTP status codes 200, 404, and 405 as appropriate. | Must |
| FR-3 | The server must support the following routes and methods: | Must |
| | • `GET /` → return a plain-text greeting “Hello, World!” | |
| | • `GET /health` → return JSON `{"status":"ok"}` | |
| | • `GET /echo/<param>` → return plain-text `<param>` | |
| FR-4 | Any other path or HTTP method must return 404 Not Found or 405 Method Not Allowed respectively. | Must |
| FR-5 | The server must log every request to stdout in the format: `<timestamp> <method> <path> <status>` | Should |
| FR-6 | The server must be gracefully shut down on SIGINT (Ctrl-C). | Should |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | Language | Use Python 3.8+ standard library only (no external packages). |
| TR-2 | Entry point | Provide a single file `server.py` that can be started with `python server.py [--port PORT]`. |
| TR-3 | Port configuration | Accept an optional `--port` CLI argument; default to 8080. |
| TR-4 | Concurrency | Handle one request at a time (no threading/async required). |
| TR-5 | Headers | Always include `Content-Type` and `Content-Length` in responses. |
| TR-6 | Encoding | Use UTF-8 for all text bodies. |
| TR-7 | Directory layout | All code in one file; no subdirectories or config files. |

## 4. Success Criteria
- [ ] Running `python server.py` starts the server on port 8080 and prints “Listening on http://localhost:8080 …”.
- [ ] `curl -i http://localhost:8080/` returns HTTP 200 and body “Hello, World!”.
- [ ] `curl -i http://localhost:8080/health` returns HTTP 200 and JSON `{"status":"ok"}`.
- [ ] `curl -i http://localhost:8080/echo/abc123` returns HTTP 200 and body “abc123”.
- [ ] `curl -i http://localhost:8080/missing` returns HTTP 404.
- [ ] `curl -i -X POST http://localhost:8080/` returns HTTP 405.
- [ ] Every request appears in stdout with timestamp, method, path, and status.
- [ ] Pressing Ctrl-C shuts down the server cleanly.