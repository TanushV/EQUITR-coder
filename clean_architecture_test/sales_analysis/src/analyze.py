"""
Analysis module for sales data.

This module provides functionality to compute statistics from cleaned sales data.
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import Any, Dict, List
import numpy as np


@dataclass
class StatsResult:
    """Container for computed sales statistics."""
    
    total_revenue: float
    average_order_value: float
    top_5_products: List[Dict[str, Any]]
    monthly_revenue_trend: List[Dict[str, Any]]
    total_orders: int
    unique_customers: int
    unique_products: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert StatsResult to dictionary for serialization."""
        return {
            'total_revenue': self.total_revenue,
            'average_order_value': self.average_order_value,
            'top_5_products': self.top_5_products,
            'monthly_revenue_trend': self.monthly_revenue_trend,
            'total_orders': self.total_orders,
            'unique_customers': self.unique_customers,
            'unique_products': self.unique_products
        }


def compute_stats(df: pd.DataFrame) -> StatsResult:
    """
    Compute comprehensive statistics from sales data.
    
    Args:
        df: DataFrame with columns ['order_id', 'customer_id', 'product', 
                                   'quantity', 'unit_price', 'order_date', 'region']
    
    Returns:
        StatsResult object containing computed statistics
    
    Raises:
        ValueError: If required columns are missing or data is empty
    """
    if df.empty:
        raise ValueError("Cannot compute statistics on empty DataFrame")
    
    required_columns = ['order_id', 'customer_id', 'product', 'quantity', 'unit_price', 'order_date']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Ensure order_date is datetime
    df = df.copy()
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Calculate revenue for each order
    df['revenue'] = df['quantity'] * df['unit_price']
    
    # Basic statistics
    total_revenue = float(df['revenue'].sum())
    total_orders = int(len(df))
    average_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0.0
    unique_customers = int(df['customer_id'].nunique())
    unique_products = int(df['product'].nunique())
    
    # Top 5 products by revenue
    product_revenue = df.groupby('product').agg({
        'revenue': 'sum',
        'quantity': 'sum'
    }).reset_index()
    product_revenue = product_revenue.sort_values('revenue', ascending=False).head(5)
    
    top_5_products = []
    for _, row in product_revenue.iterrows():
        top_5_products.append({
            'product': str(row['product']),
            'total_revenue': float(row['revenue']),
            'total_quantity': int(row['quantity'])
        })
    
    # Monthly revenue trend
    df['year_month'] = df['order_date'].dt.to_period('M')
    monthly_revenue = df.groupby('year_month')['revenue'].sum().reset_index()
    monthly_revenue['year_month'] = monthly_revenue['year_month'].astype(str)
    
    monthly_revenue_trend = []
    for _, row in monthly_revenue.iterrows():
        monthly_revenue_trend.append({
            'month': str(row['year_month']),
            'revenue': float(row['revenue'])
        })
    
    # Sort by month for consistent ordering
    monthly_revenue_trend.sort(key=lambda x: x['month'])
    
    return StatsResult(
        total_revenue=total_revenue,
        average_order_value=average_order_value,
        top_5_products=top_5_products,
        monthly_revenue_trend=monthly_revenue_trend,
        total_orders=total_orders,
        unique_customers=unique_customers,
        unique_products=unique_products
    )