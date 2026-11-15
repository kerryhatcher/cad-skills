"""A small S-expression reader for KiCad text files. It has no dependency.

`parse(text)` gives nested lists. An atom is a string. A quoted string keeps its text and
is wrapped as `Quoted` so that callers can tell `"R1"` from `R1` when they need to.
"""

from __future__ import annotations


class Quoted(str):
    """A string that came from a quoted token."""


def parse(text: str):
    tokens, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            tokens.append(c)
            i += 1
        elif c == '"':
            j, out = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    j += 1
                out.append(text[j])
                j += 1
            tokens.append(Quoted("".join(out)))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()":
                j += 1
            tokens.append(text[i:j])
            i = j
    stack, root = [], []
    current = root
    for token in tokens:
        if token == "(" and not isinstance(token, Quoted):
            new = []
            current.append(new)
            stack.append(current)
            current = new
        elif token == ")" and not isinstance(token, Quoted):
            current = stack.pop()
        else:
            current.append(token)
    if stack:
        raise ValueError("unbalanced parentheses")
    return root[0] if len(root) == 1 else root


def children(node, name):
    """All child lists of `node` whose first item is `name`."""
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def child(node, name):
    found = children(node, name)
    return found[0] if found else None


def find_symbol_text(text: str, name: str) -> str:
    """Return the exact text of the top-level symbol `name` of a symbol library."""
    marker = f'(symbol "{name}"'
    start = text.index(marker)
    depth, i = 0, start
    while True:
        c = text[i]
        if c == '"':
            i += 1
            while text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
