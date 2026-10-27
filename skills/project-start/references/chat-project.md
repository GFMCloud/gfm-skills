# A chat project (no repo)

For a workspace in a chat app (a Claude Project, a ChatGPT project) rather than a folder of code:
the user brings a rough idea and wants it set up so every chat in it starts with the right context.

## 1. Check it needs a project

It does if the work will take several conversations, needs the same documents again and again, or
goes on for weeks. A single deliverable (one email, one answer) doesn't: say so and offer to do it
now.

## 2. Ask only what is missing

Take what the user already said, and ask at most four questions in one batch, each with your
guess filled in: what "done" or success looks like; who the output is for; what is out of scope or
already decided; how they want the assistant to work with them (push back, or just execute). If
they said "just do it", ask nothing and mark your guesses.

## 3. Write four things

1. **Description** (one to four sentences, ready to paste): what it is, the goal, the main limit.
2. **Instructions** (ready to paste, written to the assistant: "You are...", "When asked..."):
   its role and the kind of work; how to work with the user; tone for each audience; default
   output format; what is in and out of scope and what is already decided; what to do when
   context is missing (ask one focused question, or make a call and flag it); background that
   holds for every chat. Each sentence should change behaviour; cut generic lines.
3. **Files to add:** named kinds of document the user actually has or said they have, not
   "relevant context".
4. **First chats:** two or three specific opening requests.

No brackets or blanks left for the user to fill: write a real value, and list any value you
guessed under "Guesses to check" so the user can correct it. If the session has a working folder,
save the four parts as `<name>-project-setup.md` there and give the path; otherwise reply with
them. Don't create a git repo for a chat project.
