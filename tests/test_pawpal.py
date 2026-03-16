import pytest
from pawpal_system import Task, Pet, Owner, Scheduler
from datetime import datetime, timedelta

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


def test_sorting_correctness():
    owner = Owner(name="Alex", preferences={"sort_by": "time"})
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    now = datetime.now().replace(second=0, microsecond=0)
    t1 = Task(title="Morning Walk", duration_minutes=30, priority="high", scheduled_time=now)
    t2 = Task(title="Lunch", duration_minutes=15, priority="medium", scheduled_time=now + timedelta(hours=2))
    t3 = Task(title="Evening Play", duration_minutes=20, priority="low", scheduled_time=now + timedelta(hours=4))
    pet.add_task(t1)
    pet.add_task(t2)
    pet.add_task(t3)
    scheduler = Scheduler(owner)
    scheduler.schedule = [t1, t2, t3]
    sorted_tasks = scheduler.get_view()
    times = [t.scheduled_time for t in sorted_tasks]
    assert times == sorted(times)

# --- Recurrence Logic --- #
def test_recurrence_logic():
    owner = Owner(name="Sam", preferences={})
    pet = Pet(name="Luna", species="cat")
    owner.add_pet(pet)
    today = datetime.now().replace(second=0, microsecond=0)
    task = Task(title="Feed", duration_minutes=10, priority="medium", recurrence="daily", required_by=today)
    pet.add_task(task)
    task.update_status("completed", parent_pet=pet)
    tasks_titles = [t.title for t in pet.tasks]
    assert any("Feed" in title for title in tasks_titles)
    assert len(pet.tasks) > 1
    # Check that new task is for the next day
    new_task = [t for t in pet.tasks if t.status == "pending" and t.required_by and t.required_by.date() == (today + timedelta(days=1)).date()]
    assert new_task

# --- Conflict Detection --- #
def test_conflict_detection():
    owner = Owner(name="Jamie", preferences={})
    pet1 = Pet(name="Max", species="dog")
    pet2 = Pet(name="Bella", species="cat")
    owner.add_pet(pet1)
    owner.add_pet(pet2)
    now = datetime.now().replace(second=0, microsecond=0)
    t1 = Task(title="Vet Visit", duration_minutes=30, priority="high", scheduled_time=now, fixed=True)
    t2 = Task(title="Grooming", duration_minutes=30, priority="high", scheduled_time=now, fixed=True)
    pet1.add_task(t1)
    pet2.add_task(t2)
    scheduler = Scheduler(owner)
    scheduler.schedule = [t1, t2]
    scheduler._pet_of = {id(t1): pet1, id(t2): pet2}
    conflicts = scheduler.check_schedule()
    assert conflicts, "Scheduler should flag duplicate times as conflict."

# --- Edge Case: Owner with No Pets --- #
def test_owner_with_no_pets():
    owner = Owner(name="Solo", preferences={})
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule({})
    assert schedule == [], "Schedule should be empty if owner has no pets."

# --- Edge Case: Pet with No Tasks --- #
def test_pet_with_no_tasks():
    owner = Owner(name="Alex", preferences={})
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule({})
    assert schedule == [], "Schedule should be empty if pet has no tasks."

# --- Filtering by Species and Status --- #
def test_filtering_by_species_and_status():
    owner = Owner(name="Pat", preferences={"filter_species": "dog", "view_mode": "pending"})
    dog = Pet(name="Rex", species="dog")
    cat = Pet(name="Whiskers", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    task1 = Task(title="Walk", duration_minutes=20, priority="high", status="pending")
    task2 = Task(title="Feed", duration_minutes=10, priority="medium", status="completed")
    dog.add_task(task1)
    cat.add_task(task2)
    scheduler = Scheduler(owner)
    scheduler.schedule = [task1, task2]
    scheduler._pet_of = {id(task1): dog, id(task2): cat}
    filtered = scheduler.get_view()
    assert len(filtered) == 1
    assert filtered[0].title == "Walk"

# --- Invalid Task Data: Missing required_by, times_per_day --- #
def test_invalid_task_data():
    owner = Owner(name="Chris", preferences={})
    pet = Pet(name="Buddy", species="dog")
    owner.add_pet(pet)
    # Task with missing required_by and times_per_day
    task = Task(title="Play", duration_minutes=15, priority="low")
    pet.add_task(task)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule({})
    assert schedule, "Scheduler should handle tasks with missing required_by and times_per_day."
