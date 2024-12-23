from groq import Groq
from rag_database import RAGDatabaseManager
import streamlit as st




class RAGChatbot:
    def __init__(self, apikey, model="llama3-8b-8192", max_context_tokens=4000):
        """
        Initialize the RAG-enhanced chatbot.
        
        :param model: Groq model to use
        :param max_context_tokens: Maximum tokens for retrieved context
        """
        # Initialize Groq client
        self.groq_client = Groq(api_key=apikey)
        
        # Initialize RAG Database Manager
        self.rag_manager = RAGDatabaseManager()
        
        # Chatbot configuration
        self.model = model
        self.max_context_tokens = max_context_tokens
    def _format_context(self, contexts):
        """
        Format retrieved contexts into a string.
        
        :param contexts: List of context dictionaries
        :return: Formatted context string
        """
        formatted_contexts = []
        for context in contexts:
            # Include text and metadata in context
            context_str = f"Context (Type: {context['metadata'].get('type', 'unknown')}):\n{context['text']}"
            formatted_contexts.append(context_str)
        
        return "\n\n".join(formatted_contexts)

    def get_chat_response(self, messages, query):
        """
        Get a chat response with RAG-enhanced context.
        
        :param messages: Conversation history
        :param query: Current user query
        :return: AI-generated response
        """
        # Retrieve relevant context
        dialogue_contexts = self.rag_manager.retrieve_relevant_context(query, "dialogue")
        article_contexts = self.rag_manager.retrieve_relevant_context(query, "article")
        
        # Combine contexts
        all_contexts = dialogue_contexts + article_contexts
        
        # Format context
        context_str = self._format_context(all_contexts)
        
        # Prepare augmented messages with context
        augmented_messages = [
            {"role": "system", "content": f"Use the following context to inform your response:\n{context_str}"}
        ] + messages

        try:
            # Generate chat completion
            chat_completion = self.groq_client.chat.completions.create(
                messages=augmented_messages,
                model=self.model,
                max_tokens=self.max_context_tokens,
                temperature=0.7,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            st.error(f"Error getting chat response: {e}")
            return None