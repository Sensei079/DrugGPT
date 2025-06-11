from fda_api import fetch_fda_data, get_fda_search_term

def test_get_fda_search_term():
    # Test with a known drug
    search_term = get_fda_search_term('ibuprofen')
    assert 'openfda.generic_name' in search_term
    assert 'openfda.brand_name' in search_term
    
    # Test with a mapped drug
    search_term = get_fda_search_term('advil')
    assert 'openfda.generic_name' in search_term
    assert 'openfda.brand_name' in search_term

def test_fetch_fda_data():
    # Test with a known drug
    result = fetch_fda_data('ibuprofen')
    assert result is not None
    assert 'name' in result
    assert 'info' in result
    assert 'side_effects' in result
    assert 'warnings' in result
    
    # Test with an unknown drug
    result = fetch_fda_data('nonexistentdrug123')
    assert result is not None
    assert result['name'] == 'nonexistentdrug123'
    assert 'No FDA information available' in result['info'] 