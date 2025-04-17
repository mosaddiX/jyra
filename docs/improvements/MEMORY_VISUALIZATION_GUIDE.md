# Memory Visualization Guide for Jyra Bot

This guide explains how to use the memory visualization features in Jyra bot.

## Overview

Jyra now includes powerful memory visualization features that allow you to:

1. View your memories as an interactive network graph
2. See relationships between memories based on semantic similarity
3. Visualize connections between memories, tags, and categories


## Commands

### Basic Visualization

```
/visualize_memories [max_memories] [min_importance]
```

This command generates a visualization of your memories and sends it as an image in the chat.

**Parameters:**
- `max_memories`: Maximum number of memories to include (default: 30)
- `min_importance`: Minimum importance level for memories (default: 1)

**Examples:**
- `/visualize_memories` - Generate visualization with default settings
- `/visualize_memories 20` - Generate visualization with max 20 memories
- `/visualize_memories 20 2` - Generate visualization with max 20 memories and min importance 2

After generating the visualization, you'll see buttons that allow you to customize the view:
- **More Memories**: Increases the number of memories shown
- **Higher Similarity**: Shows only stronger connections between memories
- **Tags Only**: Shows only tag relationships
- **Categories Only**: Shows only category relationships



## Understanding the Visualization

### Node Types

The visualization uses different shapes and colors to represent different types of nodes:

- **Blue Circles**: Individual memories
- **Green Squares**: Tags
- **Red Hexagons**: Categories

### Connection Types

Different line styles represent different types of connections:

- **Blue Dashed Lines**: Semantic similarity between memories
- **Green Solid Lines**: Memory-to-tag connections
- **Red Solid Lines**: Memory-to-category connections

### Interpreting the Graph

- **Clusters**: Groups of closely connected memories often represent related concepts or topics
- **Central Nodes**: Memories with many connections are often key concepts in your knowledge base
- **Isolated Nodes**: Memories with few connections may be unique or unrelated to other memories

## Tips for Effective Visualization

1. **Start Small**: Begin with a small number of memories (10-20) to understand the structure
2. **Filter by Importance**: Use the min_importance parameter to focus on your most important memories
3. **Look for Patterns**: Identify clusters and central nodes to understand your memory structure

4. **Generate Regularly**: As you add more memories, generate new visualizations to see how your knowledge evolves

## Troubleshooting

If you encounter issues with the visualization:

1. **Empty Visualization**: Make sure you have memories stored (use `/remember` to create memories)
2. **Slow Generation**: Large numbers of memories may take longer to visualize
3. **Cluttered Graph**: Try increasing the similarity threshold or reducing the number of memories

## Next Steps

After exploring your memory visualizations, you might want to:

1. **Add More Structured Memories**: Use categories and tags consistently
2. **Remove Redundant Memories**: Delete duplicate or low-value memories
3. **Consolidate Related Memories**: Combine related memories into more comprehensive ones
4. **Create Topic-Specific Visualizations**: Use category filters to focus on specific topics
