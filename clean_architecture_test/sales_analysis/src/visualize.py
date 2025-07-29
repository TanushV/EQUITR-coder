"""Visualization module for sales analysis.

This module generates charts and graphs for the sales data analysis.
"""

from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plot_revenue_by_product(df: pd.DataFrame, output_path: Path) -> None:
    """Create a horizontal bar chart showing revenue by product.
    
    Args:
        df: DataFrame containing sales data with 'product' and 'revenue' columns
        output_path: Path where the PNG file will be saved
    
    Returns:
        None
    """
    # Set style for better aesthetics
    sns.set_style("whitegrid")
    
    # Calculate revenue by product
    revenue_by_product = df.groupby('product')['revenue'].sum().sort_values(ascending=True)
    
    # Create figure with appropriate size
    plt.figure(figsize=(10, 8))
    
    # Create horizontal bar chart
    bars = plt.barh(revenue_by_product.index, revenue_by_product.values)
    
    # Customize the plot
    plt.title('Revenue by Product', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Total Revenue ($)', fontsize=12)
    plt.ylabel('Product', fontsize=12)
    
    # Format x-axis to show currency
    ax = plt.gca()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Add value labels on bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width + max(revenue_by_product.values) * 0.01, 
                bar.get_y() + bar.get_height()/2, 
                f'${width:,.0f}', 
                ha='left', va='center', fontsize=10)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save with high DPI for quality
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    # Verify file size constraint
    if output_path.exists():
        file_size_kb = output_path.stat().st_size / 1024
        if file_size_kb > 500:
            # Recreate with lower DPI if too large
            plt.figure(figsize=(10, 8))
            plt.barh(revenue_by_product.index, revenue_by_product.values)
            plt.title('Revenue by Product')
            plt.xlabel('Total Revenue ($)')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()


def plot_monthly_trend(df: pd.DataFrame, output_path: Path) -> None:
    """Create a line chart showing monthly revenue trend.
    
    Args:
        df: DataFrame containing sales data with 'order_date' and 'revenue' columns
        output_path: Path where the PNG file will be saved
    
    Returns:
        None
    """
    # Set style for better aesthetics
    sns.set_style("whitegrid")
    
    # Ensure order_date is datetime
    df = df.copy()
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Calculate monthly revenue
    df['year_month'] = df['order_date'].dt.to_period('M')
    monthly_revenue = df.groupby('year_month')['revenue'].sum()
    
    # Convert period index to timestamp for plotting
    monthly_revenue.index = monthly_revenue.index.to_timestamp()
    
    # Create figure
    plt.figure(figsize=(12, 6))
    
    # Create line chart
    line = plt.plot(monthly_revenue.index, monthly_revenue.values, 
                   marker='o', linewidth=2.5, markersize=6, color='#2E86AB')
    
    # Customize the plot
    plt.title('Monthly Revenue Trend', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Revenue ($)', fontsize=12)
    
    # Format y-axis to show currency
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Add value labels on points
    for x, y in zip(monthly_revenue.index, monthly_revenue.values):
        plt.annotate(f'${y:,.0f}', (x, y), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save with high DPI for quality
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    # Verify file size constraint
    if output_path.exists():
        file_size_kb = output_path.stat().st_size / 1024
        if file_size_kb > 500:
            # Recreate with lower DPI if too large
            plt.figure(figsize=(12, 6))
            plt.plot(monthly_revenue.index, monthly_revenue.values, marker='o')
            plt.title('Monthly Revenue Trend')
            plt.xlabel('Month')
            plt.ylabel('Revenue ($)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()


def create_visualizations(df: pd.DataFrame, figures_dir: Path) -> Dict[str, Path]:
    """Create all required visualizations.
    
    Args:
        df: DataFrame containing processed sales data
        figures_dir: Directory where figures will be saved
    
    Returns:
        Dictionary mapping figure names to their file paths
    """
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    revenue_by_product_path = figures_dir / "revenue_by_product.png"
    monthly_trend_path = figures_dir / "monthly_revenue_trend.png"
    
    plot_revenue_by_product(df, revenue_by_product_path)
    plot_monthly_trend(df, monthly_trend_path)
    
    return {
        'revenue_by_product': revenue_by_product_path,
        'monthly_trend': monthly_trend_path
    }