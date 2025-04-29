QWEN = Qwen/Qwen2.5-1.5B-Instruct
GEMMA = google/gemma-3-4b-it

.PHONY: serve
serve:
	vllm serve $(GEMMA)
