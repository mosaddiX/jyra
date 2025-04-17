# Semantic Search Guide for Jyra Bot

This guide explains how to use the semantic search features in Jyra to find memories based on meaning rather than just keywords.

## What is Semantic Search?

Semantic search goes beyond simple keyword matching to understand the meaning and context of your query. This means you can find memories that are conceptually related to your search, even if they don't contain the exact words you're searching for.

For example, if you search for "vacation plans," semantic search might find memories about "holiday itinerary" or "travel arrangements" even if they don't contain the words "vacation" or "plans."

## Basic Semantic Search

The simplest way to use semantic search is with the `/search_memories` command:

```
/search_memories <query>
```

**Examples:**
- `/search_memories vacation plans`
- `/search_memories cooking recipes`
- `/search_memories work meetings`

By default, this command uses semantic search to find memories related to your query.

## Search Options

The `/search_memories` command supports several options to refine your search:

```
/search_memories <query> [options]
```

**Options:**
- `-c, --category <category>`: Filter by category
- `-i, --importance <1-5>`: Filter by minimum importance (1-5)
- `-t, --tags <tag1,tag2>`: Filter by tags (comma-separated)
- `-l, --limit <number>`: Maximum number of results (default: 5)
- `-k, --keyword`: Use keyword search instead of semantic search

**Examples:**
- `/search_memories vacation -c travel -i 3`
- `/search_memories recipes -t cooking,food -l 10`
- `/search_memories meeting notes -k`

To see all available options, use:
```
/search_memories --help
```

## Advanced Semantic Search

For more complex searches, use the `/advanced_search` command:

```
/advanced_search [options]
```

**Options:**
- `-q, --query <text>`: Search query text
- `-c, --category <category>`: Filter by category
- `-i, --importance <1-5>`: Filter by minimum importance (1-5)
- `-t, --tags <tag1,tag2>`: Filter by tags (comma-separated)
- `-d, --date <YYYY-MM-DD>`: Filter by date (memories created on or after)
- `-l, --limit <number>`: Maximum number of results (default: 10)
- `-s, --sort <field>`: Sort by field (importance, recency, confidence)
- `-k, --keyword`: Use keyword search instead of semantic search

**Examples:**
- `/advanced_search -q vacation plans -c travel -i 3`
- `/advanced_search -t work,meeting -d 2023-01-01 -s recency`
- `/advanced_search -c recipes -i 2 -l 20 -k`

To see all available options, use:
```
/advanced_search --help
```

## Understanding Search Results

Search results include several pieces of information:

1. **Content**: The text of the memory
2. **Category**: The category the memory belongs to
3. **Importance**: The importance level (1-5)
4. **Created**: When the memory was created
5. **Tags**: Any tags associated with the memory
6. **Similarity**: For semantic searches, how closely the memory matches your query
7. **Match**: A visual representation of the similarity (★★★☆☆)

The similarity score ranges from 0 to 1, with higher values indicating a closer match to your query.

## Tips for Effective Semantic Search

1. **Be specific**: More specific queries generally yield better results
2. **Try different phrasings**: If you don't get the results you want, try rephrasing your query
3. **Use filters**: Combine semantic search with category, tag, or importance filters
4. **Compare with keyword search**: If semantic search isn't finding what you want, try using the `-k` flag for keyword search
5. **Generate embeddings**: If you've added many memories, run `/generate_embeddings` to ensure all memories have embeddings for semantic search

## Generating Embeddings

For semantic search to work effectively, your memories need embeddings (vector representations). These are usually generated automatically when memories are created, but if you've imported memories or are experiencing issues with semantic search, you can generate embeddings for all memories with:

```
/generate_embeddings
```

This process may take some time depending on how many memories you have.

## Troubleshooting

If you're having issues with semantic search:

1. **No results**: Try broadening your search or using different keywords
2. **Irrelevant results**: Try being more specific or using filters
3. **Missing memories**: Make sure all memories have embeddings by running `/generate_embeddings`
4. **Error messages**: If you see error messages, try again later or report the issue

## Advanced Features

### Combining Search Methods

You can combine semantic search with traditional filters for powerful queries:

```
/advanced_search -q "cooking" -c recipes -t vegetarian,dinner -i 3 -s importance
```

This searches for memories semantically related to "cooking" that are in the "recipes" category, have the tags "vegetarian" and "dinner", have an importance of at least 3, and are sorted by importance.

### Date-Based Filtering

Find memories created after a specific date:

```
/advanced_search -q "project ideas" -d 2023-06-01
```

This finds memories related to "project ideas" created on or after June 1, 2023.

### Sorting Options

Sort your search results in different ways:

- **importance**: Sort by importance level (default)
- **recency**: Sort by when the memory was last accessed
- **confidence**: Sort by confidence level
- **recall_count**: Sort by how often the memory has been recalled

Example:
```
/advanced_search -c work -s recency
```

This finds memories in the "work" category, sorted by most recently accessed.

## Future Enhancements

We're continuously improving the semantic search capabilities. Future updates may include:

- Semantic clustering of related memories
- Natural language queries
- Multi-language support
- Improved similarity algorithms
- Search within search results
