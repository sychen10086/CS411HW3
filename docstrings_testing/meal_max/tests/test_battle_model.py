import pytest
from meal_max.models.battle_model import Character, battle
from meal_max.utils.random_utils import random_selection  

@pytest.fixture
def characters():
    char_a = Character(name="Knight", health=100, attack=15, defense=10)
    char_b = Character(name="Orc", health=120, attack=12, defense=8)
    return char_a, char_b

def test_init_character(characters):
    char_a, _ = characters
    assert char_a.name == "Knight"
    assert char_a.health == 100
    assert char_a.attack == 15
    assert char_a.defense == 10

def test_attack_damage_calculation(characters):
    char_a, char_b = characters
    initial_health_b = char_b.health
    damage = char_a.attack_enemy(char_b)  # Hypothetical method
    assert damage > 0
    assert char_b.health == initial_health_b - damage

def test_defend_calculation(characters):
    char_a, char_b = characters
    initial_health_a = char_a.health
    damage = char_b.attack
    char_a.defend_attack(damage)  # Hypothetical defend method
    assert char_a.health < initial_health_a

def test_battle_outcome(characters):
    char_a, char_b = characters
    result = battle(char_a, char_b)  # Hypothetical battle function
    assert result in ["Knight", "Orc"]

def test_random_selection_in_battle(characters):
    char_a, char_b = characters
    selected = random_selection([char_a, char_b])
    assert selected in [char_a, char_b]
