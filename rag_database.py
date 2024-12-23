# import os
# import chromadb
# from typing import List, Optional
# import uuid

# class RAGDatabaseManager:
#     def __init__(self, persist_directory="/home/ekats/scratch/#Project Charvis/start fro the basics/RAG"):
#         """
#         Initialize ChromaDB vector database for RAG system.
        
#         :param persist_directory: Directory to persist the vector database
#         """
#         # If no directory specified, use a default in the user's home directory
#         if persist_directory is None:
#             base_dir = os.path.expanduser("~/.charvis")
#             persist_directory = os.path.join(base_dir, "rag_database")
        
#         # Ensure directory exists
#         os.makedirs(persist_directory, exist_ok=True)
        
#         # Store the directory path
#         self.persist_directory = persist_directory
        
#         # Initialize ChromaDB client
#         self.client = chromadb.PersistentClient(path=persist_directory)
        
#         # Create or get collections
#         self.dialogue_collection = self.client.get_or_create_collection(
#             name="dialogue_collection", 
#             metadata={"hnsw:space": "cosine"}
#         )
#         self.article_collection = self.client.get_or_create_collection(
#             name="article_collection", 
#             metadata={"hnsw:space": "cosine"}
#         )
    
#     def get_database_path(self):
#         """
#         Get the path to the current vector database.
        
#         :return: Path to the vector database directory
#         """
#         return self.persist_directory

#     def __init__(self, persist_directory="./rag_database"):
#         """
#         Initialize ChromaDB vector database for RAG system.
        
#         :param persist_directory: Directory to persist the vector database
#         """
#         # Ensure directory exists
#         os.makedirs(persist_directory, exist_ok=True)
        
#         # Initialize ChromaDB client
#         self.client = chromadb.PersistentClient(path=persist_directory)
        
#         # Create or get collections
#         self.dialogue_collection = self.client.get_or_create_collection(
#             name="dialogue_collection", 
#             metadata={"hnsw:space": "cosine"}
#         )
#         self.article_collection = self.client.get_or_create_collection(
#             name="article_collection", 
#             metadata={"hnsw:space": "cosine"}
#         )

#     def add_dialogue(self, dialogue: str, context: Optional[str] = None, tags: Optional[List[str]] = None):
#         """
#         Add a dialogue to the vector database.
        
#         :param dialogue: The dialogue text to store
#         :param context: Optional context for the dialogue
#         :param tags: Optional tags for categorization
#         """
#         # Generate a unique ID
#         doc_id = str(uuid.uuid4())
        
#         # Prepare metadata
#         metadata = {
#             "type": "dialogue",
#             "context": context or "",
#             "tags": ",".join(tags) if tags else ""
#         }
        
#         # Add to collection
#         self.dialogue_collection.add(
#             documents=[dialogue],
#             metadatas=[metadata],
#             ids=[doc_id]
#         )
        
#         return doc_id

#     def add_article(self, article: str, title: Optional[str] = None, tags: Optional[List[str]] = None):
#         """
#         Add an article to the vector database.
        
#         :param article: The article text to store
#         :param title: Optional title of the article
#         :param tags: Optional tags for categorization
#         """
#         # Generate a unique ID
#         doc_id = str(uuid.uuid4())
        
#         # Prepare metadata
#         metadata = {
#             "type": "article",
#             "title": title or "",
#             "tags": ",".join(tags) if tags else ""
#         }
        
#         # Add to collection
#         self.article_collection.add(
#             documents=[article],
#             metadatas=[metadata],
#             ids=[doc_id]
#         )
        
#         return doc_id

#     def retrieve_relevant_context(self, query: str, collection_type: str = "dialogue", top_k: int = 3):
#         """
#         Retrieve relevant context from the specified collection.
        
#         :param query: The query to find relevant context for
#         :param collection_type: Type of collection to search ('dialogue' or 'article')
#         :param top_k: Number of top results to retrieve
#         :return: List of relevant context documents
#         """
#         # Select the appropriate collection
#         collection = (self.dialogue_collection if collection_type == "dialogue" 
#                       else self.article_collection)
        
#         # Perform similarity search
#         results = collection.query(
#             query_texts=[query],
#             n_results=top_k
#         )
        
#         # Process and return results
#         relevant_contexts = []
#         for i in range(len(results['documents'][0])):
#             context = {
#                 'text': results['documents'][0][i],
#                 'metadata': results['metadatas'][0][i],
#                 'distance': results['distances'][0][i]
#             }
#             relevant_contexts.append(context)
        
#         return relevant_contexts

#     def list_entries(self, collection_type: str = "dialogue"):
#         """
#         List all entries in a specified collection.
        
#         :param collection_type: Type of collection to list ('dialogue' or 'article')
#         :return: List of entries with their metadata
#         """
#         # Select the appropriate collection
#         collection = (self.dialogue_collection if collection_type == "dialogue" 
#                       else self.article_collection)
        
#         # Retrieve all entries
#         entries = collection.get()
        
#         # Process entries
#         formatted_entries = []
#         for i in range(len(entries['ids'])):
#             entry = {
#                 'id': entries['ids'][i],
#                 'text': entries['documents'][i],
#                 'metadata': entries['metadatas'][i]
#             }
#             formatted_entries.append(entry)
        
#         return formatted_entries

# # Example usage demonstration
# def main():
#     # Initialize the RAG Database Manager
#     rag_manager = RAGDatabaseManager()
    
#     # Add a dialogue
#     dialogue_id = rag_manager.add_dialogue(
#         "Claude is an AI assistant created by Anthropic to be helpful, honest, and harmless.",
#         context="Company background",
#         tags=["AI", "Anthropic"]
#     )
    
#     # Add an article
#     article_id = rag_manager.add_article(
#         "Large language models are advanced AI systems trained on vast amounts of text data to understand and generate human-like text.",
#         title="Understanding Large Language Models",
#         tags=["AI", "Machine Learning"]
#     )
    
#     # Retrieve relevant context
#     context = rag_manager.retrieve_relevant_context("Tell me about AI assistants")
#     print("Retrieved Context:", context)

# if __name__ == "__main__":
#     main()

import os
import chromadb
from typing import List, Optional
import uuid

class RAGDatabaseManager:
    """
        RAGDatabaseManager: A class for managing a ChromaDB vector database in the context of a Retrieval-Augmented Generation (RAG) system.

        This class facilitates the storage, retrieval, and management of structured data within a vector database, enabling efficient access to relevant dialogue and article content for natural language processing tasks. It supports adding dialogues and articles, retrieving relevant context, and listing entries from specified database collections.

        Attributes:
        - persist_directory: Directory to store the vector database.
        - dialogue_collection: ChromaDB collection for storing dialogue data.
        - article_collection: ChromaDB collection for storing article data.

        Methods:
        - __init__(persist_directory=None): Initializes the RAGDatabaseManager, setting up the database and creating collections if necessary.
        - get_database_path(): Returns the path to the current vector database.
        - add_dialogue(dialogue, context=None, tags=None): Adds a dialogue to the database, generating a unique ID for each entry.
        - add_article(article, title=None, tags=None): Adds an article to the database, with optional title and tags.
        - retrieve_relevant_context(query, collection_type="dialogue", top_k=3): Retrieves the top-k relevant entries from the specified collection based on the given query.
        - list_entries(collection_type="dialogue"): Lists all entries in the specified collection, returning metadata and document content.

        Example usage:
        - Initialize the manager using `RAGDatabaseManager()`.
        - Use `add_dialogue` and `add_article` methods to store content.
        - Call `retrieve_relevant_context` to fetch relevant data based on queries.
        - Utilize `list_entries` to see stored entries in the specified collections.
    """

    def __init__(self, persist_directory=None):
        """
        Initialize ChromaDB vector database for RAG system.
        
        :param persist_directory: Directory to persist the vector database
        """
        # If no directory specified, use a default in the user's home directory
        if persist_directory is None:
            base_dir = os.path.expanduser("~/.charvis")
            persist_directory = os.path.join(base_dir, "rag_database")
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Store the directory path as an instance attribute
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collections
        self.dialogue_collection = self.client.get_or_create_collection(
            name="dialogue_collection", 
            metadata={"hnsw:space": "cosine"}
        )
        self.article_collection = self.client.get_or_create_collection(
            name="article_collection", 
            metadata={"hnsw:space": "cosine"}
        )

    def get_database_path(self):
        """
        Get the path to the current vector database.
        
        :return: Path to the vector database directory
        """
        return self.persist_directory

    def add_dialogue(self, dialogue: str, context: Optional[str] = None, tags: Optional[List[str]] = None):
        """
        Add a dialogue to the vector database.
        
        :param dialogue: The dialogue text to store
        :param context: Optional context for the dialogue
        :param tags: Optional tags for categorization
        """
        # Generate a unique ID
        doc_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            "type": "dialogue",
            "context": context or "",
            "tags": ",".join(tags) if tags else ""
        }
        
        # Add to collection
        self.dialogue_collection.add(
            documents=[dialogue],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id

    def add_article(self, article: str, title: Optional[str] = None, tags: Optional[List[str]] = None):
        """
        Add an article to the vector database.
        
        :param article: The article text to store
        :param title: Optional title of the article
        :param tags: Optional tags for categorization
        """
        # Generate a unique ID
        doc_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            "type": "article",
            "title": title or "",
            "tags": ",".join(tags) if tags else ""
        }
        
        # Add to collection
        self.article_collection.add(
            documents=[article],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id

    def retrieve_relevant_context(self, query: str, collection_type: str = "dialogue", top_k: int = 3):
        """
        Retrieve relevant context from the specified collection.
        
        :param query: The query to find relevant context for
        :param collection_type: Type of collection to search ('dialogue' or 'article')
        :param top_k: Number of top results to retrieve
        :return: List of relevant context documents
        """
        # Select the appropriate collection
        collection = (self.dialogue_collection if collection_type == "dialogue" 
                      else self.article_collection)
        
        # Perform similarity search
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Process and return results
        relevant_contexts = []
        for i in range(len(results['documents'][0])):
            context = {
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            }
            relevant_contexts.append(context)
        
        return relevant_contexts

    def list_entries(self, collection_type: str = "dialogue"):
        """
        List all entries in a specified collection.
        
        :param collection_type: Type of collection to list ('dialogue' or 'article')
        :return: List of entries with their metadata
        """
        # Select the appropriate collection
        collection = (self.dialogue_collection if collection_type == "dialogue" 
                      else self.article_collection)
        
        # Retrieve all entries
        entries = collection.get()
        
        # Process entries
        formatted_entries = []
        for i in range(len(entries['ids'])):
            entry = {
                'id': entries['ids'][i],
                'text': entries['documents'][i],
                'metadata': entries['metadatas'][i]
            }
            formatted_entries.append(entry)
        
        return formatted_entries

# # Example usage demonstration
# def main():
#     # Initialize the RAG Database Manager
#     rag_manager = RAGDatabaseManager()
    
#     # Demonstrate database path retrieval
#     print("Database Path:", rag_manager.get_database_path())
    
#     # Add a dialogue
#     dialogue_id = rag_manager.add_dialogue(
#         "Claude is an AI assistant created by Anthropic to be helpful, honest, and harmless.",
#         context="Company background",
#         tags=["AI", "Anthropic"]
#     )
    
#     # Add an article
#     article_id = rag_manager.add_article(
#         "Large language models are advanced AI systems trained on vast amounts of text data to understand and generate human-like text.",
#         title="Understanding Large Language Models",
#         tags=["AI", "Machine Learning"]
#     )
    
#     # Retrieve relevant context
#     context = rag_manager.retrieve_relevant_context("Tell me about AI assistants")
#     print("Retrieved Context:", context)

# if __name__ == "__main__":
#     main()