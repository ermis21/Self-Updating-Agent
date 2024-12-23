import streamlit as st
import os

class CodeFileParser:
    @staticmethod
    def parse_code_file(uploaded_file):
        """
        Parse various code files and extract their content.
        
        :param uploaded_file: Uploaded file object
        :return: Extracted text content
        """
        # Get file extension and name
        file_name = uploaded_file.name
        file_extension = os.path.splitext(file_name)[1].lower()

        try:
            # Read file content
            file_content = uploaded_file.getvalue().decode('utf-8')
            
            # Optional: Add more sophisticated parsing for specific file types
            if file_extension in ['.py', '.js', '.ts', '.cpp', '.java', '.c', '.cs', '.rb', '.php', '.go', '.rs', '.swift']:
                # For most code files, we'll just use the raw content
                return file_content
            
            # For other text-based files
            return file_content
        
        except UnicodeDecodeError:
            # Handle binary files or files with different encoding
            st.warning(f"Could not parse {file_name}. Ensure it's a text-based file.")
            return None