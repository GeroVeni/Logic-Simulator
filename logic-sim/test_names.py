"""Test the names module."""
import pytest

from names import Names


############
# FIXTURES #
############

@pytest.fixture
def new_names():
    """Return a new instance of the Names class."""
    return Names()


@pytest.fixture
def sample_names_list():
    """Returns a predefined list of names."""
    return ["george", "jorge", "dimitris"]


@pytest.fixture
def filled_names(sample_names_list):
    """Return a Names class with three error codes and
    three names."""
    new_names = Names()
    new_names.unique_error_codes(3)
    new_names.lookup(sample_names_list)
    return new_names


###################
# TEST EXCEPTIONS #
###################

def test_unique_error_codes_raises_exceptions(filled_names):
    """Test if unique_error_codes raises expected exceptions."""
    with pytest.raises(TypeError):
        filled_names.unique_error_codes(1.4)
    with pytest.raises(TypeError):
        filled_names.unique_error_codes("hello")
    with pytest.raises(ValueError):
        filled_names.unique_error_codes(0)
    with pytest.raises(ValueError):
        filled_names.unique_error_codes(-1)


def test_query_raises_exceptions(filled_names):
    """Test if query raises expected exceptions."""
    with pytest.raises(TypeError):
        filled_names.query(1)
    with pytest.raises(TypeError):
        filled_names.query(1.4)
    with pytest.raises(TypeError):
        filled_names.query(['hello'])
    with pytest.raises(ValueError):
        filled_names.query('')
    with pytest.raises(ValueError):
        filled_names.query('2hello') # identifiers should start with a letter


def test_lookup_raises_exceptions(filled_names):
    """Test if lookup raises expected exceptions."""
    with pytest.raises(TypeError):
        filled_names.lookup(1)
    with pytest.raises(TypeError):
        filled_names.lookup(1.4)
    with pytest.raises(TypeError):
        filled_names.lookup('hello')
    with pytest.raises(TypeError):
        filled_names.lookup(['hello', 2])
    with pytest.raises(TypeError):
        filled_names.lookup([2])
    with pytest.raises(ValueError):
        filled_names.lookup([''])
    with pytest.raises(ValueError):
        filled_names.lookup(['hello', ''])
    with pytest.raises(ValueError):
        filled_names.lookup(['2hello', 'hello'])


def test_get_name_string_raises_exceptions(filled_names):
    """Test if get_name_string raises expected exceptions."""
    with pytest.raises(TypeError):
        filled_names.get_name_string(1.4)
    with pytest.raises(TypeError):
        filled_names.get_name_string(['hello'])
    with pytest.raises(TypeError):
        filled_names.get_name_string('hello')
    with pytest.raises(ValueError):
        filled_names.get_name_string(-1)


###########################
# TEST unique_error_codes #
###########################

def test_unique_error_codes(new_names):
    """Test if unique_error_codes correctly generates error codes."""
    res = new_names.unique_error_codes(1)
    assert res == range(0, 1)
    res = new_names.unique_error_codes(2)
    assert res == range(1, 3)
    res = new_names.unique_error_codes(3)
    assert res == range(3, 6)


##############
# TEST query #
##############

def test_query_names_not_found(filled_names):
    """Test that query returns None for names not in it."""
    assert filled_names.query('non-existing-name') is None


@pytest.mark.parametrize("name, name_id", [
    ("george", 0),
    ("jorge", 1),
    ("dimitris", 2),
])
def test_query(filled_names, name, name_id):
    """Test that query returns correct ID for names in it."""
    assert filled_names.query(name) == name_id


###############
# TEST lookup #
###############

def test_lookup_new_names(new_names, sample_names_list):
    """Test that new names are added by lookup."""
    assert new_names.lookup(sample_names_list) == [0, 1, 2]
    assert new_names.lookup(['a', 'b', 'c']) == [3, 4, 5]


def test_lookup_filled_names(filled_names, sample_names_list):
    """Test that existing names are not added and the correct IDs are returned."""
    assert filled_names.lookup(sample_names_list) == [0, 1, 2]
    assert filled_names.lookup(sample_names_list[::-1]) == [2, 1, 0]
    assert filled_names.lookup(["george", "george"]) == [0, 0]
    # test case for only a subset of input name strings already in list
    assert filled_names.lookup(["george", "andreas"]) == [0, 3]

def test_lookup_empty_names_list(filled_names):
    """Test that an empty input list returns an empty output list."""
    assert filled_names.lookup([]) == []


########################
# TEST get_name_string #
########################

def test_get_name_string_id_not_present(filled_names):
    """Test that get_name_string returns None if ID is not present."""
    assert filled_names.get_name_string(3) is None


@pytest.mark.parametrize("name, name_id", [
    ("george", 0),
    ("jorge", 1),
    ("dimitris", 2),
])
def test_get_name_string_id_present(filled_names, name, name_id):
    """Test that get_name_string return the correct name."""
    assert filled_names.get_name_string(name_id) == name
