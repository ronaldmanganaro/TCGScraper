import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'pages')))
from pages.PokemonPriceTracker import extract_listing

def test_extract_listing_valid():
    card_str = "Pikachu, (25) [Listings: 42]"
    assert extract_listing(card_str) == 42

def test_extract_listing_invalid():
    card_str = "Pikachu, (25) [NoListings]"
    assert extract_listing(card_str) == 0

def test_extract_listing_empty():
    card_str = ""
    assert extract_listing(card_str) == 0
