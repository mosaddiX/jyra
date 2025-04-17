import sqlite3
import asyncio
from jyra.ai.embeddings.embedding_generator import embedding_generator
from jyra.ai.embeddings.vector_db import vector_db
from jyra.utils.config import DATABASE_PATH


async def test_search(query="jyoti", use_keyword=True, use_semantic=True):
    """
    Test the search functionality directly.

    Args:
        query (str): The search query
        use_keyword (bool): Whether to use keyword search
        use_semantic (bool): Whether to use semantic search
    """
    print(
        f"Searching for: '{query}' (keyword: {use_keyword}, semantic: {use_semantic})")

    # Get all memories
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all memories
    cursor.execute("SELECT * FROM memories")
    rows = cursor.fetchall()

    # Get unique user IDs
    user_ids = set(row["user_id"] for row in rows)
    print(f"Found users: {user_ids}")

    print(f"Total memories for user: {len(rows)}")

    # Perform keyword search if requested
    keyword_results = []
    if use_keyword:
        cursor.execute(
            "SELECT * FROM memories WHERE content LIKE ?", (f"%{query}%",))
        keyword_rows = cursor.fetchall()
        keyword_results = [dict(row) for row in keyword_rows]
        print(f"Keyword search found {len(keyword_results)} results")
        for i, memory in enumerate(keyword_results, 1):
            print(
                f"{i}. Memory #{memory['memory_id']} (User {memory['user_id']}): {memory['content'][:100]}...")

    # Perform semantic search if requested
    semantic_results = []
    if use_semantic:
        try:
            # Generate embedding for the query
            query_embedding = await embedding_generator.generate_embedding(query)

            # Get all memory IDs
            memory_ids = [row["memory_id"] for row in rows]

            # Calculate similarity for each memory
            memories_with_similarity = []
            for memory_id in memory_ids:
                # Get or generate embedding for the memory
                memory_embedding = await vector_db.get_embedding(memory_id)
                if not memory_embedding:
                    # Get the memory content
                    cursor.execute(
                        "SELECT content FROM memories WHERE memory_id = ?", (memory_id,))
                    content = cursor.fetchone()["content"]

                    # Generate embedding if it doesn't exist
                    memory_embedding = await embedding_generator.generate_embedding(content)
                    await vector_db.store_embedding(memory_id, memory_embedding)

                # Calculate similarity
                if memory_embedding:
                    similarity = embedding_generator.cosine_similarity(
                        query_embedding, memory_embedding)

                    # Add to results if similarity is high enough
                    if similarity >= 0.3:  # Lower threshold for testing
                        cursor.execute(
                            "SELECT * FROM memories WHERE memory_id = ?", (memory_id,))
                        memory = dict(cursor.fetchone())
                        memory["similarity"] = similarity
                        memories_with_similarity.append(memory)

            # Sort by similarity
            semantic_results = sorted(
                memories_with_similarity, key=lambda x: x.get("similarity", 0), reverse=True)
            print(f"Semantic search found {len(semantic_results)} results")
            for i, memory in enumerate(semantic_results, 1):
                print(
                    f"{i}. Memory #{memory['memory_id']} (User {memory['user_id']}): {memory['content'][:100]}... (similarity: {memory['similarity']:.2f})")
        except Exception as e:
            print(f"Error in semantic search: {str(e)}")

    # Combine results if both methods are used
    if use_keyword and use_semantic:
        # Get unique memory IDs from both result sets
        keyword_ids = {m["memory_id"] for m in keyword_results}
        semantic_ids = {m["memory_id"] for m in semantic_results}
        all_ids = keyword_ids.union(semantic_ids)

        # Create a combined result set
        combined_results = []
        for memory_id in all_ids:
            # Find the memory in either result set
            memory = next(
                (m for m in semantic_results if m["memory_id"] == memory_id), None)
            if not memory:
                memory = next(
                    (m for m in keyword_results if m["memory_id"] == memory_id), None)

            combined_results.append(memory)

        # Sort by similarity if available, otherwise just by memory_id
        combined_results = sorted(combined_results,
                                  key=lambda x: (
                                      x.get("similarity", 0), x["memory_id"]),
                                  reverse=True)

        print(f"\nCombined search found {len(combined_results)} results")
        for i, memory in enumerate(combined_results, 1):
            similarity_str = f" (similarity: {memory.get('similarity', 0):.2f})" if "similarity" in memory else ""
            print(
                f"{i}. Memory #{memory['memory_id']} (User {memory['user_id']}): {memory['content'][:100]}...{similarity_str}")

    conn.close()

if __name__ == "__main__":
    asyncio.run(test_search("jyoti", use_keyword=True, use_semantic=True))
