"""Test the names module."""
import pytest

from names import Names


@pytest.fixture
def new_names():
    """Return a new instance of the Names class."""
    return Names()


@pytest.fixture
def sample_names_list():
    """Returns a predefined list of names."""
    return ["george", "jorge", "dimitris"]


@pytest.fixture
def names_filled(sample_names_list):
    """Return a Names class with three error codes and
    three names."""
    new_names = Names()
    new_names.unique_error_codes(3)
    new_names.lookup(sample_names_list)
    return new_names


def test_unique_error_codes_raises_exceptions(names_filled):
    """Test if unique_error_codes raises expected exceptions."""
    with pytest.raises(TypeError):
        names_filled.unique_error_codes(1.4)
    with pytest.raises(TypeError):
        names_filled.unique_error_codes("hello")
    with pytest.raises(ValueError):
        names_filled.unique_error_codes(0)
    with pytest.raises(ValueError):
        names_filled.unique_error_codes(-1)


def test_query_raises_exceptions(names_filled):
    """Test if query raises expected exceptions."""
    with pytest.raises(TypeError):
        names_filled.query(1)
    with pytest.raises(TypeError):
        names_filled.query(1.4)
    with pytest.raises(TypeError):
        names_filled.query(['hello'])
    with pytest.raises(ValueError):
        names_filled.query('')


def test_lookup_raises_exceptions(names_filled):
    """Test if lookup raises expected exceptions."""
    with pytest.raises(TypeError):
        names_filled.lookup(1)
    with pytest.raises(TypeError):
        names_filled.lookup(1.4)
    with pytest.raises(TypeError):
        names_filled.lookup('hello')
    with pytest.raises(TypeError):
        names_filled.lookup(['hello', 2])
    with pytest.raises(TypeError):
        names_filled.lookup([2])
    with pytest.raises(ValueError):
        names_filled.lookup([''])
    with pytest.raises(ValueError):
        names_filled.lookup(['hello', ''])
        
def test_get_name_string_raises_exceptions(names_filled):
    """Test if get_name_string raises expected exceptions."""
    with pytest.raises(TypeError):
        names_filled.get_name_string(1.4)
    with pytest.raises(TypeError):
        names_filled.get_name_string('hello')
    with pytest.raises(ValueError):
        names_filled.get_name_string(-1)
