from sentence_transformers import SentenceTransformer
from pinecone import Index
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Connect to Pinecone
pinecone_index = Index(
    name="codebase-rag",
    api_key=PINECONE_API_KEY,
    host=PINECONE_HOST
)

# Function to generate embeddings using SentenceTransformer
def get_embeddings(text, model_name="sentence-transformers/all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)
    return model.encode(text)

# Perform RAG using OpenAI
def perform_rag(query):
    # Generate query embedding
    query_embedding = get_embeddings(query)

    # Retrieve relevant contexts from Pinecone
    search_results = pinecone_index.query(
        vector=query_embedding.tolist(),
        top_k=5,
        include_metadata=True,
    )
    contexts = [match["metadata"]["text"] for match in search_results["matches"]]

    if not contexts:
        return "No relevant context found in Pinecone."

    # Build augmented query
    augmented_query = f"<CONTEXT>\n{'\n---\n'.join(contexts)}\n</CONTEXT>\n\nQUESTION:\n{query}"

    try:
        # Use the new OpenAI client API
        completion = openai_client.chat.completions.create(
            model="gpt-4o",  # Replace with your model name
            messages=[
                {"role": "system", "content": "You are an expert software assistant."},
                {"role": "user", "content": augmented_query},
            ],
            max_tokens=300,
            temperature=0.7,
        )

        # Extract and return the response
        if completion.choices:
            # Use `.message.content` to access the message content
            return completion.choices[0].message.content.strip()
        else:
            return "Error: No valid response received from OpenAI."
    except Exception as e:
        return f"Error during OpenAI API call: {e}"


# Example usage
if __name__ == "__main__":
    # Test query
    query = "How does the JavaScript parser work?"
    response = perform_rag(query)
    print(response)


