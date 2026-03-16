from dataclasses import dataclass, field, replace
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str                           # "low" / "medium" / "high"
    status: str = "pending"                 # "pending" / "completed" / "skipped"
    required_by: Optional[datetime] = None  # exact datetime — hard deadline (vet/grooming)
    fixed: bool = False                     # True = cannot be moved (e.g. vet appt)
    recurrence: str = "daily"               # "daily" / "weekly" / "occasional" / "one-off"
    times_per_day: Optional[int] = None             # e.g. 3 for feeding
    preferred_times: Optional[List[datetime]] = None # user-pinned times for each repetition
    requires_active_attention: bool = True           # True = walk/vet; False = feeding
    scheduled_time: Optional[datetime] = None

    def set_scheduled_time(self, time: datetime) -> None:
        self.scheduled_time = time

    def update_status(self, status: str) -> None:
        valid = {"pending", "completed", "skipped"}
        if status not in valid:
            raise ValueError(f"status must be one of {valid}")
        self.status = status

    def get_details(self) -> dict:
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "status": self.status,
            "required_by": (
                self.required_by.strftime("%Y-%m-%d %H:%M") if self.required_by else None
            ),
            "fixed": self.fixed,
            "recurrence": self.recurrence,
            "times_per_day": self.times_per_day,
            "preferred_times": (
                [t.strftime("%Y-%m-%d %H:%M") for t in self.preferred_times]
                if self.preferred_times else None
            ),
            "requires_active_attention": self.requires_active_attention,
            "scheduled_time": (
                self.scheduled_time.strftime("%H:%M") if self.scheduled_time else None
            ),
        }


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        self.tasks.remove(task)

    def get_tasks(self) -> List[Task]:
        return list(self.tasks)


class Owner:
    def __init__(self, name: str, preferences: Dict):
        self.name = name
        self.pets: List[Pet] = []
        self.preferences = preferences

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        self.pets.remove(pet)

    def get_pets(self) -> List[Pet]:
        return list(self.pets)

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across every pet, filtered by owner.preferences.

        Respects:
            filter_species — e.g. "dog" shows only dog tasks; None shows all
            view_mode      — "all" (default) / "pending" / "completed" / "skipped"
        """
        species_filter = self.preferences.get("filter_species")
        view_mode = self.preferences.get("view_mode", "all")

        tasks = []
        for pet in self.pets:
            if species_filter and pet.species != species_filter:
                continue
            for task in pet.get_tasks():
                if view_mode != "all" and task.status != view_mode:
                    continue
                tasks.append(task)
        return tasks


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: List[Task] = []
        self._pet_of: Dict[int, Pet] = {}  # id(task) → Pet, populated by generate_schedule

    # ------------------------------------------------------------------ #
    # Conflict helpers                                                     #
    # ------------------------------------------------------------------ #

    def has_conflict(self, task_a: Task, task_b: Task) -> bool:
        """Return True if task_a and task_b overlap in time AND at least one
        requires active attention (cross-pet conflict rule)."""
        if task_a.scheduled_time is None or task_b.scheduled_time is None:
            return False
        end_a = task_a.scheduled_time + timedelta(minutes=task_a.duration_minutes)
        end_b = task_b.scheduled_time + timedelta(minutes=task_b.duration_minutes)
        overlap = task_a.scheduled_time < end_b and task_b.scheduled_time < end_a
        if not overlap:
            return False
        return task_a.requires_active_attention or task_b.requires_active_attention

    def _times_overlap(self, start: datetime, end: datetime, other: Task) -> bool:
        """Check if a candidate [start, end) window overlaps with a scheduled task."""
        if other.scheduled_time is None:
            return False
        other_end = other.scheduled_time + timedelta(minutes=other.duration_minutes)
        return start < other_end and other.scheduled_time < end

    # ------------------------------------------------------------------ #
    # Core scheduling                                                      #
    # ------------------------------------------------------------------ #

    def _expand_task(self, task: Task, start_dt: datetime, end_dt: datetime) -> List[Task]:
        """Expand a repeated task into N individual copies, one per occurrence.

        - If the user provided preferred_times, each copy is anchored to that time (fixed).
        - Otherwise the scheduler auto-distributes evenly across the day window (also fixed,
          but the user can call set_scheduled_time() on any copy to override afterward).
        Each copy gets a numbered title so the user can tell them apart.
        """
        n = task.times_per_day or 1
        if n <= 1:
            return [task]

        if task.preferred_times and len(task.preferred_times) >= n:
            slots = task.preferred_times[:n]
        else:
            window_minutes = (end_dt - start_dt).total_seconds() / 60
            spacing = window_minutes / n
            slots = [start_dt + timedelta(minutes=spacing * i) for i in range(n)]

        return [
            replace(
                task,
                title=f"{task.title} ({i + 1}/{n})",
                required_by=slot,
                fixed=True,
                scheduled_time=None,
                times_per_day=None,
                preferred_times=None,
            )
            for i, slot in enumerate(slots)
        ]

    def generate_schedule(self, time_constraints: dict) -> List[Task]:
        """Build a conflict-free daily schedule within the given time window.

        time_constraints keys:
            start_time  — "HH:MM", default "07:00"
            end_time    — "HH:MM", default "22:00"
        """
        today = datetime.today().date()
        start_str = time_constraints.get("start_time", "07:00")
        end_str = time_constraints.get("end_time", "22:00")
        start_dt = datetime.combine(today, datetime.strptime(start_str, "%H:%M").time())
        end_dt = datetime.combine(today, datetime.strptime(end_str, "%H:%M").time())

        # Collect pending tasks, expanding repeated ones into individual copies
        self._pet_of = {}
        pet_tasks: List[Tuple[Task, Pet]] = []
        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if task.status != "pending":
                    continue
                for copy in self._expand_task(task, start_dt, end_dt):
                    pet_tasks.append((copy, pet))
                    self._pet_of[id(copy)] = pet

        # Sort: fixed first → high priority first → earliest required_by
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        pet_tasks.sort(
            key=lambda tp: (
                0 if tp[0].fixed else 1,
                priority_rank.get(tp[0].priority, 1),
                tp[0].required_by or datetime.max,
            )
        )

        scheduled: List[Tuple[Task, Pet]] = []
        cursor = start_dt  # rolling pointer for flexible tasks

        for task, pet in pet_tasks:
            # Fixed tasks anchor to required_by datetime; flexible tasks follow the cursor
            if task.fixed and task.required_by:
                slot = task.required_by
            else:
                slot = cursor

            task_end = slot + timedelta(minutes=task.duration_minutes)
            if task_end > end_dt:
                continue  # doesn't fit in today's window

            # Check conflicts with already-scheduled tasks
            conflict = False
            for sched_task, sched_pet in scheduled:
                same_pet = sched_pet.name == pet.name
                if same_pet:
                    # Any time overlap is a conflict for same pet
                    if self._times_overlap(slot, task_end, sched_task):
                        conflict = True
                        break
                else:
                    # Temporarily assign slot to evaluate cross-pet conflict
                    task.set_scheduled_time(slot)
                    if self.has_conflict(task, sched_task):
                        conflict = True
                        task.scheduled_time = None
                        break
                    task.scheduled_time = None

            if not conflict:
                task.set_scheduled_time(slot)
                scheduled.append((task, pet))
                if not task.fixed:
                    cursor = task_end

        self.schedule = [t for t, _ in scheduled]
        return self.schedule

    def check_schedule(self) -> List[Tuple[Task, Task]]:
        """Scan the full schedule and return every conflicting pair of tasks."""
        conflicts: List[Tuple[Task, Task]] = []
        for i, task_a in enumerate(self.schedule):
            for task_b in self.schedule[i + 1:]:
                same_pet = self._pet_of.get(id(task_a)) is self._pet_of.get(id(task_b))
                if same_pet:
                    end_a = task_a.scheduled_time + timedelta(minutes=task_a.duration_minutes)
                    end_b = task_b.scheduled_time + timedelta(minutes=task_b.duration_minutes)
                    if task_a.scheduled_time < end_b and task_b.scheduled_time < end_a:
                        conflicts.append((task_a, task_b))
                else:
                    if self.has_conflict(task_a, task_b):
                        conflicts.append((task_a, task_b))
        return conflicts

    def get_view(self) -> List[Task]:
        """Return the schedule filtered and sorted by owner.preferences.

        Respects:
            filter_species — e.g. "dog" / "cat" / None (all)
            view_mode      — "all" (default) / "pending" / "completed" / "skipped"
            sort_by        — "time" (default) / "priority" / "pet" / "status"
        """
        prefs = self.owner.preferences
        species_filter = prefs.get("filter_species")
        view_mode = prefs.get("view_mode", "all")
        sort_by = prefs.get("sort_by", "time")

        tasks = list(self.schedule)

        if species_filter:
            tasks = [
                t for t in tasks
                if self._pet_of.get(id(t)) and self._pet_of[id(t)].species == species_filter
            ]

        if view_mode != "all":
            tasks = [t for t in tasks if t.status == view_mode]

        priority_rank = {"high": 0, "medium": 1, "low": 2}
        status_rank = {"pending": 0, "completed": 1, "skipped": 2}

        if sort_by == "time":
            tasks.sort(key=lambda t: t.scheduled_time or datetime.max)
        elif sort_by == "priority":
            tasks.sort(key=lambda t: priority_rank.get(t.priority, 1))
        elif sort_by == "pet":
            tasks.sort(key=lambda t: (
                self._pet_of[id(t)].name if self._pet_of.get(id(t)) else ""
            ))
        elif sort_by == "status":
            tasks.sort(key=lambda t: status_rank.get(t.status, 0))

        return tasks

    def explain_plan(self) -> str:
        """Return a human-readable summary of the scheduled day."""
        if not self.schedule:
            return "No tasks have been scheduled yet."

        lines = [f"Daily care plan for {self.owner.name}:\n"]
        for task in sorted(self.schedule, key=lambda t: t.scheduled_time or datetime.min):
            fmt = "%a %b %d %H:%M" if task.fixed else "%H:%M"
            time_str = task.scheduled_time.strftime(fmt) if task.scheduled_time else "?"
            attention = "active" if task.requires_active_attention else "passive"
            lines.append(
                f"  {time_str}  {task.title}"
                f"  ({task.duration_minutes} min | {task.priority} priority | {attention})"
            )

        conflicts = self.check_schedule()
        if conflicts:
            lines.append("\nWarnings:")
            for a, b in conflicts:
                lines.append(f"  ! Conflict: '{a.title}' overlaps with '{b.title}'")

        return "\n".join(lines)
