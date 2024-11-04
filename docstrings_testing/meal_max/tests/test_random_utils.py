import pytest
from meal_max.utils.random_utils import get_random  # Assuming random_selection exists in random_utils

def test_random_selection_list():
    elements = [1, 2, 3, 4]
    result = get_random(elements)
    assert result in elements

def test_random_selection_empty_list():
    result = get_random([])
    assert result is None  # Assuming None is returned for an empty list

def test_random_selection_one_element():
    elements = [99]
    result = get_random(elements)
    assert result == 99
