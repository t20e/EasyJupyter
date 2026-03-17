import EasyJupyter # Always import at the very top

from test_example import test, Bank, hello # import a notebook

# TODO help VSC intellisense know info about the notebook, for example: TYPECHECKING, and easily importing function in from test_example import test, ....

b = Bank()
print(b.withdraw)