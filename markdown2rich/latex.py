#!/usr/bin/env python3
"""LaTeX math interception for markdown2rich.

Markdown documents that carry math write it between dollar signs: ``$...$`` for
inline math and ``$$...$$`` for display math.  ``rich.markdown`` has no notion
of math, so it prints the raw LaTeX verbatim.  This module runs as a pre-pass
over the raw source *before* it reaches rich's markdown parser, replacing each
math span with the Unicode approximation produced by :mod:`pylatexenc`.

Two things make this more than a regex substitution:

* A ``$`` inside a code span or fenced code block is not math (``$PATH``), so
  code regions are matched first and passed through untouched.
* A ``$`` in prose is usually currency.  ``_is_math`` is the gate that decides
  which candidate spans are real math; see its docstring for the trade-off.
"""

import re

#: Regions of the document we care about, in priority order.  Code regions come
#: first so that their contents can be skipped wholesale; ``escaped`` keeps a
#: literal ``\$`` from opening a span.
#: Deliberately compiled without ``re.DOTALL``: ``.`` must stay line-bounded so
#: that the ``\\.`` escape inside ``inline`` cannot swallow a newline and let
#: inline math run off the end of its line.  Patterns that *should* span lines
#: spell it out with ``[\s\S]``.
_SCAN_RE = re.compile(
    r"""
      (?P<fence>
          ^[ \t]{0,3}(?P<ticks>`{3,}|~{3,})[^\n]*\n
          [\s\S]*?
          (?:^[ \t]{0,3}(?P=ticks)[ \t]*$|\Z)
      )
    | (?P<code>(?P<backticks>`+)(?:(?!(?P=backticks))[\s\S])+(?P=backticks))
    | (?P<escaped>\\\$)
    | (?P<display>
          \$\$
          # Display math may wrap across lines, but never across a blank line:
          # an unclosed "$$" must not swallow the rest of the document looking
          # for its partner.  A paragraph break ends the search, as in Jupyter.
          (?P<display_body>(?:(?!\n[ \t]*\n)[\s\S])+?)
          \$\$
      )
    | (?P<inline>\$(?![\s$])(?P<inline_body>(?:[^$\\\n]|\\.)+?)(?<!\s)\$)
    """,
    re.VERBOSE | re.MULTILINE,
)

#: A span is math if it contains a letter, a LaTeX command, or sub/superscript
#: and grouping syntax.
_MATH_SIGNAL_RE = re.compile(r"[A-Za-z\\^_{}]")

#: ...or if it is a complete signed number.  ``$+1$`` and ``$-0.7$`` are math
#: even though they carry no letters, whereas the currency case ``$5-$10``
#: leaves the fragment ``5-``, which dangles on an operator.
_NUMBER_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")

#: ASCII punctuation that markdown would otherwise interpret once the converted
#: math is fed back through the parser.  CommonMark lets any ASCII punctuation
#: be backslash-escaped, so escaping these is always safe.
_MD_SPECIAL_RE = re.compile(r"([\\`*_\[\]<>|])")


def _is_math(body: str) -> bool:
    """Decide whether a ``$...$`` candidate is math rather than currency.

    The regex has already applied the usual "no whitespace next to the
    delimiters" rule, which handles ``costs $5, or $10 total``.  It does not
    handle ``range $5-$10``, where the candidate body is ``5-``.

    A letter, backslash, ``^``, ``_`` or brace keeps ``$n$`` and ``$x + y$``
    working.  Bodies with none of those are accepted only when they are a
    complete signed number: ``$+1$`` and ``$-0.7$`` are math, while the
    dangling ``5-`` of a price range is not.
    """
    body = body.strip()
    return bool(_MATH_SIGNAL_RE.search(body) or _NUMBER_RE.fullmatch(body))


def _escape_markdown(text: str) -> str:
    """Neutralize markdown syntax in converted math.

    The pre-pass output is re-parsed by rich's markdown parser, so an ``_`` or
    ``*`` that pylatexenc emitted as part of an expression must not turn into
    emphasis.
    """
    return _MD_SPECIAL_RE.sub(r"\\\1", text)


def _format_display_math(text: str) -> str:
    """Lay out converted display math so markdown does not reflow it.

    A single-line result is safe as its own paragraph and is returned as-is.  A
    multi-line result -- from ``aligned``, ``cases``, ``matrix``, ``array`` --
    is not: markdown reads the newlines as soft breaks, joins the lines, and
    strips the leading spaces pylatexenc used to line the columns up.

    Indenting by four spaces makes it an indented code block, which is the only
    one of the three plausible layouts that preserves the column alignment
    exactly.  Measured against rich:

        paragraph (no-op)       "a    = b + c d    = e - f"   alignment lost
        hard breaks (\\ at EOL)  a    = b + c                lines kept, but
                                d    = e - f                  leading spaces
                                                              stripped
        four-space indent       a    = b + c                  alignment exact
                                 d    = e - f                 (chosen)

    The cost is that rich paints the block on a code background.  For an
    ``aligned`` environment the columns are the point, so that is the trade
    worth making.
    """
    if "\n" not in text:
        return text
    return "\n".join("    " + line for line in text.split("\n"))


def convert_latex_math(content: str, math_mode: str = "text") -> str:
    """Replace ``$...$`` and ``$$...$$`` spans with Unicode text.

    ``math_mode`` is passed through to :class:`pylatexenc.latex2text.LatexNodes2Text`;
    the default ``"text"`` drops the dollar delimiters so math reads as prose.
    Content inside code spans and fenced code blocks is left alone.
    """
    # Imported lazily so that importing markdown2rich stays cheap and the rest
    # of the tool keeps working if pylatexenc is unavailable.
    from pylatexenc.latex2text import LatexNodes2Text

    converter = LatexNodes2Text(math_mode=math_mode)

    def convert(latex: str) -> str:
        # pylatexenc only emits Unicode sub/superscripts when it knows it is in
        # math mode, which it infers from the delimiters -- so hand it the whole
        # span, dollars included, rather than just the body.
        return converter.latex_to_text(latex)

    def replace(match: "re.Match") -> str:
        # Code regions and escaped dollars pass through verbatim.
        if any(match.group(g) is not None for g in ("fence", "code", "escaped")):
            return match.group(0)

        if match.group("display") is not None:
            text = convert(match.group("display")).strip()
            if not text:
                return match.group(0)
            return _format_display_math(_escape_markdown(text))

        body = match.group("inline_body")
        if not _is_math(body):
            return match.group(0)
        text = convert(match.group("inline")).strip()
        if not text:
            return match.group(0)
        return _escape_markdown(text)

    return _SCAN_RE.sub(replace, content)
