import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.rows import (  # noqa: E402
    find_dni_index, normalize_dni, pad_rows, parse_fecha, unique_keys,
)


def test_unique_keys_duplicates_and_blanks():
    assert unique_keys(["a", "", "a", " ", "a", "b"]) == [
        "a", "__blank__1", "a_2", "__blank__2", "a_3", "b"]


def test_unique_keys_no_collision_with_existing_suffix():
    assert unique_keys(["a", "a_2", "a"]) == ["a", "a_2", "a_3"]


def test_normalize_dni():
    assert normalize_dni("12345678.0") == "12345678"
    assert normalize_dni(" 12.345.678 ") == "12345678"
    assert normalize_dni("") is None
    assert normalize_dni("s/d") is None


def test_find_dni_index():
    assert find_dni_index(["Nombre", " Dni "]) == 1
    assert find_dni_index(["Nombre", "Por favor completa el DNI"]) == 1
    assert find_dni_index(["Nombre"]) is None


def test_parse_fecha():
    assert parse_fecha("05/03/2024 10:11:12") == "2024-03-05"
    assert parse_fecha("2024-03-05") == "2024-03-05"
    assert parse_fecha("basura") is None


def test_pad_rows():
    assert pad_rows([["a", "b"], ["c"]]) == [["a", "b"], ["c", ""]]
