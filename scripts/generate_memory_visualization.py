#!/usr/bin/env python
"""
Memory visualization script for Jyra.

This script generates memory visualizations for a user, including
a memory graph, category distribution, importance histogram, and a comprehensive dashboard.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import jyra modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jyra.utils.logger import setup_logger
from jyra.ai.visualization.memory_visualizer import memory_visualizer
from jyra.db.models.user import User

# Set up logging
logger = setup_logger(__name__)


async def generate_visualizations(user_id: int, dashboard: bool = True):
    """
    Generate memory visualizations for a user.
    
    Args:
        user_id (int): User ID
        dashboard (bool): Whether to generate a comprehensive dashboard
    """
    try:
        # Check if user exists
        user = await User.get_user(user_id)
        if not user:
            print(f"Error: User {user_id} not found")
            return
        
        print(f"Generating memory visualizations for user {user_id}...")
        
        if dashboard:
            # Generate comprehensive dashboard
            dashboard_path = await memory_visualizer.generate_memory_dashboard(user_id)
            if dashboard_path:
                print(f"Memory dashboard generated: {dashboard_path}")
                print(f"Open this file in a web browser to view the dashboard.")
            else:
                print("Failed to generate memory dashboard")
        else:
            # Generate individual visualizations
            graph_path = await memory_visualizer.generate_memory_graph(user_id)
            if graph_path:
                print(f"Memory graph generated: {graph_path}")
            else:
                print("Failed to generate memory graph")
                
            category_path = await memory_visualizer.generate_category_distribution(user_id)
            if category_path:
                print(f"Category distribution generated: {category_path}")
            else:
                print("Failed to generate category distribution")
                
            importance_path = await memory_visualizer.generate_importance_histogram(user_id)
            if importance_path:
                print(f"Importance histogram generated: {importance_path}")
            else:
                print("Failed to generate importance histogram")
        
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate memory visualizations for a user")
    parser.add_argument("user_id", type=int, help="User ID")
    parser.add_argument("--no-dashboard", action="store_true", help="Generate individual visualizations instead of a dashboard")
    
    args = parser.parse_args()
    
    await generate_visualizations(args.user_id, dashboard=not args.no_dashboard)


if __name__ == "__main__":
    asyncio.run(main())
