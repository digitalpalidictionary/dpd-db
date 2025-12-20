# Rules to follow.

## Security
- DO NOT modify:
  - .env files
  - .ini files

## File Reading
- You never need permission to read a file or analyze file.

## Custom instructions
- Promise to follow the custom instructions.

## Python Type Hints
- Please add type hints to all code, especially when it is missing in existing code. 
- Use modern type hints not old type hints
  - Use `dict[str, str]` not `Dict[str, str]` 
  - Use `tuple[str, str]` not `Tuple[str, str]`
  - Use `list[str]` not `List[str]`
  - Use `| None` not Optional[None]

## Use Path from Pathlib
- Use Path for anything related to filepaths, not os.

## Comments
- Do not add comments unnecessarily. 
- Only add comments when truly necessary to explain WHY something is being done. Never WHAT is being done. 
- Leave existing comments as they are.

## Dependencies

### uv
- Use astral uv to manage dependencies.
- Install with "uv add" not "pip install" or "uv pip install" etc.
- DO NOT run any scripts with uv UNLESS specifically asked to do so. 

## Plan Mode
- When starting to plan, show that you've understood the question by saying "Hmmm...". If not, ask more questions to clarify.
- Analyze all code files thoroughly.
- Get the full context before suggesting a solution.
- Show an implementation plan with relevant code snippets.
- List all assumptions and uncertainties you need to clear up before writing code.
- Give a confidence rating. On a scale of 1 to 10, how confident are you in this solution?
- Think. Is this an elegant solution to this problem? Is the code easy to read? Is the code maintainable? Does the code integrate well with other parts of the project.

## Act Mode
- Always give a summary of code that's changed using snippets, unless otherwise asked.

## Memory Check
- If you understand the prompt fully, respond with 'Hopa!' every time you are about to use a tool.

## Flet
- When answering questions about Flet refer to the /resources/flet-docs folder.

## Tree
- On a weekly basis, or anytime the project tree changes, check that the project tree matches the tree specified in @docs/technical/project_folder_structure.md

## Database model
- On a weekly basis, or anytime the database model changes, check that the database model in @db/models.py matches the docs in @docs/technical/dpd_headwords_table.md

## GitHub
- Unless otherwise specified the repository in question is https://github.com/digitalpalidictionary/dpd-db.
- DO NOT add or commit to GitHub, unless specifically instructed to do so.

### Solve
- "Solve" means read the specified GitHub issue using get_issue and offer solutions. Don't think about it, don't ask questions, just read it.
- Ask the user to open the necessary files that you need.
- Is this a straightforward solution, or does it need to be solved at a higher level?
- Show code snippets of suggested changes.

### Commit
- "Commit" means commit the changed files using execute_command.
- Use this format, all in lowercase. #issue number area: change1, change2 . E.g. #67 webapp: updated css, fixed overflow

# Code Review
- When completed the task, ask the user for permission to run `coderabbit --prompt-only` in the terminal to get a review
- Fix all the suggested issues
- If there are no issues, there's nothing to fix.

## Update Gemini CLI
```bash
npm install -g @google/gemini-cli@latest
```