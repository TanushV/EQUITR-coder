# requirements.md

## 1. Project Overview
Build a minimal HTTP web server that can listen on a configurable port and respond to incoming requests with basic route matching. The server must be able to distinguish between at least two distinct URL paths and return different content for each.

## 2. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | The server must listen on a TCP port specified at startup (default 8080). | Must |
| FR-2 | The server must respond with HTTP/1.1 compliant messages. | Must |
| FR-3 | The server must support a `GET /` route that returns a plain-text greeting. | Must |
| FR-4 | The server must support a `GET /health` route that returns `{"status":"ok"}` with `Content-Type: application/json`. | Must |
| FR-5 | Any other path must return `404 Not Found` with a plain-text body `Not Found`. | Must |
| FR-6 | The server must log each request to stdout in the format: `<method> <path> <status-code>`. | Should |
| FR-7 | The server must handle concurrent requests (i.e., not block on a single request). | Should |
| FR-8 | The server must shut down gracefully on `SIGINT` (Ctrl-C). | Should |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | Language | Use Python 3.9+ or Node.js 18+ (pick one). |
| TR-2 | Core library only | Use only the standard library (no external dependencies). |
| TR-3 | Entry point | Provide an executable script named `server.py` (Python) or `server.js` (Node). |
| TR-4 | Configuration | Accept an optional `--port` CLI argument; if omitted, default to 8080. |
| TR-5 | Encoding | All text responses must be UTF-8. |
| TR-6 | Headers | Always include `Content-Length` and `Content-Type` headers. |
| TR-7 | Directory layout | Single file; no subdirectories or build step required. |

## 4. Success Criteria
- [ ] `curl http://localhost:8080/` returns `200 OK` with body `Hello from /`.
- [ ] `curl http://localhost:8080/health` returns `200 OK` with JSON body `{"status":"ok"}`.
- [ ] `curl http://localhost:8080/missing` returns `404 Not Found` with body `Not Found`.
- [ ] Running `server.py --port 3000` (or `server.js --port 3000`) starts the server on port 3000.
- [ ] Two concurrent `curl` requests complete without error.
- [ ] Pressing Ctrl-C terminates the server within 2 seconds.