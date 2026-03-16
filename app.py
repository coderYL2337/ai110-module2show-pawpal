import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
from datetime import datetime, timedelta

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")
owner_name = st.text_input("Owner name", value="Jordan")
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, preferences={})

st.markdown("### Add Pet")
pet_name = st.text_input("Pet name", value="")
species = st.selectbox("Species", ["dog", "cat", "other"])
if st.button("Add pet") and pet_name:
    st.session_state.owner.add_pet(Pet(name=pet_name, species=species))

pet_names = [pet.name for pet in st.session_state.owner.pets]
if pet_names:
    st.write("Current pets:")
    st.table([{"Name": pet.name, "Species": pet.species, "Tasks": len(pet.tasks)} for pet in st.session_state.owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.subheader("Add Task")

task_title = st.text_input("Task title", value="")
duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
pet_for_task = st.selectbox("Assign to pet", pet_names) if pet_names else None
specify_start_time = st.checkbox("Specify start time?")
start_time = st.time_input("Start time") if specify_start_time else None
recurrence = st.selectbox("Recurrence", ["one-off", "daily", "weekly", "occasional"], index=0)

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if st.button("Add task") and task_title and pet_for_task:
    # Check for overlapping tasks for the same pet
    overlap = False
    for t in st.session_state.tasks:
        if t["pet_name"] == pet_for_task and start_time and t["start_time"]:
            # Both tasks have a start time
            t_start = t["start_time"]
            t_end = (datetime.combine(datetime.today(), t_start) + timedelta(minutes=t["duration_minutes"])).time()
            new_end = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=duration)).time()
            # Overlap if times intersect
            if (start_time < t_end and t_start < new_end):
                overlap = True
                break
    if overlap:
        st.warning(f"Task '{task_title}' for pet '{pet_for_task}' overlaps with another task at {start_time.strftime('%H:%M')}. Please choose a different time.")
    else:
        st.session_state.tasks.append(
            {
                "title": task_title,
                "duration_minutes": int(duration),
                "priority": priority,
                "pet_name": pet_for_task,
                "start_time": start_time,
                "recurrence": recurrence
            }
        )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")


sort_by = st.selectbox("Sort by", ["time", "priority", "pet", "status"], index=0)
view_mode = st.selectbox("View mode", ["all", "pending", "completed", "skipped"], index=0)
species_filter = st.selectbox("Filter species", ["all"] + [pet.species for pet in st.session_state.owner.pets], index=0)
pet_name_filter = st.selectbox("Filter by pet name", ["all"] + [pet.name for pet in st.session_state.owner.pets], index=0)

st.session_state.owner.preferences = {
    "sort_by": sort_by,
    "view_mode": view_mode,
    "filter_species": None if species_filter == "all" else species_filter,
    "filter_pet_name": None if pet_name_filter == "all" else pet_name_filter
}

if st.button("Generate schedule"):
    if "scheduler" not in st.session_state:
        st.session_state.scheduler = Scheduler(st.session_state.owner)

    # Add tasks to the correct pet
    for t in st.session_state.tasks:
        pet = next((p for p in st.session_state.owner.pets if p.name == t["pet_name"]), None)
        if pet and not any(task.title == t["title"] for task in pet.tasks):
            required_by = datetime.combine(datetime.today(), t["start_time"]) if t["start_time"] else None
            pet.add_task(Task(
                title=t["title"],
                duration_minutes=t["duration_minutes"],
                priority=t["priority"],
                required_by=required_by,
                recurrence=t["recurrence"]
            ))

    schedule = st.session_state.scheduler.generate_schedule({"start_time": "07:00", "end_time": "22:00"})
    conflicts = st.session_state.scheduler.check_schedule()
    if conflicts:
        for a, b in conflicts:
            st.warning(f"Conflict: '{a.title}' overlaps with '{b.title}'")
    else:
        st.success("No conflicts detected!")


    # Filter schedule by pet name if selected
    schedule_view = st.session_state.scheduler.get_view()
    if pet_name_filter != "all":
        schedule_view = [t for t in schedule_view if st.session_state.scheduler._pet_of.get(id(t)) and st.session_state.scheduler._pet_of[id(t)].name == pet_name_filter]

    schedule_data = [
        {
            "Time": t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "?",
            "Task": t.title,
            "Pet": st.session_state.scheduler._pet_of[id(t)].name if st.session_state.scheduler._pet_of.get(id(t)) else "",
            "Priority": t.priority,
            "Status": t.status,
            "Recurrence": t.recurrence
        }
        for t in schedule_view
    ]
    st.table(schedule_data)

    st.markdown("#### Plan explanation")
    st.text(st.session_state.scheduler.explain_plan())

st.divider()

# --- Update Task Status Section ---
st.subheader("Update Task Status")
if "scheduler" in st.session_state and st.session_state.scheduler.schedule:
    st.write("Mark a task as completed or skipped:")
    for i, t in enumerate(st.session_state.scheduler.get_view()):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            pet = st.session_state.scheduler._pet_of.get(id(t))
            pet_label = f" [{pet.name}]" if pet else ""
            st.write(f"{t.title}{pet_label} ({t.scheduled_time.strftime('%H:%M') if t.scheduled_time else '?'}) - {t.status}")
        with col2:
            if st.button(f"Complete {i}"):
                pet = st.session_state.scheduler._pet_of.get(id(t))
                if pet:
                    t.update_status("completed", parent_pet=pet)
                st.rerun()
        with col3:
            if st.button(f"Skip {i}"):
                pet = st.session_state.scheduler._pet_of.get(id(t))
                if pet:
                    t.update_status("skipped", parent_pet=pet)
                st.rerun()
