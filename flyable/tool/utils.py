from dataclasses import dataclass, field
from typing import Literal, Callable, Any, Iterable


# ###################################### Step ###################################### #
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


# ###################################### list utils ###################################### #

def find_first(predicate: Callable[[Any], bool], iterable: Iterable):
    """Returns the first value that matches in the iterable"""
    for value in iterable:
        if predicate(value):
            return value
    return None


def find_last(predicate: Callable[[Any], bool], iterable: Iterable):
    """Returns the first value that matches in the iterable"""
    last_match = None
    for value in iterable:
        if predicate(value):
            last_match = value
    return last_match


def find_first_idx(predicate: Callable[[Any], bool], iterable: Iterable):
    """Returns the index of the first value that matches in the iterable"""
    for idx, value in enumerate(iterable):
        if predicate(value):
            return idx
    return None


def find_last_idx(predicate: Callable[[Any], bool], iterable: Iterable):
    """Returns the first value that matches in the iterable"""
    last_idx = None
    for idx, value in enumerate(iterable):
        if predicate(value):
            last_idx = idx
    return last_idx
