# Agent instructions for cad-skills

These instructions apply when you use or develop the skills in this repository.

## Language: ASD-STE100 Simplified Technical English (STE)

Use ASD-STE100 Simplified Technical English (STE) for all text that you write:

- Documentation (`SKILL.md`, `references/*.md`, `README.md`).
- Code comments, docstrings, CLI help text, log messages and error messages.
- Commit messages and pull request descriptions.
- Messages to the user, reports and summaries.

STE makes text clear for readers whose first language is not English, and for machine translation. The standard is ASD-STE100 (current issue). The rules below are a summary. If you are not sure about a rule, use the shorter and more direct sentence.

### Words

1. Use only approved STE words with their approved meaning. Use each word with one meaning only. For example, use "right" for the direction, not for "correct".
2. You can use technical names (part names, materials, software, file names, units) and technical verbs (for example "mesh", "slice", "export", "extrude").
3. Use the same term for the same thing everywhere. Do not use synonyms to vary the text.
4. Do not use phrasal verbs when an approved verb exists. Write "remove", not "take out". Write "examine", not "look into".
5. Do not make noun clusters of more than three words. Write "the speed of the outer perimeter", not "outer perimeter print speed setting".
6. Use the articles "the", "a" and "an", and the demonstratives "this" and "these", where possible.
7. Do not use slang, idioms, jargon or abbreviations that are not technical names. Write each abbreviation in full the first time.

### Verbs and sentences

1. Use the active voice. Write "The script calculates the safety factor", not "The safety factor is calculated".
2. Use the imperative (command) form for instructions: "Measure the wall thickness."
3. Use only these tenses: simple present, simple past and simple future. Use the past participle only as an adjective ("the oriented model").
4. Do not use the "-ing" form of a verb, except in a technical name ("infill", "input shaping").
5. Keep one topic in each sentence. Write one instruction in each sentence, unless you must do two actions at the same time.
6. Maximum sentence length: 20 words in procedures, 25 words in descriptions.
7. Maximum paragraph length: six sentences. Start each paragraph with a topic sentence.
8. Use "if" for a condition and "when" for a time.

### Procedures, warnings and cautions

1. Write procedures as numbered steps in the sequence that the user does them.
2. Use vertical lists for complex conditions or for more than three items.
3. A warning (risk of injury) or a caution (risk of damage) starts with a clear command. Then give the reason. Example: "Do not start the print before you clear the bed. The nozzle can hit loose parts."
4. Put the warning or caution before the step to which it applies.

### Code

1. Write comments and docstrings in STE. Say what the code does and why, in short sentences.
2. Write CLI help text and error messages in STE. An error message tells the user the problem and the action to do.
3. Use approved words for identifiers where this is practical (`wall_thickness`, not `wt`). Keep the technical names of libraries and APIs as they are.
4. Do not change the text of code, commands, file names, setting keys or quoted output to STE. Copy them exactly.

### Examples

| Not STE | STE |
|---|---|
| It's recommended that the part be oriented so that layers aren't loaded in tension. | Orient the part so that the load does not pull the layers apart. |
| Once you've got the mesh looking good, go ahead and kick off the solve. | Examine the mesh. Then start the solver. |
| Bumping perimeters is typically the biggest lever for strength. | More perimeters give the largest increase in strength. |
| The file gets uploaded and printing starts automatically. | PrusaLink receives the file and starts the print. |

## Repository conventions

- Run all Python with `uv` (PEP 723 script headers). Do not use `pip install` into a system Python.
- Run the tests before you commit:
  - `uv run tests/test_snippets.py` (every Python block in the skill documents)
  - `uv run tests/test_print_tools.py` (FEA, printability and PrusaSlicer tools)
- Each skill must work alone. Do not make one skill depend on a file in a different skill.
