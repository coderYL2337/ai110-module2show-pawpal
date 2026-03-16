import pytest
from pawpal_system import Task, Pet
from datetime import datetime

def test_task_completion():
    task = Task(title="Feed", duration_minutes=10, priority="medium")
    task.update_status("completed")
    assert task.status == "completed"

def test_task_addition():
    pet = Pet(name="Mochi", species="dog")
    initial_count = len(pet.tasks)
    task = Task(title="Walk", duration_minutes=20, priority="high")
    pet.add_task(task)
    assert len(pet.tasks) == initial_count + 1
