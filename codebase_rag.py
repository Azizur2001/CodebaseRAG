# Main program
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from git import Repo
import os
from pinecone import Index
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Initialize environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")  # Your Pinecone host URL
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Connect to the Pinecone index
pinecone_index = Index(
    name="codebase-rag",
    api_key=PINECONE_API_KEY,
    host=PINECONE_HOST
)

def get_embeddings(text, model_name="sentence-transformers/all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)
    return model.encode(text)

# Function to retrieve file content from a cloned repo
def clone_repository(repo_url):
    """Clones a GitHub repository to a local directory."""
    repo_name = repo_url.split("/")[-1]
    repo_path = f"./{repo_name}"
    if os.path.exists(repo_path):
        print(f"Repository {repo_name} already exists at {repo_path}. Skipping cloning.")
        return str(repo_path)
    Repo.clone_from(repo_url, str(repo_path))
    return str(repo_path)

SUPPORTED_EXTENSIONS = {'.py', '.js', '.tsx', '.jsx', '.ipynb', '.java', '.cpp', '.ts', '.go', '.rs', '.vue', '.swift', '.c', '.h'}
IGNORED_DIRS = {'node_modules', 'venv', 'env', 'dist', 'build', '.git', '__pycache__', '.next', '.vscode', 'vendor'}

def get_file_content(file_path, repo_path):
    """Retrieve content from a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        rel_path = os.path.relpath(file_path, repo_path)
        return {"name": rel_path, "content": content}
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def get_main_files_content(repo_path: str):
    """Retrieve content of supported code files from a local repository."""
    files_content = []
    try:
        for root, _, files in os.walk(repo_path):
            if any(ignored_dir in root for ignored_dir in IGNORED_DIRS):
                continue
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.splitext(file)[1] in SUPPORTED_EXTENSIONS:
                    file_content = get_file_content(file_path, repo_path)
                    if file_content:
                        files_content.append(file_content)
    except Exception as e:
        print(f"Error reading repository: {e}")
    return files_content

# Function to populate Pinecone index
def populate_pinecone(file_content):
    for file in file_content:
        # Create embeddings for the file content
        embedding = get_embeddings(f"{file['name']}\n{file['content']}")
        
        # Upsert to Pinecone
        pinecone_index.upsert([
            (file["name"], embedding.tolist(), {"text": file["content"], "source": file["name"]})
        ])

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
        # Use the new OpenAI client and updated syntax
        completion = client.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert software assistant."},
                {"role": "user", "content": augmented_query},
            ],
        )

        # Extract and return the response
        if completion.choices and len(completion.choices) > 0:
            return completion.choices[0].message.content
        else:
            return "Error: No valid response received from OpenAI."
    except Exception as e:
        return f"Error during OpenAI API call: {e}"

# Example usage
if __name__ == "__main__":
    # Clone a repo and populate Pinecone (only once)
    repo_path = clone_repository("https://github.com/CoderAgent/SecureAgent")
    file_content = get_main_files_content(repo_path)
    print("Files Extracted:", [file["name"] for file in file_content])
    populate_pinecone(file_content)

    # Test query
    query = "How is the JavaScript parser used?"
    response = perform_rag(query)
    print(response)



# from openai import OpenAI
# from sentence_transformers import SentenceTransformer
# from git import Repo
# import os
# from pinecone import Index
# from dotenv import load_dotenv
# import requests

# # Load environment variables
# load_dotenv()

# # Initialize environment variables
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# PINECONE_HOST = os.getenv("PINECONE_HOST")  # Your Pinecone host URL
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # Initialize OpenAI client
# client = OpenAI(api_key=OPENAI_API_KEY)

# # Connect to the Pinecone index
# pinecone_index = Index(
#     name="codebase-rag",
#     api_key=PINECONE_API_KEY,
#     host=PINECONE_HOST
# )

# def get_embeddings(text, model_name="sentence-transformers/all-mpnet-base-v2"):
#     """Generate embeddings using SentenceTransformer."""
#     model = SentenceTransformer(model_name)
#     return model.encode(text)

# # Function to retrieve file content from a cloned repo
# def clone_repository(repo_url):
#     """Clones a GitHub repository to a local directory."""
#     repo_name = repo_url.split("/")[-1]
#     repo_path = f"./{repo_name}"
#     if os.path.exists(repo_path):
#         print(f"Repository {repo_name} already exists at {repo_path}. Skipping cloning.")
#         return str(repo_path)
#     Repo.clone_from(repo_url, str(repo_path))
#     return str(repo_path)

# SUPPORTED_EXTENSIONS = {'.py', '.js', '.tsx', '.jsx', '.ipynb', '.java', '.cpp', '.ts', '.go', '.rs', '.vue', '.swift', '.c', '.h'}
# IGNORED_DIRS = {'node_modules', 'venv', 'env', 'dist', 'build', '.git', '__pycache__', '.next', '.vscode', 'vendor'}

# def get_file_content(file_path, repo_path):
#     """Retrieve content from a single file."""
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             content = f.read()
#         rel_path = os.path.relpath(file_path, repo_path)
#         return {"name": rel_path, "content": content}
#     except Exception as e:
#         print(f"Error processing file {file_path}: {e}")
#         return None

# def get_main_files_content(repo_path: str):
#     """Retrieve content of supported code files from a local repository."""
#     files_content = []
#     try:
#         for root, _, files in os.walk(repo_path):
#             if any(ignored_dir in root for ignored_dir in IGNORED_DIRS):
#                 continue
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 if os.path.splitext(file)[1] in SUPPORTED_EXTENSIONS:
#                     file_content = get_file_content(file_path, repo_path)
#                     if file_content:
#                         files_content.append(file_content)
#     except Exception as e:
#         print(f"Error reading repository: {e}")
#     return files_content

# def populate_pinecone(file_content, namespace):
#     """Populate Pinecone with file content under a specific namespace."""
#     for file in file_content:
#         # Create embeddings for the file content
#         embedding = get_embeddings(f"{file['name']}\n{file['content']}")

#         # Upsert to Pinecone with the specified namespace
#         pinecone_index.upsert(
#             [(file["name"], embedding.tolist(), {"text": file["content"], "source": file["name"]})],
#             namespace=namespace,  # Use namespace for separation
#         )

# def perform_rag(query, namespace):
#     """Perform RAG by querying Pinecone and using OpenAI."""
#     # Generate query embedding
#     query_embedding = get_embeddings(query)

#     try:
#         # Retrieve relevant contexts from Pinecone using the namespace
#         search_results = pinecone_index.query(
#             vector=query_embedding.tolist(),
#             top_k=5,
#             include_metadata=True,
#             namespace=namespace,  # Specify namespace
#         )
#         contexts = [match["metadata"]["text"] for match in search_results["matches"]]

#         if not contexts:
#             return "No relevant context found in Pinecone."
        
#         # Build augmented query
#         augmented_query = f"<CONTEXT>\n{'\n---\n'.join(contexts)}\n</CONTEXT>\n\nQUESTION:\n{query}"

#         # Use OpenAI to get a response
#         completion = client.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": "You are an expert software assistant."},
#                 {"role": "user", "content": augmented_query},
#             ],
#         )

#         # Extract and return the response
#         if completion.choices and len(completion.choices) > 0:
#             return completion.choices[0].message.content.strip()
#         else:
#             return "Error: No valid response received from OpenAI."
#     except Exception as e:
#         return f"Error during RAG process: {e}"

# # Example usage
# if __name__ == "__main__":
#     # Example: Populate Pinecone with "Secure Agent" namespace
#     repo_url = "https://github.com/CoderAgent/SecureAgent"
#     repo_path = clone_repository(repo_url)
#     file_content = get_main_files_content(repo_path)
#     print("Files Extracted:", [file["name"] for file in file_content])

#     # Populate the "secure_agent" namespace in Pinecone
#     populate_pinecone(file_content, namespace="secure_agent")

#     repo_url = "https://github.com/Azizur2001/ai-support-app"
#     repo_path = clone_repository(repo_url)
#     file_content = get_main_files_content(repo_path)
#     print("Files Extracted:", [file["name"] for file in file_content])

#     # Populate the "secure_agent" namespace in Pinecone
#     populate_pinecone(file_content, namespace="ai-support")

#     # Example: Perform RAG for the "secure_agent" namespace
#     query = "How is the JavaScript parser used?"
#     response = perform_rag("What does this function do?", namespace="another_repo")
#     print(response)

