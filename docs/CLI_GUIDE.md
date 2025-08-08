# CLI Guide

Note: Throughout the codebase and examples, we standardize on:
- Short name/title (task_name) via config.description
- Detailed task body passed as the first argument to execute_task (or via CLI/TUI input)

## Single Agent

Run a single agent task:

```
equitrcoder single "Implement a CLI calculator" --model moonshot/kimi-k2-0711-preview
```

Expected output:
```
🤖 Starting single agent task: Implement a CLI calculator
============================================================
[ASSISTANT] Planning task groups...
🔧 Using tool: list_task_groups
... (logs) ...
============================================================
✅ Task completed successfully!
💰 Total cost: $0.5234
🔄 Iterations: 7
```

## Multi-Agent Parallel

Run with supervisor/worker models and optional team profiles:

```
equitrcoder multi "Build a FastAPI + React app" \
  --supervisor-model moonshot/kimi-k2-0711-preview \
  --worker-model moonshot/kimi-k2-0711-preview \
  --workers 3 \
  --team backend_dev,frontend_dev,qa_engineer
```

Expected output:
```
🤖 Starting multi-agent task with 3 agents: Build a FastAPI + React app
============================================================
[ASSISTANT] Planning task groups...
🔧 Using tool: list_task_groups
... (parallel agent logs) ...
============================================================
✅ Multi-agent task completed successfully!
```

## Research Mode (ML)

Interactive collection of datasets and experiments, then full execution:

```
equitrcoder research "Evaluate ResNet on CIFAR-10" \
  --supervisor-model moonshot/kimi-k2-0711-preview \
  --worker-model moonshot/kimi-k2-0711-preview \
  --workers 3
```

Prompts:
```
Dataset path (blank to finish): ./data/cifar10
Short description: Local CIFAR-10 folder
Dataset path (blank to finish):
Any additional hardware notes? (blank to skip):
Experiment name (blank to finish): baseline
Shell command to run: python train.py --dataset cifar10 --epochs 1
Experiment name (blank to finish): augmented
Shell command to run: python train.py --dataset cifar10 --epochs 1 --augment
Experiment name (blank to finish):
```

Completion:
```
🎉 INITIAL PHASES COMPLETED!
🧪 Experiments complete. Generating supervisor report...
✅ Researcher mode completed successfully!
📄 Report: docs/task_20250101_153000/research_report.md
``` 