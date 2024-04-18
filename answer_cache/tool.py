from __future__ import annotations
import json
from griptape.artifacts import TextArtifact, InfoArtifact, ErrorArtifact, BaseArtifact
from griptape.tools import BaseTool
from griptape.utils.decorators import activity
from griptape.drivers import BaseEmbeddingDriver, BaseVectorStoreDriver
from schema import Schema
from typing import Optional
from attr import define, field
import logging


@define
class AnswerCache(BaseTool):
    threshold: float = field(kw_only=True)
    embedding_driver: BaseEmbeddingDriver = field(kw_only=True)
    vector_store: BaseVectorStoreDriver = field(kw_only=True)
    namespace: Optional[str] = field(default="cache", kw_only=True)
    off_prompt: bool = field(default=False, kw_only=True)

    @activity(
        config={
            "description": "get_answer_from_cache can be used to get answer from cache, passing user prompt",
            "schema": Schema({"prompt": str}),
        }
    )
    def get_answer_from_cache(self, params: dict) -> TextArtifact | ErrorArtifact:
        return self._search(params["values"].get("prompt"))

    @activity(
        config={
            "description": "store_answer_in_cache can be used to store answer in cache, passing user prompt and your answer",
            "schema": Schema({"prompt": str, "answer": str}),
        }
    )
    def store_answer_in_cache(self, params: dict) -> InfoArtifact | ErrorArtifact:
        return self._store(params["values"].get("prompt"), params["values"].get("answer"))

    def _search(self, prompt: str) -> TextArtifact | ErrorArtifact:
        try:
            for result in self.vector_store.query(query=prompt, count=1, namespace=self.namespace):
                if abs(result.score) <= self.threshold:
                    return TextArtifact.from_dict(json.loads(result.meta)["answer"])
        except Exception as e:
            error = ErrorArtifact(f"Error during cache search: {e}")
            logging.error(error)
            return error
        return ErrorArtifact("Answer not found in cache")

    def _store(self, prompt: str, answer: str) -> InfoArtifact | ErrorArtifact:
        try:
            self.vector_store.upsert_text_artifact(
                artifact=TextArtifact(prompt), namespace=self.namespace, meta={"answer": TextArtifact(answer).to_dict()}
            )
            return InfoArtifact("Answer stored in cache")
        except Exception as e:
            error = ErrorArtifact(f"Error during storing in cache: {e}")
            logging.error(error)
            return error
