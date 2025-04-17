# Memory Consolidation Guide for Jyra Bot

This guide explains how to use the advanced memory consolidation features in Jyra bot.

## Overview

Jyra now includes sophisticated memory consolidation capabilities that allow you to:

1. Automatically identify groups of related memories
2. Combine similar memories into more comprehensive ones
3. Maintain relationships between original and consolidated memories
4. Improve the organization and quality of your knowledge base

## How Memory Consolidation Works

Memory consolidation uses semantic clustering to identify groups of memories that are related by meaning, not just keywords. When memories are consolidated:

1. The original memories are preserved but marked as consolidated
2. A new, more comprehensive memory is created that combines the information
3. Relationships are maintained between original and consolidated memories
4. The consolidated memory inherits tags and categories from the original memories

## Commands

### Show Consolidation Candidates

```
/show_consolidation_candidates [min_similarity]
```

This command analyzes your memories and shows groups that are candidates for consolidation.

**Parameters:**
- `min_similarity`: Minimum similarity threshold (0.5-0.95, default: 0.75)

**Examples:**
- `/show_consolidation_candidates` - Show candidates with default similarity threshold
- `/show_consolidation_candidates 0.8` - Show candidates with higher similarity threshold

### Consolidate Memories

```
/consolidate_memories [max_consolidations]
```

This command automatically consolidates groups of related memories.

**Parameters:**
- `max_consolidations`: Maximum number of consolidations to perform (1-10, default: 3)

**Examples:**
- `/consolidate_memories` - Consolidate memories with default settings
- `/consolidate_memories 5` - Consolidate up to 5 groups of memories

## Benefits of Memory Consolidation

### Improved Knowledge Organization
- Reduces redundancy and duplication in your memory base
- Creates more comprehensive and coherent memories
- Makes it easier to find and recall information

### Enhanced Recall
- Consolidated memories are more likely to be retrieved when relevant
- Related information is kept together, providing better context
- Important details from multiple memories are preserved in one place

### Better Memory Quality
- Consolidated memories have higher importance scores
- They combine the best aspects of multiple memories
- They provide more comprehensive answers to questions

## When to Use Memory Consolidation

Memory consolidation is most useful when:

1. You have many memories on similar topics
2. You've collected information about the same subject over time
3. You want to organize and streamline your knowledge base
4. You notice redundancy or fragmentation in your memories

## Tips for Effective Consolidation

1. **Start with a higher similarity threshold** (0.8+) for your first consolidations to ensure only very similar memories are combined
2. **Review the candidates** before consolidating to make sure they're truly related
3. **Consolidate in small batches** (3-5 groups at a time) to better control the process
4. **Use visualization** after consolidation to see how your memory network has improved
5. **Periodically run consolidation** as you add new memories to keep your knowledge base organized

## Advanced Usage

### Combining with Visualization

After consolidating memories, use the visualization commands to see how your memory network has improved:

```
/visualize_memories
```

This will show you how consolidation has affected the structure of your memory network.

### Manual Review and Editing

After automatic consolidation, you may want to:

1. Review the consolidated memories to ensure they're accurate
2. Add any missing details that might have been lost
3. Adjust importance levels if needed
4. Add additional tags to improve retrievability

## Troubleshooting

If you encounter issues with memory consolidation:

1. **No candidates found**: You may not have enough related memories, or they may not be similar enough
2. **Poor quality consolidations**: Try increasing the similarity threshold
3. **Too many consolidations at once**: Reduce the max_consolidations parameter
4. **Important information missing**: Review and edit consolidated memories manually

## Next Steps

After consolidating your memories, consider:

1. **Adding new memories** to fill gaps in your knowledge
2. **Using semantic search** to find and retrieve your consolidated memories
3. **Visualizing your memory network** to see the improved structure
4. **Setting up regular consolidation** as part of your memory maintenance routine
