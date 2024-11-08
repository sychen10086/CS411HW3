from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.models.kitchen_model import (
    Meal,
    create_meal,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

   # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the catalog."""

    # Call the function to create a new meal
    create_meal(meal="Spaghetti", cuisine="Italian", price=20.0, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Spaghetti", "Italian", 20.0, "MED")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate meal name (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with meal name 'Spaghetti' already exists."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=20.0, difficulty="MED")
   
def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (e.g., negative number)"""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid meal price: -20.0 \(must be a positive number\)."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=-20.0, difficulty="MED")

    # Attempt to create a meal with a non-number price
    with pytest.raises(ValueError, match="Invalid meal price: invalid \(must be a positive number\)."):
        create_meal(meal="Spaghetti", cuisine="Italian", price="invalid", difficulty="MED")

def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty (e.g., "Easy")."""

    # Attempt to create a meal with a difficulty of easy 
    with pytest.raises(ValueError, match="Invalid difficulty provided: Easy \(must be LOW, MED, or HIGH\)."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=20.0, difficulty="EASY")

    # Attempt to create a meal with a non-string difficulty
    with pytest.raises(ValueError, match="Invalid difficulty provided: 20.0 \(must be LOW, MED, or HIGH\)."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=20.0, difficulty=20.0)


def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the catalog by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_song function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has already been deleted"):
        delete_meal(999)

def test_clear_meals(mock_cursor, mocker):
    """Test clearing the entire meals table (removes all meals)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_meal function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()

######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Spaghetti", "Italian", 20.0, "MED", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Spaghetti", "Italian", 20.0, "MED", False)

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM songs WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_id_bad_id(mock_cursor):
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)


def test_get_meal_by_name(mock_cursor):
    # Simulate that the meal exists (name = "Spaghetti")
    mock_cursor.fetchone.return_value = (1, "Spaghetti", "Italian", 20.0, "MED", False)

    # Call the function and check the result
    result = get_meal_by_name("Spaghetti")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Spaghetti", "Italian", 20.0, "MED", False)

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Spaghetti",)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_name_bad_name(mock_cursor):
    # Simulate that no meal exists for the given name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with name Nachos not found"):
        get_meal_by_name("Nachos")

def test_get_leaderboard(mock_cursor):
    """Test retrieving all meals that are not marked as deleted."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Pasta", "Italian", 10.0, "MED", 10, 8, 0.8, False),
        (2, "Sushi", "Japanese", 15.0, "HIGH", 20, 15, 0.75, False),
        (3, "Burger", "American", 12.0, "LOW", 5, 2, 0.4, True)  # This meal is marked as deleted
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard(sort_by="wins")

    # Ensure the results match the expected output
    expected_result = [
        {"id": 1, "meal": "Pasta", "cuisine": "Italian", "price": 10.0, "difficulty": "MED", "battles": 10, "wins": 8, "win_pct": 80.0},
        {"id": 2, "meal": "Sushi", "cuisine": "Japanese", "price": 15.0, "difficulty": "HIGH", "battles": 20, "wins": 15, "win_pct": 75.0}
    ]

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_battles_greater_than_zero(mock_cursor):
    """Test retrieving all meals with battles > 0."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Pasta", "Italian", 10.0, "MED", 10, 8, 0.8),
        (2, "Sushi", "Japanese", 15.0, "HIGH", 20, 15, 0.75),
        (3, "Burger", "American", 12.0, "LOW", 0, 0, None)  # This meal should be excluded
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard(sort_by="wins")

    # Expected result should exclude the meal with battles = 0
    expected_result = [
        {"id": 1, "meal": "Pasta", "cuisine": "Italian", "price": 10.0, "difficulty": "MED", "battles": 10, "wins": 8, "win_pct": 80.0},
        {"id": 2, "meal": "Sushi", "cuisine": "Japanese", "price": 15.0, "difficulty": "HIGH", "battles": 20, "wins": 15, "win_pct": 75.0}
    ]

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Verify the SQL query
    expected_query = """
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """
    actual_query = mock_cursor.execute.call_args[0][0]
    assert normalize_whitespace(actual_query) == normalize_whitespace(expected_query), "The SQL query did not match the expected structure."

def test_get_leaderboard_ordered_by_wins(mock_cursor):
    """Test retrieving all meals ordered by wins."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Pasta", "Italian", 10.0, "MED", 10, 8, 0.8),
        (2, "Sushi", "Japanese", 15.0, "HIGH", 20, 15, 0.75),
        (3, "Burger", "American", 12.0, "LOW", 5, 2, 0.4)
    ]

    # Call the get_leaderboard function with sort_by="wins"
    leaderboard = get_leaderboard(sort_by="wins")

    # Ensure the results are sorted by winss
    expected_result = [
        {"id": 2, "meal": "Sushi", "cuisine": "Japanese", "price": 15.0, "difficulty": "HIGH", "battles": 20, "wins": 15, "win_pct": 75.0},
        {"id": 1, "meal": "Pasta", "cuisine": "Italian", "price": 10.0, "difficulty": "MED", "battles": 10, "wins": 8, "win_pct": 80.0},
        {"id": 3, "meal": "Burger", "cuisine": "American", "price": 12.0, "difficulty": "LOW", "battles": 5, "wins": 2, "win_pct": 40.0}
    ]
        

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, sort_by
        FROM meals
        WHERE deleted = FALSE AND battles > 0 
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match

def test_get_leaderboard_ordered_by_win_pct(mock_cursor):
    """Test retrieving all meals ordered by win_pct."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (3, "Burger", "American", 12.0, "LOW", 5, 2, 0.4),
        (1, "Pasta", "Italian", 10.0, "MED", 10, 8, 0.8),
        (2, "Sushi", "Japanese", 15.0, "HIGH", 20, 15, 0.75)
    ]

    # Call the get_leaderboard function with sort_by="win_pct"
    leaderboard = get_leaderboard(sort_by="win_pct")

    # Ensure the results are sorted by win percentage
    expected_result = [
        {"id": 1, "meal": "Pasta", "cuisine": "Italian", "price": 10.0, "difficulty": "MED", "battles": 10, "wins": 8, "win_pct": 80.0},
        {"id": 2, "meal": "Sushi", "cuisine": "Japanese", "price": 15.0, "difficulty": "HIGH", "battles": 20, "wins": 15, "win_pct": 75.0},
        {"id": 3, "meal": "Burger", "cuisine": "American", "price": 12.0, "difficulty": "LOW", "battles": 5, "wins": 2, "win_pct": 40.0}
    ]

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, sort_by
        FROM meals
        WHERE deleted = FALSE AND battles > 0 
        ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_invalid_sort_by():
    """Test error when trying to create a leaderboard with an invalid sort_by (e.g., points)."""

    #Expect a ValueError when sort_by value is invalid
    with pytest.raises(ValueError, match="Invalid sort_by parameter: points \(must be wins or win_pct\)."):
        get_leaderboard(sort_by="points")

def test_update_meal_stats_win(mock_cursor):
    """Test updating meal stats when the result is 'win'."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call update_meal_stats function with 'win' result for a sample meal ID
    meal_id = 1
    update_meal_stats(meal_id, result="win")

    # Normalize the expected SQL query for wins
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Asset that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID and result)
    expected_arguments = (meal_id, result)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_update_meal_stats_loss(mock_cursor):
    """Test updating meal stats when the result is 'loss'."""

    # Simulate that the meal exists and is not deleted
    mock_cursor.fetchone.return_value = [False]

    # Call update_meal_stats with 'loss' result for a sample meal ID
    meal_id = 2
    update_meal_stats(meal_id, result="loss")

    # Normalize the expected SQL query for losses
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Asset that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID and result)
    expected_arguments = (meal_id, result)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


### Test for Updating a Deleted Meal:
def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when trying to update stats for a deleted meal."""

    # Simulate that the meal exists but is marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, result="win")

    # Ensure that no SQL query for updating stats was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test error when trying to update stats with an invalid result."""

    # Simulate that the meal exists and is not marked as deleted
    mock_cursor.fetchone.return_value = [False]

    # Attempt to update stats with an invalid result (e.g., "draw")
    with pytest.raises(ValueError, match="Invalid result: draw. Expected 'win' or 'loss'."):
        update_meal_stats(1, result="draw")

    # Ensure that no SQL query for updating stats was executed
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))
