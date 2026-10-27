# New build

Read this when step 1 sizes the work as a new build: something that doesn't exist yet. Start
from the finished state and reason back, then forward to a first slice. The plan still uses the
headings in step 3; this file says how to fill them.

## 1. Pin the end state

Write what will be true when it's built, as something a sceptic could check: who uses it, what
they can do, how many, by when, and the evidence ("12 people can book a class place from a phone,
and the owner sees the list" rather than "a booking system"). If the user can't say what done
looks like, don't invent it: ask the one question that would settle it, offer a default, and stop
there. "Not ready to plan yet" is a fair answer.

Name the fixed constraints (budget, people, hosting, rules, a deadline that really can't move) and
anything the user has already decided. If the request is really two or three projects, say so and
plan the smallest one first.

## 2. Work backwards

From the end state, ask what must already be true just before it, and then before that, until you
reach something that could start today. Write each link as a state ("the owner has a list they can
read on their phone"), not an activity ("build the admin page"). Mark which links are on the critical
path and which can run side by side. Where you are assuming people will change what they do,
or that someone else will handle something, say so: that is usually where the plan is weakest.

## 3. Pre-mortem

Imagine it's some months after launch and it failed. Write the three most likely reasons,
specific enough that you could spot each one early ("bookings come in by text message instead,
because the link is buried", not "low adoption"). For each: the early warning sign and what the
plan does about it. If a failure can't be prevented or survived, say so; dropping or pausing the
project is a fair recommendation.

## 4. First slice

Pick the smallest end-to-end piece that proves the core idea works and that someone can try
without further input from the user. It goes first in Steps, with its own done-check. Later slices
are listed after it, each with its check, in the order the backward map says.

If no first slice can be cut like that, the idea is vaguer or bigger than it looks: say so rather
than writing a long plan.

## 5. Choose the build

For each real choice (build or reuse an existing tool, hosted or self-run, which store for data),
pick the boring option that meets the end state, and put the others under Rejected with a short reason
each. Prefer what the user already has and runs. Look for an existing tool before planning to
write one, and say what you looked at.

## Output

The plan from step 3 of the skill, with:
- Goal: the end state from section 1.
- Assumptions: the weak links from section 2, marked `checked` or `unchecked`.
- Risk: the pre-mortem from section 3.
- Steps: the first slice, then the later slices.
- a short "Decisions the user needs to make" list if any choice is really theirs (taste, money,
  people), each with your default.

Don't create the repository or write code in the planning turn. Once the plan is agreed, a new
repository's skeleton is the project-start skill's job.
