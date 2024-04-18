# Answer Cache for Griptape

A Griptape tool for storing and retrieving answers from cache, using Vector Store.

## Usage

To use this tool you need to setup any Vector Store, in this example we use Redis (you can find compose.yaml for Redis Stack in examples folder).

Here's an example:

```python
from redis.commands.search.field import TagField, VectorField
from redis.commands.search.indexDefinition import IndexType, IndexDefinition
from griptape.tools import TaskMemoryClient
from griptape.structures import Agent
from answer_cache import AnswerCache
from griptape.drivers.prompt.openai_chat_prompt_driver import OpenAiChatPromptDriver
from griptape.drivers.embedding.openai_embedding_driver import OpenAiEmbeddingDriver
from griptape.drivers.vector.redis_vector_store_driver import RedisVectorStoreDriver
from griptape.rules.ruleset import Rule


# Create Index for verctor search
def create_index(redis_vector_store: RedisVectorStoreDriver, namespace: str, vector_dimension: int) -> None:
    try:
        redis_vector_store.client.ft(redis_vector_store.index).info()
    except:
        schema = (
            TagField("tag"),
            VectorField("vector", "FLAT", {"TYPE": "FLOAT32", "DIM": vector_dimension, "DISTANCE_METRIC": "COSINE"}),
        )

        doc_prefix = redis_vector_store._get_doc_prefix(namespace)
        definition = IndexDefinition(prefix=[doc_prefix], index_type=IndexType.HASH)
        redis_vector_store.client.ft(redis_vector_store.index).create_index(fields=schema, definition=definition)


embedding_driver = OpenAiEmbeddingDriver(model="text-embedding-3-small")
vector_dimension = 1536
namespace = "example"
redis_store = RedisVectorStoreDriver(embedding_driver=embedding_driver, host="localhost", port=6379, index="example")
create_index(redis_store, namespace, vector_dimension)

cache_tool = AnswerCache(
    threshold=0.30, embedding_driver=embedding_driver, vector_store=redis_store, namespace=namespace
)

agent = Agent(
    tools=[cache_tool, TaskMemoryClient(off_prompt=False)],
    rules=[
        Rule("You can use cache_tool to search for user question in cached answers"),
        Rule("If there is no answer in cache use cache_tool to store your answer in cache"),
    ],
)
agent.config.global_drivers.prompt_driver = OpenAiChatPromptDriver(model="gpt-3.5-turbo")

# First task will generate answer and store it in cache
agent.run("Tell me a joke")
# Second task should get already cached answer from vector store (depends on `threshold` that you define)
agent.run("Show me a joke")
# threshold defines maximum score that cached answer can have, let's try to lower it and change prompt
cache_tool.threshold = 0.1
agent.run("Tell me a joke about crow and fox, make it very funny")
```
```
[04/18/24 23:03:26] INFO     ToolkitTask e9f3c1d629bb45c2ac99905472f12f3a
                             Input: Tell me a joke
[04/18/24 23:03:35] INFO     Subtask 7e9f9812bbb44c869a323d03fde5740f
                             Thought: The user asked for a joke. I don't have a joke in my memory, so I'll generate a
                             simple, common joke. After generating the joke, I'll store it in the cache for future
                             reference.
                             Actions: [
                               {
                                 "name": "AnswerCache",
                                 "path": "store_answer_in_cache",
                                 "input": {
                                   "values": {
                                     "prompt": "Tell me a joke",
                                     "answer": "Why don't scientists trust atoms? Because they make up everything!"
                                   }
                                 },
                                 "tag": "store_joke_in_cache"
                               }
                             ]
[04/18/24 23:03:36] INFO     Subtask 7e9f9812bbb44c869a323d03fde5740f
                             Response: store_joke_in_cache output: Answer stored in cache
[04/18/24 23:03:37] INFO     ToolkitTask e9f3c1d629bb45c2ac99905472f12f3a
                             Output: Why don't scientists trust atoms? Because they make up everything!
                    INFO     ToolkitTask e9f3c1d629bb45c2ac99905472f12f3a
                             Input: Show me a joke
[04/18/24 23:03:44] INFO     Subtask d5fcb78a92c44c9f88ced67eda2fc176
                             Thought: I need to check if there's a joke in the cache for the prompt "Show me a joke". If
                             there isn't, I'll need to provide a joke and store it in the cache.
                             Actions: [
                               {
                                 "name": "AnswerCache",
                                 "path": "get_answer_from_cache",
                                 "input": {
                                   "values": {
                                     "prompt": "Show me a joke"
                                   }
                                 },
                                 "tag": "get_joke_from_cache"
                               }
                             ]
[04/18/24 23:03:45] INFO     Subtask d5fcb78a92c44c9f88ced67eda2fc176
                             Response: get_joke_from_cache output: Why don't scientists trust atoms? Because they make
                             up everything!
[04/18/24 23:03:46] INFO     ToolkitTask e9f3c1d629bb45c2ac99905472f12f3a
                             Output: Why don't scientists trust atoms? Because they make up everything!
                    INFO     ToolkitTask e9f3c1d629bb45c2ac99905472f12f3a
                             Input: Tell me a joke about crow and fox, make it very funny
[04/18/24 23:03:52] INFO     Subtask 6f1215221e8c47fca462c655178e21da
                             Thought: The user asked for a specific joke about a crow and a fox. I need to check if we
                             have this joke in our cache.
                             Actions: [
                               {
                                 "name": "AnswerCache",
                                 "path": "get_answer_from_cache",
                                 "input": {
                                   "values": {
                                     "prompt": "Tell me a joke about crow and fox, make it very funny"
                                   }
                                 },
                                 "tag": "get_joke_from_cache"
                               }
                             ]
[04/18/24 23:03:53] INFO     Subtask 6f1215221e8c47fca462c655178e21da
                             Response: get_joke_from_cache output: Answer not found in cache
[04/18/24 23:04:00] INFO     Subtask 2a2a6a4ed6b34a3cb40551e85cc5e4f1
                             Thought: The joke is not in the cache. I need to create a funny joke about a crow and a
                             fox. After creating the joke, I will store it in the cache for future use.
                             Actions: [{"tag": "store_joke_in_cache", "name": "AnswerCache", "path":
                             "store_answer_in_cache", "input": {"values": {"prompt": "Tell me joke about crow and fox,
                             make it very funny", "answer": "Why did the crow invite the fox to dinner? Because he heard
                             that foxes are outstanding in their 'field'!"}}}]
                    INFO     Subtask 2a2a6a4ed6b34a3cb40551e85cc5e4f1
                             Response: store_joke_in_cache output: Answer stored in cache
[04/18/24 23:04:03] INFO     ToolkitTask e9f3c1d629bb45c2ac99905472f12f3a
                             Output: Why did the crow invite the fox to dinner? Because he heard that foxes are
                             outstanding in their 'field'!
```
