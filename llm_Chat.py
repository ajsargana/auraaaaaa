# llm_chat.py
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.core.llms import ChatMessage

llm = HuggingFaceLLM(
    model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    tokenizer_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    device_map="auto"
)

conversation_history = []

def chat_with_llm(user_input):
    conversation_history.append(ChatMessage(role="user", content=user_input))
    response = llm.chat(conversation_history)
    conversation_history.append(ChatMessage(role="assistant", content=str(response)))
    return str(response)
