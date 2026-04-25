# TODO

- [ ] A better search in notebooks is a must-have, VSC currently struggles with searches in notebooks. Same for the TODO extension.

- [ ] Any other warnings I can give the user, if they wrongly use EasyJupyter in a notebook?
- [ ] How should errors be handled? For example, if user gets an error because they didn't use torch correctly, how should I handle that? Maybe they should always test in a notebook first? Add the error code block where it happened?
- [ ] Maybe a global daemon that the user can interact with to see all running daemon sessions?
- [ ] Setup a notebook in nested example that are acutal testes for the EasyJupyter package, it must pass all those tests before I can release publish a new version.

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