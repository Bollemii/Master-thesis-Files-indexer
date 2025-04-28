#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
# Record Process ID.
pid=$!

# Configure model
llm_model="gemma3:4b"
embedding_model="nomic-embed-text"

# Pause for Ollama to start.
sleep 5

echo "🔴 Retrieve LLM model ($llm_model)..."
ollama pull $llm_model
echo "🔴 Retrieve Embedding model ($embedding_model)..."
ollama pull $embedding_model
echo "🟢 Done!"

# Wait for Ollama process to finish.
wait $pid