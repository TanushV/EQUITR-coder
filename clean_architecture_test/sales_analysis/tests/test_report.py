"""Unit tests for the report generation module."""

import tempfile
import shutil
from pathlib import Path
from datetime import date
import pytest

from src.report import StatsResult, render_report


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_stats():
    """Create sample statistics for testing."""
    return StatsResult(
        total_revenue=125000.50,
        average_order_value=125.50,
        top_products=[
            {"product": "Widget A", "revenue": 45000.00},
            {"product": "Widget B", "revenue": 35000.00},
            {"product": "Widget C", "revenue": 25000.00},
            {"product": "Widget D", "revenue": 15000.00},
            {"product": "Widget E", "revenue": 5000.50},
        ],
        monthly_revenue=[
            {"month": "2023-01", "revenue": 10000.00},
            {"month": "2023-02", "revenue": 15000.00},
            {"month": "2023-03", "revenue": 20000.00},
        ],
        total_orders=1000,
        date_range={"start": date(2023, 1, 1), "end": date(2023, 12, 31)},
        data_quality={
            "original_rows": 1050,
            "cleaned_rows": 1000,
            "removed_rows": 50,
            "removed_percentage": 4.76,
        },
    )


@pytest.fixture
def sample_figures(temp_dir):
    """Create sample figure files for testing."""
    figures_dir = temp_dir / "figures"
    figures_dir.mkdir()
    
    # Create dummy PNG files
    (figures_dir / "revenue_by_product.png").write_bytes(b"fake png content")
    (figures_dir / "monthly_revenue_trend.png").write_bytes(b"fake png content")
    
    return figures_dir


def test_render_report_creates_markdown_file(temp_dir, sample_stats, sample_figures):
    """Test that render_report creates a markdown file."""
    output_path = temp_dir / "sales_report.md"
    
    render_report(sample_stats, sample_figures, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_render_report_contains_required_sections(temp_dir, sample_stats, sample_figures):
    """Test that the report contains all required sections."""
    output_path = temp_dir / "sales_report.md"
    
    render_report(sample_stats, sample_figures, output_path)
    
    content = output_path.read_text()
    
    # Check for required sections
    assert "# Sales Analysis Report" in content
    assert "## Executive Summary" in content
    assert "## Key Statistics" in content
    assert "## Top Products by Revenue" in content
    assert "## Monthly Revenue Trend" in content
    assert "## Data Quality" in content
    assert "## How to Reproduce" in content


def test_render_report_contains_statistics(temp_dir, sample_stats, sample_figures):
    """Test that the report contains the provided statistics."""
    output_path = temp_dir / "sales_report.md"
    
    render_report(sample_stats, sample_figures, output_path)
    
    content = output_path.read_text()
    
    # Check for specific values
    assert "$125,000.50" in content
    assert "$125.50" in content
    assert "1,000" in content
    assert "Widget A" in content
    assert "$45,000.00" in content


def test_render_report_contains_figure_references(temp_dir, sample_stats, sample_figures):
    """Test that the report contains references to the figures."""
    output_path = temp_dir / "sales_report.md"
    
    render_report(sample_stats, sample_figures, output_path)
    
    content = output_path.read_text()
    
    # Check for figure references
    assert "![Revenue by Product](figures/revenue_by_product.png)" in content
    assert "![Monthly Revenue Trend](figures/monthly_revenue_trend.png)" in content


def test_render_report_contains_reproduce_section(temp_dir, sample_stats, sample_figures):
    """Test that the report contains the reproduce section with correct commands."""
    output_path = temp_dir / "sales_report.md"
    
    render_report(sample_stats, sample_figures, output_path)
    
    content = output_path.read_text()
    
    # Check for reproduce commands
    assert "```bash" in content
    assert "python main.py" in content
    assert "## How to Reproduce" in content


def test_render_report_with_empty_monthly_data(temp_dir, sample_stats, sample_figures):
    """Test that render_report handles empty monthly data gracefully."""
    output_path = temp_dir / "sales_report.md"
    
    # Create stats with empty monthly data
    empty_stats = StatsResult(
        total_revenue=0,
        average_order_value=0,
        top_products=[],
        monthly_revenue=[],
        total_orders=0,
        date_range={"start": date(2023, 1, 1), "end": date(2023, 12, 31)},
        data_quality={
            "original_rows": 0,
            "cleaned_rows": 0,
            "removed_rows": 0,
            "removed_percentage": 0,
        },
    )
    
    render_report(empty_stats, sample_figures, output_path)
    
    content = output_path.read_text()
    
    # Should still contain the sections
    assert "# Sales Analysis Report" in content
    assert "## Executive Summary" in content
    assert "No data available" in content or "$0.00" in content