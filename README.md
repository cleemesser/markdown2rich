# markdown2rich

A CLI tool to render Markdown files using Python's [rich](https://github.com/Textualize/rich) library, providing beautiful terminal output with syntax highlighting, tables, and more.

## Features

- Render Markdown files with rich terminal formatting
- Optional LaTeX math rendering: `$E = mc^2$` becomes `E = mc²` (`-tex`)
- Support for tables, code blocks, lists, and other Markdown elements
- Read from files or stdin
- Beautiful syntax highlighting
- Cross-platform compatibility

## Installation

### Using uvx (recommended for one-time use)

```bash
# Run directly from GitHub (latest version)
uvx --from git+https://github.com/cleemesser/markdown2rich.git markdown2rich README.md
```
# Or install and run
```
uv tool install --from git+https://github.com/cleemesser/markdown2rich.git markdown2rich
markdown2rich README.md
```

### Using pipx or uv (recommended for regular use)

```bash
# Or install directly from GitHub
pipx install git+https://github.com/cleemesser/markdown2rich.git
```
will update this to `pipx install markdown2rich` if I decide to upload to pypi


## Usage

### Basic usage

```bash
# Render a markdown file
markdown2rich README.md

# Read from stdin
cat README.md | markdown2rich

# Using redirection
markdown2rich < README.md
```

### Command-line options

```bash
# Show help
markdown2rich --help

# Show version
markdown2rich --version

# Disable forced terminal output (auto-detect terminal capabilities)
markdown2rich --no-force-terminal README.md

# Convert LaTeX math between dollar signs to Unicode
markdown2rich -tex paper.md
```

### LaTeX math (`-tex`)

`rich.markdown` has no notion of math and prints raw LaTeX verbatim.  With
`-tex` (or `--tex`), math spans are converted to Unicode by
[pylatexenc](https://github.com/phfaist/pylatexenc) before the markdown is
parsed:

| Source | Rendered |
| --- | --- |
| `$E = mc^2$` | `E = mc²` |
| `$\alpha_i$` | `αᵢ` |
| `$2^{10}$` | `2¹⁰` |
| `$$\int_0^\infty e^{-x^2}\,dx = \frac{\sqrt{\pi}}{2}$$` | `∫₀^∞e^(-x²) dx = (√(π))/2` |

#### What counts as math

Every `$` is a candidate, but a span is only converted when all of the
following hold.  Anything rejected is left in the output exactly as written.

- **It is not inside code.**  Fenced blocks and inline code spans are skipped
  whole, so `` `$PATH` `` and a `$HOME` inside a ```` ```bash ```` block are
  never touched.
- **It is not escaped.**  A `\$` never opens a span.
- **No whitespace touches the delimiters.**  `$x$` is math; `$ x $` and `$x $`
  are not.  This is what keeps `it costs $5, or $10 total` as prose -- the
  closing candidate is preceded by a space.
- **The body looks like math.**  It must contain a letter, a `\command`, or one
  of `^` `_` `{` `}` -- or else be a complete signed number.  `$n$`, `$x + y$`,
  `$+1$` and `$-0.7$` all qualify.  The `5-` left over from `a range of $5-$10`
  does not, which is what keeps price ranges intact.
- **It stays on the page.**  Inline `$...$` may not cross a line break at all.
  Display `$$...$$` may wrap across lines but never across a blank line, so an
  unclosed `$$` cannot swallow the rest of the document looking for a partner.
  (Jupyter applies the same paragraph rule.)

| Source | Result |
| --- | --- |
| `$n$`, `$x + y$`, `$+1$`, `$-0.7$` | converted |
| `it costs $5, or $10 total` | left alone |
| `a range of $5-$10` | left alone |
| `$100,000 flat` | left alone |
| `set $HOME and $PATH` | left alone |
| `` `$PATH` `` | left alone |

Converted math is backslash-escaped on the way out, because the result is fed
back through the markdown parser -- an `_` or `*` that pylatexenc emitted must
not turn into emphasis.

#### Forcing a literal dollar sign

Write `\$`.  An escaped dollar never opens a span, and markdown renders it as a
plain `$`.  This is the explicit override for anything the heuristics get
wrong, and there is one known case where it is needed: `$HOME/$PATH` -- two
shell variables separated by a non-space character -- satisfies every rule
above and will be converted.  Write `\$HOME/\$PATH`, or put it in backticks.

#### Display math layout

Display math that converts to a single line is rendered as an ordinary
paragraph.  A result of more than one line -- `aligned`, `cases`, `matrix`,
`array` -- is indented into a code block so that rich preserves the column
alignment; markdown would otherwise join the lines and strip the leading spaces
pylatexenc used to line the columns up.

The flag is off by default; math-free documents render exactly as before.

## Examples

### Render a simple markdown file

```bash
echo "# Hello World\n\nThis is **bold** and this is *italic*." | markdown2rich
```

### View documentation with rich formatting

```bash
markdown2rich docs/api.md
```

### Integration with other tools

```bash
# Use with curl to render remote markdown
curl -s https://raw.githubusercontent.com/user/repo/main/README.md | markdown2rich

# Use with find to preview multiple files
find . -name "*.md" -exec echo "=== {} ===" \; -exec markdown2rich {} \;
```

## Integration with Emacs

This repository includes an Emacs package for seamless Markdown preview integration.

### Installing the Emacs Package

#### Option 1: Using use-package with straight.el

```elisp
(use-package markdown-preview-with-rich
  :straight (:host github :repo "cleemesser/markdown2rich" :files ("markdown-preview-with-rich.el"))
  :after markdown-mode
  :custom
  (markdown-preview-rich-command "markdown2rich")
  (markdown-preview-rich-display-action 'pop-to-buffer))
```

#### Option 2: Using use-package with local file

```elisp
(use-package markdown-preview-with-rich
  :load-path "/path/to/rich_markdown_preview/"
  :after markdown-mode
  :custom
  (markdown-preview-rich-command "markdown2rich")
  (markdown-preview-rich-display-action 'pop-to-buffer))
```

#### Option 3: Manual installation

1. Download `markdown-preview-with-rich.el`
2. Add to your Emacs load path:

```elisp
(add-to-list 'load-path "/path/to/rich_markdown_preview/")
(require 'markdown-preview-with-rich)
```

### Usage in Emacs

- **Command**: `M-x markdown-preview-with-rich`
- **Keybinding**: `C-c r` (in markdown-mode)
- **LaTeX math**: set `markdown-preview-rich-tex` to `t`, or hit `C-u C-c r` to
  toggle math rendering for a single preview
- **Customization**: `M-x customize-group RET markdown-preview-rich RET`

### Customization Options

- `markdown-preview-rich-command`: Command to use. Options include:
  - `"markdown2rich"` (default - for pip/pipx installations)
  - `"uvx -q --from git+https://github.com/cleemesser/markdown2rich.git markdown2rich"` (uvx from GitHub)
  - `"uvx markdown2rich"` (uvx from PyPI)
  - Custom command string
- `markdown-preview-rich-buffer-name`: Preview buffer name
- `markdown-preview-rich-display-action`: How to display the preview buffer
- `markdown-preview-rich-tex`: When non-nil, pass `-tex` to render LaTeX math
- `markdown-preview-rich-keybinding`: Key binding for the preview function

#### Example Configuration for uvx
If you have uvx installed, this is the easiest way to get started inside emacs 30+:
```elisp
(use-package markdown-preview-with-rich
  :vc (:url "https://github.com/cleemesser/markdown2rich.git" :rev :newest)
  :after markdown-mode
  :custom
  (markdown-preview-rich-command "uvx -q --from git+https://github.com/cleemesser/markdown2rich.git markdown2rich")
  ;; (markdown-preview-rich-command "markdown2rich")
  (markdown-preview-rich-display-action 'pop-to-buffer))
```

```elisp
(use-package markdown-preview-with-rich
  :straight (:host github :repo "cleemesser/markdown2rich" :files ("markdown-preview-with-rich.el"))
  :after markdown-mode
  :custom
  (markdown-preview-rich-command "uvx -q --from git+https://github.com/cleemesser/markdown2rich.git markdown2rich")
  (markdown-preview-rich-display-action 'pop-to-buffer))
```

### Prerequisites

1. Install the Python CLI tool: `pipx install markdown2rich`
2. Install `markdown-mode` for Emacs

## Development

### Local installation

```bash
# Clone the repository
git clone <repository-url>
cd markdown2rich

# Install in development mode
pip install -e .

# Or use pipx for isolated environment
pipx install -e .
```

### Running tests

```bash
pip install -e ".[dev]"
pytest
```

### Code formatting

```bash
black markdown2rich/
flake8 markdown2rich/
mypy markdown2rich/
```

## Requirements

- Python 3.8+
- rich >= 10.0.0
- pylatexenc >= 3.0b2 (the 3.0 beta; used for the `-tex` math conversion)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
