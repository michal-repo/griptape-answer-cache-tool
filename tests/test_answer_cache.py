from unittest.mock import patch
from griptape.artifacts import TextArtifact, ErrorArtifact
from answer_cache import AnswerCache
from griptape.drivers import DummyVectorStoreDriver, DummyEmbeddingDriver


class TestAnswerCache:
    @patch("answer_cache.AnswerCache.get_answer_from_cache")
    def test_get_answer_from_cache(self, mock_get_answer_from_cache):
        mock_get_answer_from_cache.return_value = TextArtifact("dummy")

        prompt = "human prompt"
        cache = AnswerCache(
            threshold=0.10,
            embedding_driver=DummyEmbeddingDriver(),
            vector_store=DummyVectorStoreDriver(),
            namespace="namespace",
        )
        params = {"prompt": prompt}
        result = cache.get_answer_from_cache(params)

        assert isinstance(result, TextArtifact), "Expected TextArtifact"
