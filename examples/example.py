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
agent.run("Tell me joke about crow and fox, make it very funny")
