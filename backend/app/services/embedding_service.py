from sentence_transformers import SentenceTransformer


class TextEmbeddingService:

    def __init__(self):

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )


    def encode(self, text):

        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embedding.astype("float32")