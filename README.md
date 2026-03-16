🚧🚧🚧🚧🚧🚧🚧🚧

# TODO

Code out parts of the code in juyper notebooks, and easily intergrate them into a larger code base: https://gemini.google.com/app/93150fb38ed50976

This library is specifically designed to code out parts of code in jupyter notebooks, than putting it all together. JupyText doesn't quick do this.

**Things that this library should resolve:**

1. Seamless Integration & Modularization
   1. Intent: Treat a .ipynb file as a first-class module.
   2. Requirement: Allow import notebook_name directly in .py files without pre-conversion steps.
   3. Requirement: Support sub-folder imports (e.g., from components import attention_nb).
2. Traceback & Debugging Transparency
   1. Intent: Ensure errors point to the source of truth, not a memory buffer.
   2. Requirement: Implement Source Mapping. If an error occurs on line 5 of the generated code, the traceback should explicitly state: File "attention.ipynb", Cell 3, Line 2.
   3. Requirement: Compatibility with VS Code/PyCharm debuggers so breakpoints actually work inside the notebook cells.
3. The Selective Export Syntax (#%)
   1. Intent: Distinguish between "Library Code" and "Exploratory Code."
   2. Requirement: Line-level: Use #% to ignore a single line (e.g., a local hyperparameter).
   3. Requirement: Cell-level: A magic command or comment at the top (e.g., #%% skip) to ignore the entire cell (useful for plt.show() or large dummy data loading).
4. Environment & Context Isolation
   1. Intent: Prevent notebooks from "polluting" the main namespace.
   2. Requirement: Resolve the Circular Dependency issue by ensuring that the import hook handles "already loaded" modules correctly without re-executing the entire notebook logic.
   3. Requirement: Ensure global variables in the notebook don't accidentally override variables in main.py (Namespace Sandboxing).
5. Performance & Caching
   1. Intent: Make it fast enough for large projects.
   2. Requirement: Implement a .pyc-style caching mechanism. Only re-parse the notebook if the .ipynb file's "Last Modified" timestamp has changed.
   
Other:

1. Rate it out of 10, whether I should implement it!
2. A better search in notebooks is a must-have, VSC currently struggles with searches in notebooks.
3. What are some big hurdles, for example maybe Jupyter lab, VSC, or other popular IDEs don't like this?
4. What should I name it?
5. Import files as .ipynb and thats where its temp converted into .py at runtime.
6. What about testing, i get you could test in the notebook. I think that for data science projects not really that big of an issue, however, for normal python project tests with unittest is a must!
7. When I click a function name in VSC to go to that file that contains the function, it should go to the notebook and not a temp .py file for that file
8. What languages should I build it with?
9. Also, I have an issue with the #TODO extension in VSC, it works perfectly except when used inside a markdown cell in a notebook, sometimes it can't find the #TODOs
10. If I do implement it, mention to users thats its best to use the __init__.py in every directory like what I did in the transformer model (relative imports). And also the differences between jupytext and this
   1. Also would this be an issue: "Since you are using Jupytext/Jupyter, relative imports can sometimes break when running the cell inside the notebook (because the notebook doesn't always know it's part of a package).", and I have seen if fail sometimes, is this something that could be resolved?
   2. Managed a workaround with:
        ```python
        try: # works when ran via main.py (package mode)
            from .residual_con_layer_norm import ResidualConnection, LayerNorm
            from .multi_head_attention import Multi_Head_Attention
            from .FeedForwardNetwork import FeedForwardNetwork
            from .model_utils import clones
        except ImportError:
            # Works when running from inside Jupyter Notebook
            from residual_con_layer_norm import ResidualConnection, LayerNorm
            from multi_head_attention import Multi_Head_Attention
            from FeedForwardNetwork import FeedForwardNetwork
            from model_utils import clones
        ```
    3. Have the option to peek into the temp python file, because lets say I want to share my code with an AI chat its easier, or maybe just a copy button in the notebook itself!

