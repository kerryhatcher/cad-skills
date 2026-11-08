# Agent instructions for cad-skills

These instructions apply when you use or change the skills in this repository.

## Language: ASD-STE100 Simplified Technical English (STE)

Use ASD-STE100 Simplified Technical English (STE), Issue 9, for all text that you write:

- Documentation (`SKILL.md`, `references/*.md`, `README.md`).
- Code comments, docstrings, CLI help text, log messages and error messages.
- Commit messages and pull request descriptions.
- Messages to the user, reports and summaries of the work.

STE makes text clear for readers who do not speak English as their first language. It also helps machine translation. The rules below are a summary of the writing rules in Part 1 of the standard. The rule numbers refer to Issue 9. If you are not sure about a rule, use the shorter and more simple sentence.

### Words (Section 1, Section 9)

1. Use only approved words from the STE dictionary, with their approved meaning and part of speech (Rules 1.1 to 1.4).
2. A word that is not in the dictionary is not approved. The exceptions are technical nouns and technical verbs.
3. You can use technical nouns and technical verbs of this subject field (Rules 1.5 to 1.13). Examples:
   - Technical nouns: part names, materials, software names, file names, units, "mesh", "fillet", "infill", "overhang", "stress".
   - Technical verbs (computer processes and manufacturing processes): "run", "export", "install", "slice", "extrude".
4. Do not use a technical noun as a verb (Rule 1.7). Do not use a technical verb as a noun (Rule 1.13).
5. Use the same term for the same item in all text (Rules 1.11 and 9.4). Do not use synonyms to make the text more interesting.
6. Do not use phrasal verbs (Rule 9.3). Write "remove", not "take out". Write "examine", not "look into".
7. Use American English spelling (Rule 1.14): "color", "center", "behavior", "modeling", "millimeter".
8. Do not use Latin abbreviations such as "e.g.", "i.e.", "etc." or "via" (GR-6). Write "for example", "that is", "and other", "through".

Frequent replacements:

| Not approved | Use |
|---|---|
| check (v), verify, ensure | make sure, examine, measure, do a check |
| need, require | necessary ("It is necessary to ...") |
| provide | give, supply |
| may | can, possibly |
| fix (v) | repair, correct, attach |
| avoid | prevent, do not ... |
| allow | let |
| choose, pick | select |
| create | make |
| every | each, all |
| size | dimension |
| inside | in, into, inner |
| instead | (rewrite the sentence) |
| wrong | incorrect |
| real, actual | (rewrite, or use "measured") |
| often | frequently |
| like (as an example) | for example, such as |
| so (result) | thus, as a result |

### Noun clusters (Section 2)

1. Do not write a multi-word noun of more than three words (Rule 2.1). Write "the speed of the outer perimeter", not "outer perimeter print speed setting".
2. If a technical name has more than three words, write it in full one time. Then use a shorter form (Rule 2.2).

### Verbs (Section 3)

1. Use only these verb forms (Rules 3.1 to 3.3):
   - The infinitive and the imperative.
   - The simple present, simple past and simple future tenses.
   - The past participle, only as an adjective.
2. Do not use complex verb constructions with auxiliary verbs (Rule 3.4). Examples: "has been made", "will have been sliced".
3. Use the "-ing" form only in a technical noun, or as a modifier in a technical noun (Rule 3.5). Example: "input shaping".
4. Use the active voice (Rule 3.6). Write "The script calculates the safety factor", not "The safety factor is calculated". In descriptive text, you can use the passive voice only when you do not know the agent.
5. Use a verb, not a noun, for an action (Rule 3.7). Write "Examine the mesh", not "Do an examination of the mesh".

### Sentences (Section 4)

1. Write short and clear sentences (Rule 4.1).
2. Do not make sentences shorter with contractions or missing words (Rule 4.2). Write "do not", not "don't".
3. Use a vertical list for complex text (Rule 4.3).
4. Use connecting words to connect related sentences (Rule 4.4): "then", "thus", "but", "if", "when".
5. Use an article ("the", "a", "an") or "this" or "these" before a noun where possible (Rule 4.5).

### Procedures (Section 5)

1. Use a maximum of 20 words in each sentence (Rule 5.1).
2. Write one instruction in each sentence, unless the actions occur at the same time (Rule 5.2).
3. Use the imperative (command) form (Rule 5.3): "Measure the wall thickness."
4. If the reader must know a condition first, start with the condition. Then put a comma before the command (Rule 5.4): "If the mesh is not watertight, repair it."
5. Use a note only to give information, not an instruction (Rule 5.5).

### Descriptive text (Section 6)

1. Give information gradually, one topic in each sentence (Rule 6.1).
2. Use a maximum of 25 words in each sentence (Rule 6.3).
3. Use paragraphs with only one topic and no more than six sentences (Rules 6.4 to 6.6).

### Safety instructions (Section 7)

1. Use "WARNING" for a risk of injury and "CAUTION" for a risk of damage (Rule 7.1).
2. Start with a clear command or condition (Rule 7.2). Then give the risk or the possible result (Rule 7.3). Example: "CAUTION: Do not start the print before you clear the bed. The nozzle can hit loose parts."
3. Put the safety instruction before the step to which it applies.

### Punctuation and word count (Section 8)

1. Do not use semicolons (Rule 8.1).
2. Use hyphens to connect words that are directly related (Rule 8.2): "heat-set insert".
3. Text in parentheses counts as one word (Rule 8.5).
4. Each of these counts as one word (Rule 8.6): a number with its unit, an abbreviation, an identifier, a code span, a title.

### Code

1. Write comments and docstrings in STE. Say what the code does and why, in short sentences.
2. Write CLI help text and error messages in STE. An error message tells the user the problem and the action to do.
3. Use clear words for identifiers when possible (`wall_thickness`, not `wt`). Keep the names of libraries and APIs as they are.
4. Do not change code, commands, file names, configuration keys, API names or quoted output to STE. Copy them without changes. In Markdown, put them in code spans.

### Examples

| Not STE | STE |
|---|---|
| It's recommended that the part be oriented so that layers aren't loaded in tension. | Turn the part so that the load does not pull the layers apart. |
| Once you've got the mesh looking good, go ahead and kick off the solve. | Examine the mesh. Then start the solver. |
| Bumping perimeters is typically the biggest lever for strength. | More perimeters give the largest increase in strength. |
| The file gets uploaded and printing starts automatically. | PrusaLink receives the file and starts the print. |

### Glossary and check tools

- `ste-glossary.yaml` lists the technical nouns and technical verbs of this repository (Rules 1.5 to 1.13). Use these terms with one meaning each. Add a new term to the glossary before you use it in the documentation.
- These open-source tools find STE problems. They are not ASD-certified. Use them to find problems, then examine each finding yourself:
  - [asd-ste100-checker](https://github.com/EmilioGambaSDB/asd-ste100-checker): dictionary words, part of speech, noun clusters, verb forms. It reads plain text, so first remove code blocks from the Markdown. Run `uvx --from git+https://github.com/EmilioGambaSDB/asd-ste100-checker ste100 check --glossary ste-glossary.yaml --text-type description FILE.txt`.
  - [ste-lint.py](https://github.com/danyuchn/asd-ste100-skill/blob/master/scripts/ste-lint.py): Markdown structure checks (sentence length, semicolons, passive voice, phrasal verbs, synonyms). Run `python3 ste-lint.py FILE.md`.
  - [ste-cli](https://github.com/TudorAndrei/ste-cli): a Markdown linter. You can import the dictionary from your own copy of the ASD-STE100 PDF.
- The tools give false findings. Examples: a past participle used as an adjective ("the part is flipped"), product names ("PrusaLink"), and technical nouns that are not in the glossary.

## Repository conventions

- Run all Python with `uv` (PEP 723 script headers). Do not use `pip install` into a system Python.
- Run the tests before you commit:
  - `uv run tests/test_snippets.py` (all Python blocks in the skill documents)
  - `uv run tests/test_print_tools.py` (FEA, printability and PrusaSlicer tools)
- Each skill must operate alone. A skill must not use a file from a different skill.
