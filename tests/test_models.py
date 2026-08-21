import pytest
from pydantic import ValidationError

from features.servers.models import RegisterServerInput


def _valid_boundary_kwargs(**overrides) -> dict:
    kwargs = {
        "advanced": False,
        "anti_cheat_on": False,
        "bonus_frequency": 0,
        "country": "a" * 2,
        "current_map": "a" * 16,
        "game_style": "a" * 3,
        "info": "a" * 255,
        "max_players": 2,
        "name": "a" * 30,
        "num_bots": 0,
        "os": "a" * 10,
        "players": ["a" * 16, "b" * 16],
        "port": 23073,
        "private": False,
        "realistic": False,
        "respawn": 0,
        "survival": False,
        "version": "a" * 10,
        "wm": False,
    }
    kwargs.update(overrides)
    return kwargs


def test_all_fields_exactly_at_max_length_is_valid():
    RegisterServerInput(**_valid_boundary_kwargs())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("country", "a" * 3),
        ("current_map", "a" * 17),
        ("game_style", "a" * 4),
        ("info", "a" * 256),
        ("name", "a" * 31),
        ("os", "a" * 11),
        ("version", "a" * 11),
    ],
)
def test_one_char_past_max_length_is_invalid(field, value):
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(**{field: value}))


def test_too_long_player_name_is_invalid():
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(players=["a" * 17]))


def test_players_over_max_players_is_invalid():
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(max_players=1, players=["a", "b"]))


def test_empty_optional_strings_is_valid():
    RegisterServerInput(**_valid_boundary_kwargs(country="", info=""))


def test_empty_players_list_is_valid():
    RegisterServerInput(**_valid_boundary_kwargs(players=[]))


def test_max_players_zero_is_invalid():
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(max_players=0, players=[]))


def test_port_zero_is_invalid():
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(port=0))


def test_port_65535_is_valid():
    RegisterServerInput(**_valid_boundary_kwargs(port=65535))


def test_port_out_of_range_is_invalid():
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(port=65536))


def test_negative_numbers_on_unsigned_fields_are_invalid():
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(respawn=-1))


def test_string_typed_number_is_invalid():
    # strict=True: no "23073" -> 23073 coercion
    with pytest.raises(ValidationError):
        RegisterServerInput(**_valid_boundary_kwargs(port="23073"))
