# requirements.md

## 1. Project Overview
The user wants to complete the first three open items listed in the `todos.md` file.  
The deliverable is a requirements document that captures what must be done to mark those three todos as “done”.

## 2. Functional Requirements
| ID | Requirement | Acceptance Criteria |
|--|--|--|
| FR-1 | Read the `todos.md` file | The file is successfully located and parsed; its contents are available in memory. |
| FR-2 | Identify the first three **open** todos | The system returns the exact text of the first three lines that start with `- [ ]` (unchecked checkbox). |
| FR-3 | Execute or implement each identified todo | For each of the three todos, the corresponding work is performed and the todo line is updated to `- [x]`. |
| FR-4 | Persist the updated `todos.md` | After all three todos are completed, the file is saved back to disk with the same name and location. |

## 3. Technical Requirements
- **Language / Runtime**: Any scripting language that can read/write UTF-8 text files (e.g., Python 3, Node.js, Bash).  
- **File Location**: `todos.md` is assumed to be in the current working directory.  
- **Todo Format**: Each open todo is a single line starting with `- [ ]` followed by a space and the task description.  
- **Concurrency**: Single-threaded execution is sufficient.  
- **Error Handling**:  
  - If `todos.md` does not exist, exit with a clear error message.  
  - If fewer than three open todos exist, process only the ones available and warn the user.  
- **Logging**: Print to stdout the text of each todo as it is completed.

## 4. Success Criteria
- [ ] The script runs without errors.  
- [ ] Exactly three `- [ ]` lines in `todos.md` are changed to `- [x]`.  
- [ ] The rest of the file remains unchanged.  
- [ ] The updated `todos.md` is saved to disk.