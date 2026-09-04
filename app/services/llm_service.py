import httpx


class OllamaUnavailableError(RuntimeError):
    pass


class OllamaService:
    def __init__(self, base_url: str, model: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, question: str, context: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "options": {"num_predict": 256},
            "messages": [
                {"role": "system", "content": "Answer only from the provided context. If the answer is not present in the context, say you don't know."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
        }
        try:
            response = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return str(data["message"]["content"])
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise OllamaUnavailableError(
                f"Ollama could not generate an answer using model '{self.model}'."
            ) from exc