"""
Command-line interface for DisasterLens.
"""
import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from src.models.predictor import predict_disaster_impact
from src.optimization.allocator import allocate_resources
from src.utils.config import validate_config
from src.utils.logger import logger

# Create console for rich output
console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    DisasterLens - Disaster Impact Prediction and Resource Allocation Tool.
    
    This tool helps predict the impact of natural disasters on communities
    and optimize resource allocation for disaster response.
    """
    # Validate configuration
    if not validate_config():
        console.print("[bold red]Error:[/bold red] Configuration validation failed.")
        console.print("Please check your .env file and ensure all required variables are set.")
        console.print("You can copy .env.example to .env and fill in the values.")
        sys.exit(1)


@cli.command()
@click.option(
    "--region",
    "-r",
    required=True,
    help="Region to predict disaster impact for (e.g., 'Kathmandu' or '27.7172,85.3240')",
)
@click.option(
    "--disaster-type",
    "-d",
    default="flood",
    help="Type of disaster (e.g., flood, earthquake)",
)
@click.option(
    "--model-type",
    "-m",
    default="random_forest",
    type=click.Choice(["linear", "random_forest"]),
    help="Type of prediction model to use",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path for JSON results",
)
def predict(region: str, disaster_type: str, model_type: str, output: Optional[str]):
    """
    Predict disaster impact for a region.
    """
    console.print(f"Predicting {disaster_type} impact for [bold]{region}[/bold]...")
    
    try:
        # Make prediction
        result = predict_disaster_impact(
            location=region,
            disaster_type=disaster_type,
            model_type=model_type,
        )
        
        # Display results
        _display_prediction(result)
        
        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            console.print(f"\nResults saved to [bold]{output}[/bold]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        logger.exception("Error in predict command")
        sys.exit(1)


@cli.command()
@click.option(
    "--regions",
    "-r",
    required=True,
    help="Comma-separated list of regions (e.g., 'Kathmandu,Pokhara')",
)
@click.option(
    "--resources",
    "-res",
    required=True,
    help="Resources in format 'resource1:amount1,resource2:amount2' (e.g., 'water:1000,food:500')",
)
@click.option(
    "--disaster-type",
    "-d",
    default="flood",
    help="Type of disaster (e.g., flood, earthquake)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path for JSON results",
)
def allocate(regions: str, resources: str, disaster_type: str, output: Optional[str]):
    """
    Allocate resources across multiple regions based on predicted impact.
    """
    # Parse regions
    region_list = [r.strip() for r in regions.split(",")]
    
    # Parse resources
    resource_dict = {}
    for item in resources.split(","):
        if ":" in item:
            resource_type, amount = item.split(":")
            try:
                resource_dict[resource_type.strip()] = int(amount.strip())
            except ValueError:
                console.print(f"[bold red]Error:[/bold red] Invalid resource amount: {amount}")
                sys.exit(1)
    
    console.print(f"Allocating resources across [bold]{len(region_list)}[/bold] regions...")
    
    try:
        # Allocate resources
        result = allocate_resources(
            locations=region_list,
            resources=resource_dict,
            disaster_type=disaster_type,
        )
        
        # Display results
        _display_allocation(result)
        
        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            console.print(f"\nResults saved to [bold]{output}[/bold]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        logger.exception("Error in allocate command")
        sys.exit(1)


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to run the visualization server on",
)
@click.option(
    "--port",
    default=5000,
    type=int,
    help="Port to run the visualization server on",
)
def visualize(host: str, port: int):
    """
    Start the web visualization server.
    """
    console.print(f"Starting visualization server on [bold]{host}:{port}[/bold]...")
    
    try:
        # Import here to avoid circular imports
        from src.api.app import app
        app.run(host=host, port=port)
    
    except ImportError:
        console.print("[bold red]Error:[/bold red] Flask not installed. Install with 'pip install flask'.")
        sys.exit(1)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        logger.exception("Error in visualize command")
        sys.exit(1)


def _display_prediction(result: Dict[str, Any]):
    """
    Display prediction results in a formatted table.
    
    Args:
        result (Dict[str, Any]): Prediction results
    """
    # Create table
    table = Table(title=f"Disaster Impact Prediction for {result['location']}")
    
    # Add columns
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    # Add rows
    table.add_row("Location", result["location"])
    table.add_row("Disaster Type", result["disaster_type"])
    table.add_row("Impact Score", f"{result['impact_score']:.2f}")
    table.add_row("Impact Level", result["impact_level"].title())
    
    # Add feature rows
    table.add_row("", "")
    table.add_row("[bold]Key Features[/bold]", "")
    
    for feature, value in result["features"].items():
        if feature in ["rainfall_1h", "rainfall_3h", "rainfall_24h", "rainfall_5d"]:
            table.add_row(feature.replace("_", " ").title(), f"{value:.1f} mm")
        elif feature in ["temperature"]:
            table.add_row(feature.replace("_", " ").title(), f"{value:.1f} °C")
        elif feature in ["wind_speed"]:
            table.add_row(feature.replace("_", " ").title(), f"{value:.1f} m/s")
        elif feature in ["humidity"]:
            table.add_row(feature.replace("_", " ").title(), f"{value:.1f}%")
        elif feature in ["social_signal_count"]:
            table.add_row("Social Signals", str(int(value)))
        elif feature in ["max_urgency", "avg_urgency"]:
            table.add_row(feature.replace("_", " ").title(), f"{value:.2f}")
        else:
            table.add_row(feature.replace("_", " ").title(), str(value))
    
    # Print table
    console.print(table)


def _display_allocation(result: Dict[str, Any]):
    """
    Display allocation results in a formatted table.
    
    Args:
        result (Dict[str, Any]): Allocation results
    """
    # Create table
    table = Table(title=f"Resource Allocation for {result['disaster_type'].title()} Disaster")
    
    # Add columns
    table.add_column("Region", style="cyan")
    table.add_column("Impact", style="magenta")
    
    # Add resource columns
    for resource_type in result["resources"].keys():
        table.add_column(resource_type.title(), style="green")
    
    # Add rows for each location
    for location in result["locations"]:
        # Get impact level
        impact_level = result["predictions"][location]["impact_level"].title()
        impact_score = result["predictions"][location]["impact_score"]
        impact = f"{impact_level} ({impact_score:.2f})"
        
        # Get allocations
        allocations = [
            str(result["allocations"][resource_type][location])
            for resource_type in result["resources"].keys()
        ]
        
        # Add row
        table.add_row(location, impact, *allocations)
    
    # Add totals row
    totals = [str(amount) for amount in result["resources"].values()]
    table.add_row("[bold]Total[/bold]", "", *totals)
    
    # Print table
    console.print(table)


if __name__ == "__main__":
    cli() 