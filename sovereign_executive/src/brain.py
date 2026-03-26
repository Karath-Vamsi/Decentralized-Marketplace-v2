import openai


client = openai.OpenAI(
    base_url="http://localhost:8081/v1", 
    api_key="sk-no-key-required" # A placeholder is required but ignored
)

def chat_with_twin(prompt):
    try:
        response = client.chat.completions.create(
            model="local-model", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Connection Error: {str(e)}"

if __name__ == "__main__":
    print("Connecting to the Digital Twin...")
    test_response = chat_with_twin("Hello! Confirm you are running locally.")
    print(f"Twin says: {test_response}")