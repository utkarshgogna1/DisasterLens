"""
Resource allocation optimization for DisasterLens.

This module provides functions to optimize the allocation of limited resources
across affected areas based on predicted impact and other constraints.
"""
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
from scipy.optimize import linprog

from src.models.predictor import predict_disaster_impact
from src.utils.logger import logger


class ResourceAllocator:
    """
    Class for optimizing resource allocation across affected areas.
    """

    def __init__(self):
        """
        Initialize the ResourceAllocator.
        """
        # Default resource types and their weights
        self.resource_types = {
            "water": {"weight": 1.0, "priority": 1.0},
            "food": {"weight": 1.5, "priority": 0.9},
            "medicine": {"weight": 0.5, "priority": 0.8},
            "shelter": {"weight": 5.0, "priority": 0.7},
            "blankets": {"weight": 0.8, "priority": 0.6},
        }
    
    def allocate(
        self,
        locations: List[str],
        resources: Dict[str, int],
        disaster_type: str = "flood",
        max_distance: Optional[float] = None,
        central_location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Allocate resources across multiple locations.
        
        Args:
            locations (List[str]): List of affected locations
            resources (Dict[str, int]): Available resources (e.g., {"water": 1000})
            disaster_type (str): Type of disaster
            max_distance (Optional[float]): Maximum distance for allocation
            central_location (Optional[str]): Central location for distance calculation
        
        Returns:
            Dict[str, Any]: Allocation results
        """
        # Get impact predictions for each location
        predictions = {}
        for location in locations:
            try:
                prediction = predict_disaster_impact(location, disaster_type)
                predictions[location] = prediction
            except Exception as e:
                logger.error(f"Error predicting impact for {location}: {e}")
                # Use a default prediction with low impact
                predictions[location] = {
                    "location": location,
                    "disaster_type": disaster_type,
                    "impact_score": 0.1,
                    "impact_level": "minimal",
                }
        
        # Calculate allocation for each resource type
        allocations = {}
        
        for resource_type, amount in resources.items():
            # Get resource properties
            resource_props = self.resource_types.get(
                resource_type, 
                {"weight": 1.0, "priority": 0.5}
            )
            
            # Allocate based on impact scores
            allocation = self._optimize_allocation(
                locations=locations,
                predictions=predictions,
                resource_type=resource_type,
                amount=amount,
                resource_props=resource_props,
            )
            
            allocations[resource_type] = allocation
        
        # Combine results
        result = {
            "locations": locations,
            "disaster_type": disaster_type,
            "resources": resources,
            "allocations": allocations,
            "predictions": predictions,
        }
        
        return result
    
    def _optimize_allocation(
        self,
        locations: List[str],
        predictions: Dict[str, Dict[str, Any]],
        resource_type: str,
        amount: int,
        resource_props: Dict[str, float],
    ) -> Dict[str, int]:
        """
        Optimize allocation of a single resource type.
        
        Args:
            locations (List[str]): List of affected locations
            predictions (Dict[str, Dict[str, Any]]): Impact predictions
            resource_type (str): Type of resource
            amount (int): Available amount
            resource_props (Dict[str, float]): Resource properties
        
        Returns:
            Dict[str, int]: Allocation for each location
        """
        # Extract impact scores
        impact_scores = [predictions[loc]["impact_score"] for loc in locations]
        
        # Simple proportional allocation based on impact scores
        if sum(impact_scores) == 0:
            # Equal allocation if all impacts are zero
            equal_amount = amount // len(locations)
            remainder = amount % len(locations)
            
            allocation = {loc: equal_amount for loc in locations}
            
            # Distribute remainder
            for i in range(remainder):
                allocation[locations[i]] += 1
        else:
            # Normalize impact scores
            normalized_scores = [score / sum(impact_scores) for score in impact_scores]
            
            # Calculate initial allocation
            raw_allocation = [int(score * amount) for score in normalized_scores]
            allocated = sum(raw_allocation)
            
            # Distribute remainder based on fractional parts
            remainder = amount - allocated
            fractions = [(score * amount) % 1 for score in normalized_scores]
            
            # Sort locations by fractional part (descending)
            sorted_indices = sorted(
                range(len(fractions)), 
                key=lambda i: fractions[i], 
                reverse=True
            )
            
            # Create allocation dictionary
            allocation = {locations[i]: raw_allocation[i] for i in range(len(locations))}
            
            # Distribute remainder
            for i in range(remainder):
                if i < len(sorted_indices):
                    idx = sorted_indices[i]
                    allocation[locations[idx]] += 1
        
        return allocation
    
    def _optimize_with_linprog(
        self,
        locations: List[str],
        predictions: Dict[str, Dict[str, Any]],
        resource_type: str,
        amount: int,
        resource_props: Dict[str, float],
    ) -> Dict[str, int]:
        """
        Optimize allocation using linear programming.
        
        Args:
            locations (List[str]): List of affected locations
            predictions (Dict[str, Dict[str, Any]]): Impact predictions
            resource_type (str): Type of resource
            amount (int): Available amount
            resource_props (Dict[str, float]): Resource properties
        
        Returns:
            Dict[str, int]: Allocation for each location
        """
        n_locations = len(locations)
        
        # Extract impact scores
        impact_scores = np.array([predictions[loc]["impact_score"] for loc in locations])
        
        # Objective: Maximize impact * allocation (minimize negative)
        # We weight by the resource priority
        c = -impact_scores * resource_props["priority"]
        
        # Constraint: Sum of allocations <= total amount
        A_ub = np.ones((1, n_locations))
        b_ub = np.array([amount])
        
        # Constraint: Allocations >= 0
        bounds = [(0, None) for _ in range(n_locations)]
        
        # Solve linear program
        result = linprog(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            bounds=bounds,
            method="highs",
        )
        
        if not result.success:
            logger.warning(f"Linear programming optimization failed: {result.message}")
            # Fall back to simple allocation
            return self._optimize_allocation(
                locations, predictions, resource_type, amount, resource_props
            )
        
        # Round to integers (ensuring sum <= amount)
        raw_allocation = result.x
        int_allocation = np.floor(raw_allocation).astype(int)
        
        # Distribute remainder based on fractional parts
        remainder = amount - int_allocation.sum()
        fractions = raw_allocation - int_allocation
        
        # Sort locations by fractional part (descending)
        sorted_indices = np.argsort(-fractions)
        
        # Create allocation dictionary
        allocation = {locations[i]: int_allocation[i] for i in range(n_locations)}
        
        # Distribute remainder
        for i in range(int(remainder)):
            if i < len(sorted_indices):
                idx = sorted_indices[i]
                allocation[locations[idx]] += 1
        
        return allocation


def allocate_resources(
    locations: List[str],
    resources: Dict[str, int],
    disaster_type: str = "flood",
) -> Dict[str, Any]:
    """
    Allocate resources across multiple locations.
    
    Args:
        locations (List[str]): List of affected locations
        resources (Dict[str, int]): Available resources (e.g., {"water": 1000})
        disaster_type (str): Type of disaster
    
    Returns:
        Dict[str, Any]: Allocation results
    """
    allocator = ResourceAllocator()
    return allocator.allocate(locations, resources, disaster_type) 