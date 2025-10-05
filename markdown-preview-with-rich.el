;;; markdown-preview-with-rich.el --- Preview Markdown using rich library -*- lexical-binding: t; -*-

;; Copyright (C) 2024 Chris Lee

;; Author: Chris Lee <your-email@example.com>
;; Maintainer: Chris Lee <your-email@example.com>
;; Version: 0.1.0
;; Package-Requires: ((emacs "25.1"))
;; Keywords: markdown, preview, rich, terminal
;; URL: https://github.com/your-username/markdown2rich

;; This file is not part of GNU Emacs.

;; This program is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.

;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with this program.  If not, see <https://www.gnu.org/licenses/>.

;;; Commentary:

;; This package provides a function to preview Markdown files using Python's
;; rich library for beautiful terminal formatting.  It requires the markdown2rich
;; CLI tool to be installed (available via pip or pipx).
;;
;; Usage:
;;   M-x markdown-preview-with-rich
;;   or C-c r in markdown-mode
;;
;; The preview will be displayed in a new buffer with rich formatting including
;; syntax highlighting, tables, lists, and other Markdown elements.

;;; Code:

(require 'ansi-color)

(defgroup markdown-preview-rich nil
  "Preview Markdown using rich library."
  :group 'markdown
  :prefix "markdown-preview-rich-")

(defcustom markdown-preview-rich-command "markdown2rich"
  "Command to use for rendering Markdown with rich.
Can be:
- \"markdown2rich\" (if installed via pip/pipx)
- \"uvx --from git+https://github.com/cleemesser/markdown2rich.git markdown2rich\"
- \"uvx markdown2rich\" (if available in PyPI)
- Custom command string"
  :type '(choice
          (const :tag "Local installation (pip/pipx)" "markdown2rich")
          (const :tag "uvx from GitHub" "uvx --from git+https://github.com/cleemesser/markdown2rich.git markdown2rich")
          (const :tag "uvx from PyPI" "uvx markdown2rich")
          (string :tag "Custom command"))
  :group 'markdown-preview-rich)

(defcustom markdown-preview-rich-buffer-name "*Rich Markdown Preview*"
  "Name of the buffer to display rich markdown preview."
  :type 'string
  :group 'markdown-preview-rich)

(defcustom markdown-preview-rich-display-action 'switch-to-buffer
  "How to display the preview buffer.
Can be 'switch-to-buffer, 'pop-to-buffer, or 'display-buffer."
  :type '(choice (const :tag "Switch to buffer" switch-to-buffer)
                 (const :tag "Pop to buffer" pop-to-buffer)
                 (const :tag "Display buffer" display-buffer))
  :group 'markdown-preview-rich)

(defcustom markdown-preview-rich-keybinding "C-c r"
  "Key binding for markdown-preview-with-rich in markdown-mode."
  :type 'string
  :group 'markdown-preview-rich)

(defun markdown-preview-rich--check-command ()
  "Check if the markdown2rich command is available."
  (let* ((cmd-parts (split-string markdown-preview-rich-command))
         (base-cmd (car cmd-parts)))
    (unless (executable-find base-cmd)
      (cond
       ((string= base-cmd "markdown2rich")
        (error "Command 'markdown2rich' not found. Install via: pip install markdown2rich or pipx install git+https://github.com/cleemesser/markdown2rich.git"))
       ((string= base-cmd "uvx")
        (error "Command 'uvx' not found. Please install uv: pip install uv"))
       (t
        (error "Command '%s' not found. Please check your markdown-preview-rich-command setting" base-cmd))))))

;;;###autoload
(defun markdown-preview-with-rich ()
  "Preview current Markdown buffer using rich.markdown."
  (interactive)
  (markdown-preview-rich--check-command)
  (let* ((buffer-content (buffer-substring-no-properties (point-min) (point-max)))
         (output-buffer (get-buffer-create markdown-preview-rich-buffer-name))
         (tmpfile (make-temp-file "richmarkdown" nil ".md" buffer-content)))
    (unwind-protect
        (let ((command-output (shell-command-to-string
                               (format "%s %s"
                                       markdown-preview-rich-command
                                       (shell-quote-argument tmpfile)))))
          (with-current-buffer output-buffer
            (let ((inhibit-read-only t))
              (erase-buffer)
              (insert command-output)
              (ansi-color-apply-on-region (point-min) (point-max))
              (goto-char (point-min))
              (setq-local buffer-read-only t)
              (setq-local revert-buffer-function
                          (lambda (&optional _ignore-auto _noconfirm)
                            (markdown-preview-with-rich)))))
          (funcall markdown-preview-rich-display-action output-buffer))
      (when (file-exists-p tmpfile)
        (delete-file tmpfile)))))

;;;###autoload
(defun markdown-preview-rich-setup-keybinding ()
  "Set up the key binding for markdown-preview-with-rich in markdown-mode."
  (when (and (boundp 'markdown-mode-map) markdown-mode-map)
    (define-key markdown-mode-map
                (kbd markdown-preview-rich-keybinding)
                'markdown-preview-with-rich)))

;; Set up key binding when markdown-mode is loaded
(with-eval-after-load 'markdown-mode
  (markdown-preview-rich-setup-keybinding))

;; Also set up for users who load this package before markdown-mode
(add-hook 'markdown-mode-hook #'markdown-preview-rich-setup-keybinding)

(provide 'markdown-preview-with-rich)

;;; markdown-preview-with-rich.el ends here
