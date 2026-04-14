"""This example is to shows that code can be imported from jupyter notebooks."""

import EasyJupyter  # Always import at the very top of your main.py or in notebooks if importing from other notebooks. This is to start the watcher daemon if it isn't already running.

# Use a function that was defined in a notebook
# from nested_note
from nested.nested_notebook import Bank


# use the Bank class from notebook
b = Bank()
# Print the bank's amount
print(b.amount)

