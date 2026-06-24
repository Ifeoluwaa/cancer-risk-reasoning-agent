"""embeddings.py

Deterministic local embedding generator for scientific text representation.
"""

import hashlib
from typing import List
import chromadb
from chromadb.api.types import Documents, Embeddings


class SimpleLocalEmbeddingFunction(chromadb.EmbeddingFunction[Documents]):
    """A deterministic, local embedding generator mapping text to float vectors.

    Avoids all external network calls and API keys.
    """

    def __init__(self, dimension: int = 128) -> None:
        """Initialize the embedding function.

        Args:
            dimension: The dimensionality of the generated vectors.
        """
        self.dimension = dimension

    def __call__(self, input: Documents) -> Embeddings:
        """Generate deterministic embeddings for a list of document strings.

        Args:
            input: A list of text strings (documents/chunks).

        Returns:
            A list of lists of floats representing the embeddings.
        """
        embeddings = []
        for text in input:
            vector = []
            for i in range(self.dimension):
                # Deterministic seed hashing for each dimension
                h = hashlib.md5(f"{text}_dim_{i}".encode("utf-8")).hexdigest()
                # Normalize hash value to a range of [-1.0, 1.0]
                val = (int(h, 16) % 20000) / 10000.0 - 1.0
                vector.append(val)
            embeddings.append(vector)
        return embeddings
