#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# Meal Management
#
##########################################################

clear_meals() {
  echo "Clearing the table..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

create_meal() {
  id=$1
  meal=$2
  cuisine=$3
  price=$4
  difficulty=$5

  echo "Adding meal ($meal - $cuisine, $price, $difficulty) to the database..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty":\"$difficulty}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-database-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal_name=$2

  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-from-database-by-name/$meal_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name ($meal_name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name ($meal_name)."
    exit 1
  fi
}



###############################################
#
# Battle Management Functions
#
###############################################

# Create a new battle
create_battle() {
  player1=$1
  player2=$2

  echo "Creating a battle between $player1 and $player2..."
  response=$(curl -s -X POST "$BASE_URL/create-battle" -H "Content-Type: application/json" \
    -d "{\"player1\": \"$player1\", \"player2\": \"$player2\"}")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle created successfully."
    battle_id=$(echo "$response" | jq -r '.battle_id')
    echo "Battle ID: $battle_id"
  else
    echo "Failed to create battle."
    exit 1
  fi
}

# Get battle details by ID
get_battle_by_id() {
  battle_id=$1

  echo "Getting battle details for ID ($battle_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-battle/$battle_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle details retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle JSON (ID $battle_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get battle details."
    exit 1
  fi
}

# List all battles
list_battles() {
  echo "Listing all battles..."
  response=$(curl -s -X GET "$BASE_URL/list-battles")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All battles listed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battles JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to list battles."
    exit 1
  fi
}

# Delete a battle by ID
delete_battle() {
  battle_id=$1

  echo "Deleting battle with ID ($battle_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-battle/$battle_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle deleted successfully."
  else
    echo "Failed to delete battle."
    exit 1
  fi
}

# Update battle status (e.g., to "in progress" or "completed")
update_battle_status() {
  battle_id=$1
  new_status=$2

  echo "Updating status of battle ID ($battle_id) to $new_status..."
  response=$(curl -s -X PATCH "$BASE_URL/update-battle-status" -H "Content-Type: application/json" \
    -d "{\"battle_id\": \"$battle_id\", \"status\": \"$new_status\"}")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle status updated successfully."
  else
    echo "Failed to update battle status."
    exit 1
  fi
}

# Fetch leaderboard (e.g., based on battle outcomes)
get_battle_leaderboard() {
  echo "Retrieving battle leaderboard..."
  response=$(curl -s -X GET "$BASE_URL/battle-leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve leaderboard."
    exit 1
  fi
}



# Health checks
check_health
check_db

# Clear the meals
clear_meals

# Create meals
create_meal "Pasta" "Italian" 15.0 "MED" 
create_meal "Burger" "American" 10.0 "HIGH" 
create_meal "Sushi" "Japanese" 25.0 "LOW" 
create_meal "Nachos" "Mexican" 7.0 "MED" 
create_meal "Hotdog" "American" 5.0 "HIGH"

delete_meal_by_id 1
get_leaderboard

get_meal_by_id 2
get_meal_by_name "Sushi"

# Create and retrieve battles
create_battle "Alice" "Bob"
create_battle "Charlie" "Dave"
battle_id_1=$(create_battle "Eve" "Frank")

get_battle_by_id "$battle_id_1"

# List all battles
list_battles

# Update battle status
update_battle_status "$battle_id_1" "in progress"
update_battle_status "$battle_id_1" "completed"

# Retrieve leaderboard
get_battle_leaderboard

# Delete a battle and verify it’s deleted
delete_battle "$battle_id_1"
list_battles


echo "All tests passed successfully!"
