"""Tests for the LaTeX math pre-pass."""

from pathlib import Path

import pytest

from markdown2rich.latex import convert_latex_math
from markdown2rich.cli import render_markdown


@pytest.mark.parametrize(
    "source,expected",
    [
        ("$E = mc^2$", "E = mc²"),
        ("$\\alpha_i$", "αᵢ"),
        ("$2^{10}$", "2¹⁰"),
        ("$n$", "n"),
        ("$x + y$", "x + y"),
        # Signed numerics carry no letters but are still math -- found by
        # tests/latex_and_code.md, where a table of factor loadings is full
        # of them.
        ("$+1$", "+1"),
        ("$-0.7$", "-0.7"),
    ],
)
def test_inline_math_becomes_unicode(source, expected):
    assert convert_latex_math(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "it costs $5, or $10 total",
        "a range of $5-$10",
        "priced $5-$7 each",
        "$100,000 flat",
        "$ 5 $",
    ],
)
def test_currency_is_left_alone(source):
    assert convert_latex_math(source) == source


@pytest.mark.parametrize(
    "source",
    [
        "an escaped \\$x^2\\$ span",
        "a code span `$x^2$` here",
        "a ``$x^2$`` double-backtick span",
        "```bash\nFOO=$(echo $x^2$)\n```\n",
        "~~~\n$x^2$\n~~~\n",
    ],
)
def test_code_and_escapes_pass_through(source):
    assert convert_latex_math(source) == source


def test_display_math():
    out = convert_latex_math("$$\\int_0^\\infty e^{-x^2}\\,dx$$")
    assert "∫₀" in out
    assert "$" not in out


def test_multiline_display_math_is_indented_to_keep_its_alignment():
    # An indented code block is the only layout rich preserves column
    # alignment in; a plain paragraph would join the lines.
    out = convert_latex_math("$$\\begin{aligned} a &= b \\\\ c &= d \\end{aligned}$$")
    lines = out.splitlines()
    assert len(lines) == 2
    assert all(line.startswith("    ") for line in lines)


def test_single_line_display_math_is_not_indented():
    out = convert_latex_math("$$x^2$$")
    assert out == "x²"


def test_converted_math_does_not_become_emphasis():
    # The pre-pass output is re-parsed as markdown, so an underscore pylatexenc
    # emitted must not turn into an <em>.
    out = convert_latex_math("$\\mathrm{a\\_b}$ and $\\mathrm{c\\_d}$")
    assert "\\_" in out


def test_render_markdown_leaves_latex_alone_without_the_flag():
    assert "mc^2" in render_markdown("$E = mc^2$", force_terminal=False)


def test_render_markdown_converts_with_the_flag():
    out = render_markdown("$E = mc^2$", force_terminal=False, tex=True)
    assert "mc²" in out
    assert "mc^2" not in out


def test_display_math_does_not_cross_a_paragraph_break():
    # An unclosed "$$" must not hunt through the rest of the document for a
    # partner and convert everything in between.  Same rule as Jupyter.
    source = "$$x^2\n\nprose with a stray $ here\n\nmore $$ text"
    assert convert_latex_math(source) == source


def test_display_math_may_still_wrap_across_lines():
    out = convert_latex_math("$$\\int_0^1 f(x)\\,dx\n= \\frac{1}{2}$$")
    assert "∫₀¹" in out
    assert "$" not in out


def test_inline_math_cannot_escape_its_line():
    # A trailing backslash must not act as a bridge to the next line.
    source = "$a \\\n b$ stays put"
    assert convert_latex_math(source) == source


@pytest.mark.parametrize(
    "source",
    [
        # An escaped dollar never opens a span, so this is the explicit way to
        # write currency that the heuristics would otherwise have to guess at.
        "it costs \\$5 and \\$10",
        "\\$x^2\\$ stays literal",
        "a \\$\\$not display\\$\\$ span",
    ],
)
def test_escaped_dollars_suppress_math(source):
    assert convert_latex_math(source) == source


def test_escaping_one_dollar_does_not_disable_the_rest():
    assert convert_latex_math("\\$5 and $n$ is math") == "\\$5 and n is math"


def test_sample_document_converts_cleanly():
    """Smoke test over tests/data/latex_and_code.md, a real math-heavy document."""
    source = (Path(__file__).parent / "data" / "latex_and_code.md").read_text(encoding="utf-8")
    out = convert_latex_math(source)

    # Every math span was recognised; no raw delimiters left behind.
    assert "$" not in out

    # The python block -- full of underscores that look like subscripts --
    # comes through byte for byte.
    fence = source[source.index("```python") : source.index("```\n\nThis gives")]
    assert fence in out

    # Spot-check a few conversions across tables, prose and display math.
    assert "∑ᵣ₌₁ᴿ" in out
    assert "nᵥₐᵣₛ" in out
    assert "cₓ≫" in out
