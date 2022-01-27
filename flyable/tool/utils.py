from dataclasses import dataclass, field
from typing import Literal, Callable, Any, Iterable


# ###################################### Step ###################################### #
@dataclass
class Step:
    name: str
    status: Literal["idle", "ongoing", "completed", "interrupted"] = field(
        default="idle"
    )

    def start(self):
        print(f"[START] {self.name}...")
        self.status = "ongoing"

    def end(self):
        print(f"[COMPLETE] {self.name}")
        self.status = "completed"

    def interrupt(self, reason: str):
        print(f"[INTERRUPTED] {self.name} because {reason}")
        self.status = "interrupted"


__current_step: list[Step] = []


def get_step(step_name: str):
    """
    returns the step with the matching name or None if they are no step with a matching name
    """
    return find_first(lambda step_: step_.name == step_name, __current_step)


def get_step_idx(step_name: str):
    """
    returns the step index with the matching name or None if they are no step with a matching name
    """
    return find_first_idx(lambda step_: step_.name == step_name, __current_step)


def add_step(step_name: str, start: bool = True):
    step = Step(name=step_name)
    __current_step.append(step)
    if start:
        step.start()


def start_step(step_name: str):
    step = get_step(step_name)
    step and step.start()


def interrupt_step(reason: str, cascade: bool = False, step_name: str = None):
    """
    Interrupts a certain step or the current step. If cascade is set to True, also interrupts all the step
    above the step interrupted

    :param reason: the reason for the interruption
    :param cascade: if the interruption should interrupt all step over this one
    :param step_name: the name of the interrupted step (keep None for the current step)
    """
    if not __current_step:
        return

    step_idx = -1 if step_name is None else get_step_idx(step_name)
    if step_idx is None:
        return
    __current_step.pop(step_idx).interrupt(reason)
    while cascade and abs(step_idx) < len(__current_step):
        step = __current_step.pop(step_idx)
        step.interrupt(f"Step {step.name} was interrupted")


def end_step(step_name: str = None):
    if not __current_step:
        return
    if step_name is None:
        __current_step.pop().end()
        return
    step = get_step(step_name)
    step and step.end()


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
