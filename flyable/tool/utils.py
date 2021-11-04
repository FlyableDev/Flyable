from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Step:
    name: str
    status: Literal["idle", "ongoing", "completed",
                    "interrupted"] = field(default="idle")

    def start(self):
        print(f"[START] {self.name}...")
        self.status = "ongoing"

    def end(self):
        print(f"[COMPLETE] {self.name}")
        self.status = "completed"

    def interrupted(self):
        print(f"[INTERRUPTED] {self.name}")
        self.status = "interrupted"


__current_step: Step = None


def start_step(step_name: str):
    global __current_step
    __current_step = Step(name=step_name)
    __current_step.start()


def end_step():
    global __current_step
    __current_step and __current_step.end()
    __current_step = None
