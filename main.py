from pawpal_system import Owner, Pet, Task, Scheduler
from datetime import datetime, timedelta

# Create Owner
owner = Owner(name="Jordan", preferences={})

# Create Pets
pet1 = Pet(name="Mochi", species="dog")
pet2 = Pet(name="Whiskers", species="cat")
owner.add_pet(pet1)
owner.add_pet(pet2)

# Create Tasks
now = datetime.now().replace(second=0, microsecond=0)
task1 = Task(title="Morning walk", duration_minutes=30, priority="high", required_by=now + timedelta(hours=1))
task2 = Task(title="Feeding", duration_minutes=10, priority="medium", required_by=now + timedelta(hours=2))
task3 = Task(title="Vet appointment", duration_minutes=45, priority="high", required_by=now + timedelta(hours=3), fixed=True)

# Assign tasks to pets
pet1.add_task(task1)
pet1.add_task(task3)
pet2.add_task(task2)

# Create Scheduler and generate schedule
scheduler = Scheduler(owner)
schedule = scheduler.generate_schedule({"start_time": now.strftime("%H:%M"), "end_time": (now + timedelta(hours=8)).strftime("%H:%M")})

# Print Today's Schedule
print("Today's Schedule:")
for task in scheduler.get_view():
    pet = scheduler._pet_of.get(id(task))
    time_str = task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "?"
    print(f"{time_str} - {task.title} ({pet.name if pet else 'Unknown Pet'}) [{task.priority}]")

# Optionally, print explanation
print("\n" + scheduler.explain_plan())
