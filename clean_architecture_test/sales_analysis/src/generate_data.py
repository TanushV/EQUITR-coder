"""
Data generation module for synthetic sales data.

This module generates deterministic synthetic sales data for analysis purposes.
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from faker import Faker

from logger import get_logger

logger = get_logger(__name__)

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)
fake = Faker()
fake.seed_instance(42)

# Constants
PRODUCTS = [
    "Laptop", "Smartphone", "Tablet", "Headphones", "Monitor",
    "Keyboard", "Mouse", "Webcam", "Speaker", "Charger",
    "Cable", "Case", "Stand", "Adapter", "Battery"
]

REGIONS = [
    "North America", "Europe", "Asia", "South America", 
    "Africa", "Oceania"
]


def generate_sales_csv(path: Path, rows: int = 1000) -> None:
    """
    Generate synthetic sales data and save to CSV.
    
    Args:
        path: Path where the CSV file will be saved
        rows: Number of rows to generate (default: 1000)
    
    Returns:
        None
    
    Raises:
        OSError: If unable to write to the specified path
    """
    logger.info(f"Starting data generation: {rows} rows to {path}")
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    data = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(rows):
        order_date = base_date + timedelta(
            days=random.randint(0, 364),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        quantity = max(1, int(np.random.poisson(3)))
        unit_price = round(np.random.uniform(10.0, 1000.0), 2)
        
        row = {
            "order_id": f"ORD-{i+1:06d}",
            "customer_id": f"CUST-{random.randint(1, 500):05d}",
            "product": random.choice(PRODUCTS),
            "quantity": quantity,
            "unit_price": unit_price,
            "order_date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "region": random.choice(REGIONS)
        }
        data.append(row)
    
    # Create DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    
    logger.info(f"Successfully generated {len(df)} rows to {path}")
    logger.info(f"Data schema: {list(df.columns)}")
    logger.info(f"Date range: {df['order_date'].min()} to {df['order_date'].max()}")


def validate_generated_data(path: Path) -> bool:
    """
    Validate the generated CSV file meets requirements.
    
    Args:
        path: Path to the CSV file to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        df = pd.read_csv(path)
        
        # Check row count
        if not (1000 <= len(df) <= 1050):
            logger.error(f"Row count {len(df)} outside expected range 1000-1050")
            return False
        
        # Check required columns
        required_cols = ["order_id", "customer_id", "product", "quantity", 
                        "unit_price", "order_date", "region"]
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
            return False
        
        # Check data types
        if not all(df['quantity'] >= 0):
            logger.error("Negative quantities found")
            return False
            
        if not all(df['unit_price'] >= 0):
            logger.error("Negative unit prices found")
            return False
        
        logger.info("Data validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        return False


if __name__ == "__main__":
    output_path = Path("data/raw/sales_data.csv")
    generate_sales_csv(output_path)
    validate_generated_data(output_path)