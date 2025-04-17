# Memory Decay Guide for Jyra Bot

This guide explains how to use the memory decay features in Jyra bot.

## Overview

Jyra now includes memory decay capabilities that allow you to:

1. Automatically reduce the importance of older, less accessed memories
2. Maintain a more relevant and focused memory base
3. Prioritize recent and frequently accessed information
4. Simulate the natural forgetting process of human memory

## How Memory Decay Works

Memory decay gradually reduces the importance of memories based on:

1. **Age**: Older memories are more likely to decay
2. **Access Frequency**: Rarely accessed memories decay faster
3. **Importance**: Only memories above a minimum importance threshold are considered for decay
4. **Consolidation Status**: Consolidated memories are protected from decay

When a memory decays:
- Its importance level is reduced by a configurable factor
- Its context is updated to record the decay
- The original content remains unchanged

## Commands

### Show Decay Candidates

```
/show_decay_candidates [min_age_days]
```

This command analyzes your memories and shows which ones are candidates for decay.

**Parameters:**
- `min_age_days`: Minimum age in days for memories to be considered (default: 30)

**Examples:**
- `/show_decay_candidates` - Show candidates with default age threshold
- `/show_decay_candidates 60` - Show candidates older than 60 days

### Apply Decay

```
/decay_memories [decay_factor] [min_age_days]
```

This command applies decay to eligible memories.

**Parameters:**
- `decay_factor`: Factor to multiply importance by (0.5-0.95, default: 0.9)
- `min_age_days`: Minimum age in days for memories to be considered (default: 30)

**Examples:**
- `/decay_memories` - Apply decay with default settings
- `/decay_memories 0.8` - Apply stronger decay (lower importance)
- `/decay_memories 0.8 60` - Apply stronger decay to memories older than 60 days

## Benefits of Memory Decay

### More Relevant Memory Base
- Focuses attention on recent and important memories
- Reduces noise from old, less relevant information
- Improves the quality of memory retrieval

### Better Resource Management
- Prevents memory overload
- Prioritizes important information
- Maintains a balanced knowledge base

### More Human-Like Memory
- Simulates natural forgetting processes
- Emphasizes frequently accessed information
- Creates a more dynamic memory system

## When to Use Memory Decay

Memory decay is most useful when:

1. You have accumulated many memories over time
2. You notice older, less relevant memories appearing in responses
3. You want to focus on more recent or important information
4. Your memory base has become cluttered with low-value information

## Tips for Effective Decay

1. **Start with a gentle decay factor** (0.9) to avoid losing too much information at once
2. **Review decay candidates** before applying decay to ensure you're not losing valuable information
3. **Use longer min_age_days** (60+) for memories you want to preserve longer
4. **Apply decay periodically** rather than all at once
5. **Combine with consolidation** to preserve important information from older memories

## Automatic Decay

Jyra includes an automatic decay process that runs during scheduled memory maintenance. This process:

1. Applies a gentle decay (0.9 factor) to memories older than 30 days
2. Limits decay to 5 memories per user per maintenance run
3. Prioritizes the oldest and least accessed memories
4. Protects consolidated memories from decay

You don't need to do anything to enable this feature - it runs automatically in the background.

## Recovering from Decay

If you find that an important memory has decayed too much:

1. Access the memory more frequently to prevent further decay
2. Manually increase its importance using the memory management features
3. Create a new memory with the same information but higher importance
4. Consolidate it with other related memories to protect it from future decay

## Troubleshooting

If you encounter issues with memory decay:

1. **No decay candidates**: Your memories may be too recent or already at minimum importance
2. **Too aggressive decay**: Increase the decay factor (closer to 1.0)
3. **Too gentle decay**: Decrease the decay factor (closer to 0.5)
4. **Important memories decaying**: Increase the min_importance parameter or access them more frequently

## Next Steps

After implementing memory decay, consider:

1. **Reviewing your memory base** to see the effects of decay
2. **Consolidating important memories** to protect them from decay
3. **Creating a memory maintenance routine** that includes both consolidation and decay
4. **Adjusting decay parameters** based on your specific needs and memory usage patterns
