import asyncio
from datetime import datetime
from pathlib import Path
import os

from textual.widgets import Input, Select, Button

from equitrcoder.ui.advanced_tui import EquitrTUI

# This example drives the Advanced TUI end-to-end using Textual's headless test harness.
# It configures the same models used in examples/research_programmatic_example.py and
# executes both Research Mode and Multi-Agent Mode runs, similar to real user interaction.

SUPERVISOR_MODEL = "gpt-5"          # same as research_programmatic_example.py
WORKER_MODEL = "gpt-5-mini"          # same as research_programmatic_example.py

RESEARCH_TASK = (
    "Generate a synthetic dataset and run simple experiments to pick the best heuristic, "
    "then produce a brief report."
)
MULTI_TASK = (
    "Create a small CLI utility that reads a CSV, computes per-column means, and writes a JSON summary."
)

async def run_research_flow(app: EquitrTUI):
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        # Provide a task on startup input
        app.query_one("#startup-input", Input).value = RESEARCH_TASK
        # Invoke Start without mouse click
        btn = app.query_one("#btn-start", Button)
        await app.on_button_pressed(Button.Pressed(btn))
        await pilot.pause(0.2)

        # Ensure a session exists and set explicit id for traceability
        cmd = app.query_one("#command-input", Input)
        cmd.value = "/session new rese2e"
        await pilot.press("enter")
        await pilot.pause(0.2)

        # Set models and mode using slash commands (bypasses Select options constraint)
        cmd.value = f"/set supervisor {SUPERVISOR_MODEL}"
        await pilot.press("enter")
        await pilot.pause(0.2)
        cmd.value = f"/set worker {WORKER_MODEL}"
        await pilot.press("enter")
        await pilot.pause(0.2)
        cmd.value = "/mode research"
        await pilot.press("enter")
        await pilot.pause(0.2)

        # Execute run using slash command (mirrors user flow)
        cmd.value = f"/run {RESEARCH_TASK}"
        await pilot.press("enter")

        # Let it run for a while (this will call into real backend). Adjust timeout as needed.
        await pilot.pause(600.0)


async def run_multi_flow(app: EquitrTUI):
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        # Provide a task on startup input
        app.query_one("#startup-input", Input).value = MULTI_TASK
        # Invoke Start without mouse click
        btn = app.query_one("#btn-start", Button)
        await app.on_button_pressed(Button.Pressed(btn))
        await pilot.pause(0.2)

        # Ensure a session exists for the multi run
        cmd = app.query_one("#command-input", Input)
        cmd.value = "/session new multie2e"
        await pilot.press("enter")
        await pilot.pause(0.2)

        # Set models and mode using slash commands
        cmd.value = f"/set supervisor {SUPERVISOR_MODEL}"
        await pilot.press("enter")
        await pilot.pause(0.2)
        cmd.value = f"/set worker {WORKER_MODEL}"
        await pilot.press("enter")
        await pilot.pause(0.2)
        cmd.value = "/mode multi-parallel"
        await pilot.press("enter")
        await pilot.pause(0.2)

        # Execute run using slash command
        cmd.value = f"/run {MULTI_TASK}"
        await pilot.press("enter")

        await pilot.pause(600.0)

async def main():
    # Use project-local output space, like programmatic examples do
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = Path(f"generated_projects/tui_e2e_{ts}").resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(project_dir))

    # Research Mode flow
    research_app = EquitrTUI(mode="research")
    await run_research_flow(research_app)

    # Multi-Agent Mode flow
    multi_app = EquitrTUI(mode="multi")
    await run_multi_flow(multi_app)

if __name__ == "__main__":
    asyncio.run(main()) 