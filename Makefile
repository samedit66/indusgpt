QWEN = Qwen/Qwen2.5-1.5B-Instruct
GEMMA = google/gemma-3-4b-it
GEMMA12B = google/gemma-3-12b-it
GEMMA27B = google/gemma-3-27b-it
HERMES = NousResearch/Hermes-2-Pro-Mistral-7B

.PHONY: serve
serve:
	vllm serve $(GEMMA)