# TODO

- [ ] 💡 When a user CMD+left mouse click on a function name to go its definition, it brings them to the cache file instead of the notebook file. Can this be fixed without having to create an extension? **Answer:** No, Python language servers lack source mapping natively. As a fallback, the auto-generated file header was updated to explicitly point users to the correct notebook.
- Line/Cell Specific Mapping (Estimated Time: 1 - 2 days): If you want the experience to be seamless (where clicking a function takes them not just to the notebook, but to the exact cell and line where the function is defined), it will take a bit more effort.
  - How it works: When intercepting the file open event, you would capture the line number the user landed on in the cache .py file. Because your EasyJupyterLoader already injects helpful headers like # CELL 5 | ID: f974e092, your extension would simply read the text of the cache file up to the user's cursor line, find the last # CELL header, and then use the VS Code Notebook API (vscode.NotebookEditor) to focus on that specific cell index.
  - Complexity: Navigating the VS Code Notebook API can be slightly finicky compared to standard text editors, which adds some development time.
  - If you decide to go this route, you can generate the boilerplate for a VS Code extension by simply running npx yo code in your terminal, selecting "New Extension (TypeScript)", and adding your logic to the extension.ts file!

- [ ] Maybe a global daemon that the user can interact with to see all running daemon sessions?
