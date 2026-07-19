# RTFM-interactive

LLM-powered TUI app that helps the user interactively read the fucking manual. An educational tool for learning a new library from its documentations. 

- multiple choice quiz
- step-by-step mode displays one section of a page at a time.

## Usage

```
rtfm path/to/manual.md
rtfm https://example.com/docs.md
```

after adding the following to `~/.bashrc`: 
```
alias rtfm='cd ~/Documents/vibecoding/RTFM-interactive && source .venv/bin/activate && python3 app.py'
```

Keys: `n` next section, `q` quit.