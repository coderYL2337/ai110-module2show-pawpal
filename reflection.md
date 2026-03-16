# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
     My initial UML design defined four main classes with clear relationships: Owner manages pets, Pet represents each animal and its tasks, Task models care activities, and Scheduler generates daily plans.

- What classes did you include, and what responsibilities did you assign to each?
    I included Owner (manages pet info and preferences), Pet (represents each animal and its tasks), Task (models individual care activities), and Scheduler (generates daily plans and explains reasoning).

- Three core actions a user should be able to perform:
     add a pet, schedule a walk, see today's tasks.

**b. Design changes**

- Did your design change during implementation?
    Yes
    
- If yes, describe at least one change and why you made it.
    Task gained recurrence, status, and required_by — because feeding/walking times are driven by pet needs, not owner preference

    Owner.preferences narrowed to sorting/filtering only — to separate necessity (what must happen) from preference (how to view it)

    Scheduler gained has_conflict() and check_schedule() — because one owner cannot actively perform two tasks at the same time

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    The scheduler considers task time windows, priority levels, pet needs (required_by, recurrence), and avoids conflicts based on active attention. Owner preferences are used only for sorting and filtering the output.

- How did you decide which constraints mattered most?
    Constraints driven by pet necessity (required_by, recurrence, fixed) mattered most, since care tasks must happen at specific times. Priority was used to order flexible tasks, while owner preferences were limited to display.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    The scheduler prioritizes avoiding conflicts (active attention) over strictly following owner preferences for task timing.

- Why is that tradeoff reasonable for this scenario?
    This is reasonable because pet care tasks must be performed without overlap when active attention is required, ensuring pets’ needs are met and the owner can realistically complete all tasks.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
