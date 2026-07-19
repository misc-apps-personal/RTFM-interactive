# RTFM-interactive

LLM-powered TUI app that helps the user interactively read the fucking manual. An educational tool for learning a new library from its documentations. 

- section-by-section reading with navigation
- LLM-generated multiple-choice quiz per section (DeepSeek)

## Usage

```
rtfm path/to/manual.md
rtfm https://example.com/docs.md
```

after adding the following to `~/.bashrc`: 
```
alias rtfm='cd ~/Documents/vibecoding/RTFM-interactive && source .venv/bin/activate && python3 app.py'
```

| Key | Action |
| --- | ------ |
| `n` | Next section |
| `z` | Start/exit quiz on current section |
| `a` `b` `c` `d` | Answer quiz question |
| `q` | Quit |

Requires `DEEPSEEK_API_KEY=your_key` in a `.env` file in the project root for quiz generation.