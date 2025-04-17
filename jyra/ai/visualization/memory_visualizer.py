"""
Memory visualization module for Jyra.

This module provides functionality to visualize memories and their relationships.
"""

import os
import io
import json
import asyncio
import matplotlib.pyplot as plt
import matplotlib
import networkx as nx
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import tempfile
import uuid
from pathlib import Path

from jyra.db.models.memory import Memory
from jyra.ai.embeddings.vector_db import vector_db
from jyra.utils.logger import setup_logger

# Use Agg backend for matplotlib (non-interactive, good for server environments)
matplotlib.use('Agg')

logger = setup_logger(__name__)

# Directory for storing visualization images and web files
VISUALIZATION_DIR = Path('data/visualizations')
WEB_DIR = Path('data/web')

# Ensure directories exist
VISUALIZATION_DIR.mkdir(exist_ok=True, parents=True)
WEB_DIR.mkdir(exist_ok=True, parents=True)


class MemoryVisualizer:
    """
    Class for visualizing memories and their relationships.
    """

    def __init__(self):
        """
        Initialize the memory visualizer.
        """
        logger.info("Initializing memory visualizer")

    async def generate_memory_graph(self, user_id: int,
                                    max_memories: int = 30,
                                    min_importance: int = 1,
                                    include_tags: bool = True,
                                    include_categories: bool = True,
                                    similarity_threshold: float = 0.6) -> str:
        """
        Generate a graph visualization of memories.

        Args:
            user_id (int): User ID
            max_memories (int): Maximum number of memories to include
            min_importance (int): Minimum importance level for memories
            include_tags (bool): Whether to include tag relationships
            include_categories (bool): Whether to include category relationships
            similarity_threshold (float): Threshold for semantic similarity connections

        Returns:
            str: Path to the generated visualization image
        """
        try:
            # Get memories for the user
            memories = await Memory.get_memories(
                user_id=user_id,
                min_importance=min_importance,
                limit=max_memories,
                sort_by="importance"
            )

            if not memories:
                logger.warning(f"No memories found for user {user_id}")
                return self._generate_empty_graph(user_id)

            # Create a graph
            G = nx.Graph()

            # Add memory nodes
            for memory in memories:
                G.add_node(f"m_{memory.memory_id}",
                           type="memory",
                           label=memory.content[:30] + "..." if len(
                               memory.content) > 30 else memory.content,
                           importance=memory.importance,
                           category=memory.category,
                           created_at=memory.created_at)

            # Add tag nodes and edges if requested
            if include_tags:
                for memory in memories:
                    if memory.tags:
                        for tag in memory.tags:
                            tag_node = f"t_{tag}"
                            if tag_node not in G:
                                G.add_node(tag_node, type="tag",
                                           label=f"#{tag}")
                            G.add_edge(f"m_{memory.memory_id}",
                                       tag_node, type="has_tag")

            # Add category nodes and edges if requested
            if include_categories:
                for memory in memories:
                    if memory.category:
                        category_node = f"c_{memory.category}"
                        if category_node not in G:
                            G.add_node(category_node, type="category",
                                       label=memory.category)
                        G.add_edge(f"m_{memory.memory_id}",
                                   category_node, type="has_category")

            # Add semantic similarity edges
            await self._add_similarity_edges(G, memories, similarity_threshold)

            # Generate the visualization
            return await self._visualize_graph(G, user_id)

        except Exception as e:
            logger.error(f"Error generating memory graph: {str(e)}")
            return self._generate_empty_graph(user_id)

    async def _add_similarity_edges(self, G: nx.Graph, memories: List[Memory],
                                    similarity_threshold: float) -> None:
        """
        Add edges between semantically similar memories.

        Args:
            G (nx.Graph): The graph to add edges to
            memories (List[Memory]): List of memories
            similarity_threshold (float): Threshold for semantic similarity
        """
        try:
            # Get memory IDs
            memory_ids = [memory.memory_id for memory in memories]

            # Get embeddings for all memories
            embeddings = {}
            for memory_id in memory_ids:
                embedding = await vector_db.get_embedding(memory_id)
                if embedding:
                    embeddings[memory_id] = embedding

            # Calculate similarities between all pairs of memories
            for i, memory_id1 in enumerate(memory_ids):
                if memory_id1 not in embeddings:
                    continue

                for memory_id2 in memory_ids[i+1:]:
                    if memory_id2 not in embeddings:
                        continue

                    similarity = vector_db.calculate_similarity(
                        embeddings[memory_id1],
                        embeddings[memory_id2]
                    )

                    if similarity >= similarity_threshold:
                        G.add_edge(f"m_{memory_id1}", f"m_{memory_id2}",
                                   type="similar",
                                   weight=similarity)

        except Exception as e:
            logger.error(f"Error adding similarity edges: {str(e)}")

    async def _visualize_graph(self, G: nx.Graph, user_id: int) -> str:
        """
        Create a visualization of the memory graph.

        Args:
            G (nx.Graph): The graph to visualize
            user_id (int): User ID

        Returns:
            str: Path to the generated visualization image
        """
        try:
            # Create a unique filename
            filename = f"memory_graph_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(VISUALIZATION_DIR, filename)

            # Set up the figure
            plt.figure(figsize=(12, 10))

            # Get node types
            memory_nodes = [n for n, d in G.nodes(
                data=True) if d.get('type') == 'memory']
            tag_nodes = [n for n, d in G.nodes(
                data=True) if d.get('type') == 'tag']
            category_nodes = [n for n, d in G.nodes(
                data=True) if d.get('type') == 'category']

            # Get edge types
            similarity_edges = [(u, v) for u, v, d in G.edges(
                data=True) if d.get('type') == 'similar']
            tag_edges = [(u, v) for u, v, d in G.edges(
                data=True) if d.get('type') == 'has_tag']
            category_edges = [(u, v) for u, v, d in G.edges(
                data=True) if d.get('type') == 'has_category']

            # Use a layout that spreads nodes apart
            pos = nx.spring_layout(G, k=0.3, iterations=50)

            # Draw nodes
            nx.draw_networkx_nodes(G, pos, nodelist=memory_nodes, node_color='skyblue',
                                   node_size=500, alpha=0.8)
            nx.draw_networkx_nodes(G, pos, nodelist=tag_nodes, node_color='lightgreen',
                                   node_size=300, alpha=0.8, node_shape='s')
            nx.draw_networkx_nodes(G, pos, nodelist=category_nodes, node_color='salmon',
                                   node_size=400, alpha=0.8, node_shape='h')

            # Draw edges
            nx.draw_networkx_edges(G, pos, edgelist=similarity_edges, width=2, alpha=0.5,
                                   edge_color='blue', style='dashed')
            nx.draw_networkx_edges(G, pos, edgelist=tag_edges, width=1, alpha=0.7,
                                   edge_color='green')
            nx.draw_networkx_edges(G, pos, edgelist=category_edges, width=1, alpha=0.7,
                                   edge_color='red')

            # Draw labels
            labels = {n: d.get('label', n) for n, d in G.nodes(data=True)}
            nx.draw_networkx_labels(
                G, pos, labels=labels, font_size=8, font_family='sans-serif')

            # Add a title and legend
            plt.title(f"Memory Network for User {user_id}")

            # Add a legend
            memory_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='skyblue',
                                      markersize=10, label='Memory')
            tag_patch = plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='lightgreen',
                                   markersize=10, label='Tag')
            category_patch = plt.Line2D([0], [0], marker='h', color='w', markerfacecolor='salmon',
                                        markersize=10, label='Category')
            similarity_line = plt.Line2D([0], [0], color='blue', lw=2, ls='--',
                                         label='Semantic Similarity')
            tag_line = plt.Line2D([0], [0], color='green', lw=1,
                                  label='Has Tag')
            category_line = plt.Line2D([0], [0], color='red', lw=1,
                                       label='Has Category')

            plt.legend(handles=[memory_patch, tag_patch, category_patch,
                                similarity_line, tag_line, category_line],
                       loc='upper right')

            # Remove axis
            plt.axis('off')

            # Save the figure
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(
                f"Generated memory graph for user {user_id}: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error visualizing graph: {str(e)}")
            return self._generate_empty_graph(user_id)

    def _generate_empty_graph(self, user_id: int) -> str:
        """
        Generate an empty graph when no memories are found.

        Args:
            user_id (int): User ID

        Returns:
            str: Path to the generated visualization image
        """
        try:
            # Create a unique filename
            filename = f"empty_graph_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(VISUALIZATION_DIR, filename)

            # Create a simple figure
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, "No memories found or not enough data to visualize",
                     horizontalalignment='center', verticalalignment='center',
                     fontsize=14, color='gray')
            plt.axis('off')

            # Save the figure
            plt.savefig(filepath, dpi=100)
            plt.close()

            return filepath

        except Exception as e:
            logger.error(f"Error generating empty graph: {str(e)}")
            # Return a default path if all else fails
            return os.path.join(VISUALIZATION_DIR, "error.png")

    async def generate_category_distribution(self, user_id: int) -> Optional[str]:
        """
        Generate a pie chart showing the distribution of memories by category.

        Args:
            user_id (int): User ID

        Returns:
            Optional[str]: Path to the generated image file, or None if failed
        """
        try:
            # Get all memories for the user
            memories = await Memory.get_memories(
                user_id=user_id,
                limit=1000  # Get a large number to ensure we get all categories
            )

            if not memories:
                logger.warning(f"No memories found for user {user_id}")
                return self._generate_empty_graph(user_id)

            # Count memories by category
            category_counts = {}
            for memory in memories:
                category = memory.category or "uncategorized"
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1

            # Create a timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"category_distribution_{user_id}_{timestamp}.png"
            filepath = VISUALIZATION_DIR / filename

            # Create the pie chart
            plt.figure(figsize=(10, 8))

            # Sort categories by count
            sorted_categories = sorted(
                category_counts.items(), key=lambda x: x[1], reverse=True)
            labels = [f"{cat} ({count})" for cat, count in sorted_categories]
            sizes = [count for _, count in sorted_categories]

            # Use a colorful colormap
            colors = plt.cm.tab20.colors[:len(labels)]

            # Create the pie chart
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                    shadow=True, startangle=140, textprops={'fontsize': 9})

            # Equal aspect ratio ensures that pie is drawn as a circle
            plt.axis('equal')

            # Add a title
            plt.title(f"Memory Categories for User {user_id}")

            # Save the figure
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(
                f"Generated category distribution for user {user_id}: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error generating category distribution: {str(e)}")
            return self._generate_empty_graph(user_id)

    async def generate_importance_histogram(self, user_id: int) -> Optional[str]:
        """
        Generate a histogram showing the distribution of memory importance.

        Args:
            user_id (int): User ID

        Returns:
            Optional[str]: Path to the generated image file, or None if failed
        """
        try:
            # Get all memories for the user
            memories = await Memory.get_memories(
                user_id=user_id,
                limit=1000
            )

            if not memories:
                logger.warning(f"No memories found for user {user_id}")
                return self._generate_empty_graph(user_id)

            # Extract importance values
            importance_values = [memory.importance for memory in memories]

            # Create a timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"importance_histogram_{user_id}_{timestamp}.png"
            filepath = VISUALIZATION_DIR / filename

            # Create the histogram
            plt.figure(figsize=(10, 6))

            # Create bins from 1 to 10
            bins = range(1, 12)

            # Plot the histogram
            plt.hist(importance_values, bins=bins, alpha=0.7,
                     color='skyblue', edgecolor='black')

            # Add labels and title
            plt.xlabel('Importance Level')
            plt.ylabel('Number of Memories')
            plt.title(f'Memory Importance Distribution for User {user_id}')

            # Set x-axis ticks
            plt.xticks(range(1, 11))

            # Add grid
            plt.grid(axis='y', alpha=0.75, linestyle='--')

            # Save the figure
            plt.tight_layout()
            plt.savefig(filepath, dpi=150)
            plt.close()

            logger.info(
                f"Generated importance histogram for user {user_id}: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error generating importance histogram: {str(e)}")
            return self._generate_empty_graph(user_id)

    async def generate_memory_dashboard(self, user_id: int) -> Optional[str]:
        """
        Generate a comprehensive memory dashboard with multiple visualizations.

        Args:
            user_id (int): User ID

        Returns:
            Optional[str]: Path to the generated HTML file, or None if failed
        """
        try:
            # Generate all visualizations
            graph_path = await self.generate_memory_graph(user_id)
            category_path = await self.generate_category_distribution(user_id)
            importance_path = await self.generate_importance_histogram(user_id)

            # Get memory statistics
            memories = await Memory.get_memories(user_id=user_id, limit=1000)

            if not memories:
                logger.warning(f"No memories found for user {user_id}")
                return None

            # Calculate statistics
            total_memories = len(memories)
            avg_importance = sum(m.importance for m in memories) / \
                total_memories if total_memories > 0 else 0
            categories = {}
            for memory in memories:
                category = memory.category or "uncategorized"
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1

            # Create a timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"memory_visualization_{user_id}_{timestamp}.html"
            filepath = WEB_DIR / filename

            # Create relative paths for images
            graph_rel_path = os.path.relpath(
                graph_path, start=WEB_DIR.parent) if graph_path else ""
            category_rel_path = os.path.relpath(
                category_path, start=WEB_DIR.parent) if category_path else ""
            importance_rel_path = os.path.relpath(
                importance_path, start=WEB_DIR.parent) if importance_path else ""

            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Memory Dashboard for User {user_id}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    }}
                    h1, h2 {{
                        color: #333;
                    }}
                    .stats {{
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 20px;
                    }}
                    .stat-card {{
                        background-color: #f9f9f9;
                        padding: 15px;
                        border-radius: 5px;
                        width: 30%;
                        box-shadow: 0 0 5px rgba(0,0,0,0.05);
                    }}
                    .stat-value {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #0066cc;
                    }}
                    .visualizations {{
                        display: flex;
                        flex-wrap: wrap;
                        justify-content: space-between;
                    }}
                    .viz-container {{
                        width: 48%;
                        margin-bottom: 20px;
                        background-color: white;
                        padding: 15px;
                        border-radius: 5px;
                        box-shadow: 0 0 5px rgba(0,0,0,0.05);
                    }}
                    .full-width {{
                        width: 100%;
                    }}
                    img {{
                        max-width: 100%;
                        height: auto;
                        display: block;
                        margin: 0 auto;
                    }}
                    .category-list {{
                        column-count: 2;
                    }}
                    .timestamp {{
                        text-align: right;
                        color: #999;
                        font-size: 12px;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Memory Dashboard for User {user_id}</h1>

                    <div class="stats">
                        <div class="stat-card">
                            <h3>Total Memories</h3>
                            <div class="stat-value">{total_memories}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Average Importance</h3>
                            <div class="stat-value">{avg_importance:.1f}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Categories</h3>
                            <div class="stat-value">{len(categories)}</div>
                        </div>
                    </div>

                    <div class="visualizations">
                        <div class="viz-container full-width">
                            <h2>Memory Network</h2>
                            <p>This graph shows how memories are connected by category. Larger nodes represent more important memories.</p>
                            <img src="../{graph_rel_path}" alt="Memory Network Graph">
                        </div>

                        <div class="viz-container">
                            <h2>Category Distribution</h2>
                            <p>Distribution of memories across different categories.</p>
                            <img src="../{category_rel_path}" alt="Category Distribution">
                        </div>

                        <div class="viz-container">
                            <h2>Importance Distribution</h2>
                            <p>Distribution of memory importance levels.</p>
                            <img src="../{importance_rel_path}" alt="Importance Histogram">
                        </div>

                        <div class="viz-container full-width">
                            <h2>Category Breakdown</h2>
                            <p>Number of memories in each category:</p>
                            <div class="category-list">
                                <ul>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div class="timestamp">
                        Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    </div>
                </div>
            </body>
            </html>
            """

            # Add category list items
            category_items = ""
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                category_items += f"<li><strong>{cat}</strong>: {count} memories</li>\n"

            # Insert the category items into the HTML at the right position
            html_content = html_content.replace(
                "</ul>", f"{category_items}</ul>")

            # Write HTML to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(
                f"Generated memory dashboard for user {user_id}: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error generating memory dashboard: {str(e)}")
            return None


# Create a singleton instance
memory_visualizer = MemoryVisualizer()
