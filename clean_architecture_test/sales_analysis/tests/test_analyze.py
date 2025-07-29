"""Unit tests for the analyze module."""

import pandas as pd
import pytest
from datetime import datetime, timedelta
import tempfile
import os

from src.analyze import compute_stats, StatsResult


@pytest.fixture
def sample_sales_data():
    """Create sample sales data for testing."""
    data = {
        'order_id': [f'ORD-{i:04d}' for i in range(1, 21)],
        'customer_id': [f'CUST-{i%5+1:03d}' for i in range(20)],
        'product': ['Product_A'] * 5 + ['Product_B'] * 5 + ['Product_C'] * 5 + ['Product_D'] * 5,
        'quantity': [1, 2, 3, 4, 5] * 4,
        'unit_price': [10.0, 20.0, 30.0, 40.0, 50.0] * 4,
        'order_date': [datetime(2023, 1, 1) + timedelta(days=i) for i in range(20)],
        'region': ['North'] * 10 + ['South'] * 10
    }
    
    df = pd.DataFrame(data)
    df['revenue'] = df['quantity'] * df['unit_price']
    return df


@pytest.fixture
def empty_dataframe():
    """Create an empty dataframe with correct columns."""
    return pd.DataFrame(columns=[
        'order_id', 'customer_id', 'product', 'quantity', 
        'unit_price', 'order_date', 'region'
    ])


def test_compute_stats_basic(sample_sales_data):
    """Test basic statistics computation."""
    stats = compute_stats(sample_sales_data)
    
    assert isinstance(stats, StatsResult)
    assert stats.total_revenue == 2200.0  # Sum of all revenues
    assert stats.average_order_value == 110.0  # 2200 / 20 orders
    assert len(stats.top_products) == 4  # All products should be in top 5
    assert stats.top_products[0].product == 'Product_D'
    assert stats.top_products[0].revenue == 750.0


def test_compute_stats_empty_dataframe(empty_dataframe):
    """Test statistics computation with empty dataframe."""
    stats = compute_stats(empty_dataframe)
    
    assert stats.total_revenue == 0.0
    assert stats.average_order_value == 0.0
    assert len(stats.top_products) == 0
    assert len(stats.monthly_revenue) == 0


def test_compute_stats_single_product():
    """Test statistics with single product."""
    data = {
        'order_id': ['ORD-001'],
        'customer_id': ['CUST-001'],
        'product': ['Single_Product'],
        'quantity': [10],
        'unit_price': [25.0],
        'order_date': [datetime(2023, 1, 15)],
        'region': ['North']
    }
    
    df = pd.DataFrame(data)
    df['revenue'] = df['quantity'] * df['unit_price']
    
    stats = compute_stats(df)
    
    assert stats.total_revenue == 250.0
    assert stats.average_order_value == 250.0
    assert len(stats.top_products) == 1
    assert stats.top_products[0].product == 'Single_Product'
    assert stats.top_products[0].revenue == 250.0


def test_compute_stats_monthly_aggregation():
    """Test monthly revenue aggregation."""
    data = {
        'order_id': ['ORD-001', 'ORD-002', 'ORD-003'],
        'customer_id': ['CUST-001'] * 3,
        'product': ['Product_A'] * 3,
        'quantity': [1, 2, 3],
        'unit_price': [100.0] * 3,
        'order_date': [
            datetime(2023, 1, 15),
            datetime(2023, 1, 20),
            datetime(2023, 2, 15)
        ],
        'region': ['North'] * 3
    }
    
    df = pd.DataFrame(data)
    df['revenue'] = df['quantity'] * df['unit_price']
    
    stats = compute_stats(df)
    
    assert len(stats.monthly_revenue) == 2
    assert stats.monthly_revenue[0].month == '2023-01'
    assert stats.monthly_revenue[0].revenue == 300.0  # 100 + 200
    assert stats.monthly_revenue[1].month == '2023-02'
    assert stats.monthly_revenue[1].revenue == 300.0


def test_stats_result_dataclass():
    """Test StatsResult dataclass structure."""
    from src.analyze import ProductRevenue, MonthlyRevenue
    
    # Test ProductRevenue
    prod_rev = ProductRevenue(product='Test Product', revenue=100.0)
    assert prod_rev.product == 'Test Product'
    assert prod_rev.revenue == 100.0
    
    # Test MonthlyRevenue
    month_rev = MonthlyRevenue(month='2023-01', revenue=1000.0)
    assert month_rev.month == '2023-01'
    assert month_rev.revenue == 1000.0
    
    # Test StatsResult
    stats = StatsResult(
        total_revenue=1000.0,
        average_order_value=100.0,
        top_products=[prod_rev],
        monthly_revenue=[month_rev]
    )
    
    assert stats.total_revenue == 1000.0
    assert stats.average_order_value == 100.0
    assert len(stats.top_products) == 1
    assert len(stats.monthly_revenue) == 1