# Working with AI agents

## AGENTS.md CLAUDE.md GEMINI.md

- Set up a project level agents file that contains top-level instructions to include in every prompt.
- Every time the agent makes a mistake, add it to the agents file.
- Structure it like this document with headings and subheadings and bullets.
- State everything that you want the agent to do.
- State everything that you DON'T want the agent to do.

## Prompt Strategies
- Give as detailed a prompt as possible. Fully express every single aspect of what you want done. Whatever you don't express, the AI will just guess, and probably wrongly.
- Explicitly state what you DON'T want done. What is out of scope?
- Talk, don't type. You are naturally more expressive with talking, and can express complicated ideas in detail. Typing is slower, and more arduous. You will give less detail when typing, which means the AI has to assume more.
- When you want output in a specific format, show the AI an example.
- Use specific @file references wherever possible.
- Some tasks are faster by hand. If explaining the task takes longer than doing it, just do it.
- After prompting, don't babysit your tasks. Come back in a few minutes if there will be questions in planning, or check in later for a longer running plan. You've done your job, now let the agent do theirs.

## Planning
- Use the best model you have available to plan. Claude Opus, Gemini Pro, etc.
- Always plan before coding. Even a small task requires a small plan to research the necessary files.
- Never go directly to writing code.
- Use a framework like Conductor, GSD, BMad etc. for larger more complicated plans.
- Use Context7 MCP to read the latest docs.
- If the docs aren't in Context7, ask the AI to Google it.
- Read the plan! That's your only job in the beginning.
- Get the plan reviewed by one or two other agents. 
- Feed reviews back to the original planning agent to further refine the plan.

## Skills
- Create a skill for any frequently done task.
- Keep updating the skill until it is done perfectly every time

## Models
- Use the best model you can for planning.
- If the plan is explicit and detailed, you can use a faster model for code execution.


## Prompts
- "Read all relevant files and ask questions until you have a complete understanding of what is required."
- "Find the simplest solution to this issue. Do not over-engineer!"
- "Suggest three ways of solving this problem, and rank them from easiest to most complex. What is your preference?"
- "Show me the plan before writing a single line of code".
- "Let's discuss this first."

## Context Management
- Keep a single session focused on a single task.
- Name your session clearly, so you can easily come back to it later
- If a conversation starts getting long, if the agent starts losing focus and forgetting things, immediately compact, or ask for a summary and start fresh.
- Use compact long before auto-compact kicks in.
- Your most common slash commands should be /rename /clear.

## On Completion
- Ask another agent, another model to review the plan and the changes made.
- Give the review back to your main agent.
- Use a free tool like CodeRabbit to find errors.
- Manually test all code changes, don't "trust that it works".
- Manually testing, and requesting changes is your main job after planning.

## Git Commits
- Commit to GitHub after every logical unit of work.
- Always request approval for commits, no auto-commits.
- Create a commit skill with the message style and layout of your commit messages.

## When things go wrong
- When things get broken, or stuck in a loop, cut your losses. Just delete all the changes and start fresh
- This means that you always need a meaningful GitHub commit to revert to.
- Ask the agent to update the plan with what they would do differently next time.
- Learn from mistakes: update your agents.md file, update your skills, update your plan, so the agent doesn't make the same mistakes ever again.

## CLI tools
- Claude Code: The industry leader with the best models. Also the most expensive.
- OpenCode: The best open-source CLI, provides the most model flexibility.
- Kilo CLI: A good fork of OpenCode. Good free models.
- Gemini CLI: Slow, heavily rate-limited, but free. Also has a massive context window. Good for long-running background tasks.
- Qwen: Very outdated, but also has a million token context window. Good for simple, long-running background tasks and data-crunching.
