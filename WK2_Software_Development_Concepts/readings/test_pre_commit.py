import os
import sys


def my_messy_function(arg1, arg2, arg3):
    """Black will fix the spacing in the arguments above."""
    # Black hates inconsistent quotes and cramped operators
    my_list = ["apple", "banana", "cherry"]
    dict_variable = {"key": "value", "other": 123}

    # Black will also fix this cramped math
    result = arg1 + arg2 * arg3

    print("Black will fix these weird parentheses and quotes")
    return result


# Black will ensure there is exactly one newline at the end
