from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    scheduled_time: Optional[datetime] = None

    # Methods: set_scheduled_time, get_details

@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    # Methods: add_task, get_tasks

class Owner:
    def __init__(self, name: str, preferences: Dict):
        self.name = name
        self.pets: List[Pet] = []
        self.preferences = preferences

    # Methods: add_pet, get_pets

class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: List[Task] = []

    # Methods: generate_schedule, explain_plan