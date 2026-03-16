classDiagram
    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : has
    Scheduler --> Owner : uses

    class Owner {
        + name: str
        + pets: List<Pet>
        + preferences: dict
        + add_pet(pet: Pet)
        + get_pets() List<Pet>
    }
    class Pet {
        + name: str
        + species: str
        + tasks: List<Task>
        + add_task(task: Task)
        + get_tasks() List<Task>
    }
    class Task {
        + title: str
        + duration_minutes: int
        + priority: str
        + scheduled_time: Optional[datetime]
        + set_scheduled_time(time: datetime)
        + get_details() dict
    }
    class Scheduler {
        + owner: Owner
        + schedule: List<Task>
        + generate_schedule(time_constraints: dict) List<Task>
        + explain_plan() str
    }
