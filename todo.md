# TODO

- [ ] Should I tell the user to always run any easyjupyer commands or imports from the root, I don't mean run ./nest/i.ipynb from ./i.ipynb, just like have VSC opened in the root of the project, and if in terminal be in home directory for the commands?
- [ ] A better search in notebooks is a must-have, VSC currently struggles with searches in notebooks. Same for the TODO extension.

- [ ] Move from import os to import Pathlib
- [ ] Any other warnings I can give the user, if they wrongly use EasyJupyter in a notebook?
- [ ] How should errors be handled? For example, if user gets an error because they didn't use torch correctly, how should I handle that? Maybe they should always test in a notebook first? Add the error code block where it happened?
- [ ] Maybe a global daemon that the user can interact with to see all running daemon sessions?

Example error:
╭───────────────────────────────────────── EasyJupyter Error: ValueError ─────────────────────────────────────────╮
│ Notebook: llama_config.ipynb                                                                                    │
│ Location: CELL 2 | ID: 00969281                                                                                 │
│ Code: raise ValueError(f"Missing attribute {attr} in {cls.__name__}")                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


HERE is anther error example, it gave me no code:
╭──────────────────────────────────────── EasyJupyter Error: SyntaxError ─────────────────────────────────────────╮
│ Notebook: llama_config.ipynb                                                                                    │
│ Location: CELL 5 | ID: 00969281                                                                                 │
│ Code:                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯