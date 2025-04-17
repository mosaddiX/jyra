"""
Improved search functionality for Jyra bot.

This module provides enhanced search capabilities for memories,
including both semantic and keyword search with various filtering options.
"""

import re
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes

from jyra.db.models.memory import Memory
from jyra.ai.embeddings.embedding_generator import embedding_generator
from jyra.ai.embeddings.vector_db import vector_db
from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def improved_search_memories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Search memories using both semantic and keyword search with enhanced options.

    Usage:
    /search_memories <query> [options]

    Options:
    -c, --category <category>: Filter by category
    -i, --importance <1-5>: Filter by minimum importance (1-5)
    -t, --tags <tag1,tag2>: Filter by tags (comma-separated)
    -l, --limit <number>: Maximum number of results (default: 5)
    -k, --keyword: Use keyword search instead of semantic search
    -d, --date <YYYY-MM-DD>: Filter by date (memories created on or after)
    -s, --sort <field>: Sort by field (importance, recency, confidence, recall_count)
    -b, --both: Use both semantic and keyword search

    Examples:
    /search_memories vacation plans
    /search_memories cooking -c recipes -i 3
    /search_memories books -t fiction,reading -l 10
    /search_memories meeting notes -k
    /search_memories jyoti -b
    """
    user_id = update.effective_user.id

    # Parse arguments and options
    args = context.args

    if not args:
        await update.message.reply_text(
            "Please provide a search query. Use /search_memories <query> [options]\n\n"
            "For help with options, use /search_memories --help")
        return

    # Check if user is asking for help
    if args[0] in ["--help", "-h", "help"]:
        help_text = (
            "🔍 *Search Memories Help*\n\n"
            "*Usage:*\n"
            "`/search_memories <query> [options]`\n\n"
            "*Options:*\n"
            "`-c, --category <category>`: Filter by category\n"
            "`-i, --importance <1-5>`: Filter by minimum importance\n"
            "`-t, --tags <tag1,tag2>`: Filter by tags (comma-separated)\n"
            "`-l, --limit <number>`: Maximum number of results (default: 5)\n"
            "`-k, --keyword`: Use keyword search instead of semantic search\n"
            "`-d, --date <YYYY-MM-DD>`: Filter by date (on or after)\n"
            "`-s, --sort <field>`: Sort by field (importance, recency, confidence, recall_count)\n"
            "`-b, --both`: Use both semantic and keyword search\n\n"
            "*Examples:*\n"
            "`/search_memories vacation plans`\n"
            "`/search_memories cooking -c recipes -i 3`\n"
            "`/search_memories books -t fiction,reading -l 10`\n"
            "`/search_memories meeting notes -k`\n"
            "`/search_memories jyoti -b`"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return

    # Initialize default values
    query = []
    category = None
    min_importance = 1
    tags = None
    date_filter = None
    limit = 5
    sort_by = "importance"
    use_semantic = True
    use_keyword = False

    # Parse arguments
    i = 0
    while i < len(args):
        if args[i].startswith("-"):
            option = args[i].lower()

            # Handle options that require a value
            if option in ["-c", "--category"] and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            elif option in ["-i", "--importance"] and i + 1 < len(args):
                try:
                    min_importance = int(args[i + 1])
                    if not 1 <= min_importance <= 5:
                        raise ValueError("Importance must be between 1 and 5")
                    i += 2
                except ValueError:
                    await update.message.reply_text(f"Invalid importance value: {args[i + 1]}. Must be a number between 1 and 5.")
                    return
            elif option in ["-t", "--tags"] and i + 1 < len(args):
                tags = args[i + 1].split(",")
                i += 2
            elif option in ["-l", "--limit"] and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                    if limit < 1:
                        raise ValueError("Limit must be at least 1")
                    i += 2
                except ValueError:
                    await update.message.reply_text(f"Invalid limit value: {args[i + 1]}. Must be a positive number.")
                    return
            elif option in ["-d", "--date"] and i + 1 < len(args):
                date_str = args[i + 1]
                # Validate date format (YYYY-MM-DD)
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    await update.message.reply_text(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")
                    return
                date_filter = date_str
                i += 2
            elif option in ["-s", "--sort"] and i + 1 < len(args):
                sort_option = args[i + 1].lower()
                if sort_option in ["importance", "recency", "confidence", "recall_count"]:
                    sort_by = sort_option
                    i += 2
                else:
                    await update.message.reply_text(
                        f"Invalid sort option: {args[i + 1]}. Valid options are: importance, recency, confidence, recall_count.")
                    return
            # Handle flags
            elif option in ["-k", "--keyword"]:
                use_semantic = False
                use_keyword = True
                i += 1
            elif option in ["-b", "--both"]:
                use_semantic = True
                use_keyword = True
                i += 1
            else:
                # Unknown option, treat as part of the query
                query.append(args[i])
                i += 1
        else:
            # Not an option, add to query
            query.append(args[i])
            i += 1

    # Join the query parts
    query_text = " ".join(query)

    if not query_text:
        await update.message.reply_text("Please provide a search query.")
        return

    # Send a message to indicate the search has started
    search_type = "keyword" if not use_semantic else "semantic"
    if use_keyword and use_semantic:
        search_type = "semantic and keyword"

    message = await update.message.reply_text(
        f"🔍 Searching memories for: *{query_text}*...\n\n"
        f"Using {search_type} search"
        f"{' with category: ' + category if category else ''}"
        f"{' and min importance: ' + str(min_importance) if min_importance > 1 else ''}"
        f"{' and tags: ' + ', '.join(tags) if tags else ''}"
        f"{' from date: ' + date_filter if date_filter else ''}",
        parse_mode="Markdown"
    )

    try:
        # Build SQL query conditions for direct database access
        conditions = ["m.user_id = ?"]
        params = [user_id]

        # Log the user ID for debugging
        logger.info(f"Searching memories for user ID: {user_id}")

        if min_importance > 1:
            conditions.append("m.importance >= ?")
            params.append(min_importance)

        if category:
            conditions.append("m.category = ?")
            params.append(category)

        if date_filter:
            conditions.append("m.created_at >= ?")
            params.append(date_filter)

        # Get memories with the specified filters
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()

        # Start building the query
        query_sql = """SELECT m.memory_id, m.user_id, m.content, m.category, m.importance,
                       m.source, m.context, m.last_accessed, m.created_at, m.confidence,
                       m.expires_at, m.recall_count, m.last_reinforced, m.is_consolidated
                       FROM memories m"""

        # Add tag filtering if specified
        if tags and len(tags) > 0:
            query_sql += """ JOIN memory_tag_associations mta ON m.memory_id = mta.memory_id
                           JOIN memory_tags mt ON mta.tag_id = mt.tag_id"""
            conditions.append(
                f"mt.tag_name IN ({', '.join(['?'] * len(tags))})")
            params.extend(tags)

        # Add WHERE clause
        if conditions:
            query_sql += " WHERE " + " AND ".join(conditions)

        # Add keyword search if requested
        if use_keyword and query_text:
            if conditions:
                query_sql += " AND "
            else:
                query_sql += " WHERE "
            query_sql += "m.content LIKE ?"
            params.append(f"%{query_text}%")

        # Add GROUP BY if using tags to ensure all tags are matched
        if tags and len(tags) > 0:
            query_sql += " GROUP BY m.memory_id HAVING COUNT(DISTINCT mt.tag_name) = ?"
            params.append(len(tags))

        # Add sorting
        if sort_by == "recency":
            query_sql += " ORDER BY m.last_accessed DESC"
        elif sort_by == "confidence":
            query_sql += " ORDER BY m.confidence DESC, m.importance DESC"
        elif sort_by == "recall_count":
            query_sql += " ORDER BY m.recall_count DESC, m.importance DESC"
        else:  # Default to importance
            query_sql += " ORDER BY m.importance DESC, m.last_accessed DESC"

        # Add limit - get more to allow for semantic filtering
        query_sql += " LIMIT ?"
        params.append(100)  # Get more to allow for semantic filtering

        # Execute the query
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()

        # Get tags for each memory
        memory_tags = {}
        if rows:
            memory_ids = [row["memory_id"] for row in rows]
            placeholders = ", ".join(["?" for _ in memory_ids])
            tag_query = f"""
                SELECT mta.memory_id, mt.tag_name
                FROM memory_tag_associations mta
                JOIN memory_tags mt ON mta.tag_id = mt.tag_id
                WHERE mta.memory_id IN ({placeholders})
            """
            cursor.execute(tag_query, memory_ids)
            tag_rows = cursor.fetchall()

            for memory_id, tag_name in tag_rows:
                if memory_id not in memory_tags:
                    memory_tags[memory_id] = []
                memory_tags[memory_id].append(tag_name)

        # Convert to Memory objects
        filtered_memories = []
        for row in rows:
            memory_dict = dict(row)
            memory_dict["tags"] = memory_tags.get(memory_dict["memory_id"], [])
            memory_dict["is_consolidated"] = bool(
                memory_dict["is_consolidated"])
            filtered_memories.append(memory_dict)

        # Apply semantic search if requested
        if use_semantic and query_text and filtered_memories:
            try:
                # Generate embedding for the query
                query_embedding = await embedding_generator.generate_embedding(query_text)

                # Calculate similarity for each memory
                for memory in filtered_memories:
                    # Get or generate embedding for the memory
                    memory_embedding = await vector_db.get_embedding(memory["memory_id"])
                    if not memory_embedding:
                        # Generate embedding if it doesn't exist
                        memory_embedding = await embedding_generator.generate_embedding(memory["content"])
                        await vector_db.store_embedding(memory["memory_id"], memory_embedding)

                    # Calculate similarity
                    if memory_embedding:
                        try:
                            # Make sure both embeddings are lists of floats
                            if isinstance(query_embedding, list) and isinstance(memory_embedding, list):
                                similarity = embedding_generator.cosine_similarity(
                                    query_embedding, memory_embedding)
                                memory["similarity"] = float(similarity)
                            else:
                                logger.warning(
                                    f"Invalid embedding format: query_embedding type: {type(query_embedding)}, memory_embedding type: {type(memory_embedding)}")
                                memory["similarity"] = 0.0
                        except Exception as e:
                            logger.warning(
                                f"Error calculating similarity: {str(e)}")
                            memory["similarity"] = 0.0
                    else:
                        memory["similarity"] = 0.0

                # If using both semantic and keyword, combine results
                if use_keyword:
                    # Keep all memories, but sort by similarity
                    memories = sorted(filtered_memories, key=lambda x: x.get(
                        "similarity", 0), reverse=True)
                else:
                    # Filter by similarity threshold - use a very low threshold (0.1) to find more results
                    # This ensures we find more memories that might be related
                    memories = [m for m in filtered_memories if m.get(
                        "similarity", 0) >= 0.1]
                    memories = sorted(memories, key=lambda x: x.get(
                        "similarity", 0), reverse=True)
            except Exception as e:
                logger.error(f"Error in semantic search: {str(e)}")
                # Fall back to keyword search
                logger.info(
                    "Falling back to keyword search due to semantic search error")
                memories = [
                    m for m in filtered_memories if query_text.lower() in m["content"].lower()]
                if not memories and not use_keyword:
                    # If keyword search also fails, try a more lenient approach
                    logger.info("Trying more lenient keyword search")
                    query_words = query_text.lower().split()
                    memories = []
                    for memory in filtered_memories:
                        content = memory["content"].lower()
                        # Check if any word in the query is in the content
                        if any(word in content for word in query_words if len(word) > 2):
                            memories.append(memory)
        else:
            # Use the filtered memories directly
            memories = filtered_memories

        # Apply limit
        memories = memories[:limit]

        # Close database connection
        conn.close()

        # Update last_accessed for retrieved memories
        if memories:
            await Memory._update_last_accessed([m["memory_id"] for m in memories])

        if not memories:
            await message.edit_text(
                f"No memories found for query: *{query_text}*\n\n"
                f"Try broadening your search, using different keywords, or try with `-b` option to use both semantic and keyword search.",
                parse_mode="Markdown"
            )
            return

        # Format the results
        result_text = f"🔍 *Search results for: {query_text}*\n"
        result_text += f"Found {len(memories)} results using {search_type} search\n\n"

        for i, memory in enumerate(memories, 1):
            content = memory["content"]
            category = memory["category"]
            importance = memory["importance"]
            memory_id = memory["memory_id"]
            created_at = memory.get("created_at", "Unknown date")
            if created_at and len(created_at) > 10:
                created_at = created_at[:10]  # Just show the date part

            # Format tags if available
            tags_str = ""
            if memory.get("tags") and memory["tags"]:
                tags_str = f"Tags: {', '.join(['#' + tag for tag in memory['tags']])}\n"

            # Format similarity score if available
            similarity_str = ""
            if "similarity" in memory and memory["similarity"]:
                similarity = memory["similarity"]
                similarity_str = f"Similarity: {similarity:.2f}\n"
                # Add stars based on similarity
                stars = "★" * int(similarity * 5) + "☆" * \
                    (5 - int(similarity * 5))
                similarity_str += f"Match: {stars}\n"

            result_text += f"*{i}. Memory #{memory_id}*\n"
            result_text += f"{content}\n\n"
            result_text += f"Category: {category}\n"
            result_text += f"Importance: {'🔴' if importance >= 4 else '🟠' if importance == 3 else '🟢'} {importance}/5\n"
            result_text += f"Created: {created_at}\n"
            result_text += tags_str
            result_text += similarity_str
            result_text += "\n"

        # Add a note about additional options
        result_text += "\n*Tip:* Use `/search_memories --help` to see all search options."

        # Update the message with the results
        await message.edit_text(result_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        await message.edit_text(f"❌ Error searching memories: {str(e)}")
