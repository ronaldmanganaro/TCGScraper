import sys
import os
import pytest
import pandas as pd

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'pages')))
from pages.Repricer import filter_data, analyze_repricing

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Product Name": ["CardA", "CardB", "CardC"],
        "Product Line": ["Magic", "Magic", "Pokemon"],
        "Set Name": ["Set1", "Set1", "Set2"],
        "Rarity": ["Rare", "Common", "Rare"],
        "Total Quantity": [10, 5, 2],
        "TCG Marketplace Price": [5.0, 2.0, 10.0],
        "TCG Market Price": [4.0, 2.5, 8.0],
        "Condition": ["NM", "LP", "NM"]
    })


def test_filter_data_basic(sample_df):
    # Should filter by price and quantity
    filtered = filter_data(
        sample_df, min_price=3, max_price=10, min_listing=1, max_listing=10,
        product_line="All", set_name="All", rarity_filter="All", search_text=""
    )
    assert len(filtered) == 2
    assert all(filtered["Product Name"].isin(["CardA", "CardC"]))


def test_filter_data_rarity(sample_df):
    filtered = filter_data(
        sample_df, min_price=0, max_price=10, min_listing=0, max_listing=10,
        product_line="All", set_name="All", rarity_filter="Rare", search_text=""
    )
    assert set(filtered["Rarity"]) == {"Rare"}


def test_filter_data_search(sample_df):
    filtered = filter_data(
        sample_df, min_price=0, max_price=10, min_listing=0, max_listing=10,
        product_line="All", set_name="All", rarity_filter="All", search_text="CardB"
    )
    assert len(filtered) == 1
    assert filtered.iloc[0]["Product Name"] == "CardB"


def test_analyze_repricing_threshold(sample_df):
    # All cards should exceed a 10% threshold (CardA: +25%, CardB: -20%, CardC: +25%)
    result = analyze_repricing(sample_df, threshold=10)
    assert "percentage_difference" in result.columns
    assert "suggested_price" in result.columns
    assert set(result["Product Name"]) == {"CardA", "CardB", "CardC"}


def test_analyze_repricing_suggested_price(sample_df):
    result = analyze_repricing(sample_df, threshold=10)
    # suggested_price should be 10% above market price
    for idx, row in result.iterrows():
        assert abs(row["suggested_price"] -
                   row["TCG Market Price"] * 1.1) < 1e-6
