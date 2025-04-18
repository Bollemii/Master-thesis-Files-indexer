#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
# Record Process ID.
pid=$!

# Configure model
model="gemma3:4b"

# Pause for Ollama to start.
sleep 5

echo "🔴 Retrieve $model model..."
ollama pull $model
echo "🟢 Done!"

# Wait for Ollama process to finish.
wait $pid