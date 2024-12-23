import os
import streamlit as st
from code_exec import CodeExecutionManager, get_code_executor
from Chatbot import RAGChatbot
from code_parser import CodeFileParser
from Snippet_maching import SnippetMatcher, SnippetUpdater
import pypdf, shutil
import io

# Folder to save code snippets for Docker execution
CODE_SNIPPET_FOLDER = "./code_snippets"
os.makedirs(CODE_SNIPPET_FOLDER, exist_ok=True)
EXECUTE = False

def create_rag_chatbot_ui():
    """
    Create Streamlit UI for RAG-enhanced chatbot with deployment capabilities
    """
    # Page configuration
    st.set_page_config(page_title="RAG Llama 3 Chatbot", page_icon="🤖")
    st.title("🤖 RAG-Enhanced Llama 3 Chatbot")

    # Initialize components
    chatbot = RAGChatbot(apikey=APIKEY,model=MODEL)
    rag_manager = chatbot.rag_manager
    code_executor = get_code_executor()
    snippet_placer = SnippetMatcher()

    # Initialize session state for code blocks
    if "code_blocks" not in st.session_state:
        st.session_state.code_blocks = {}
    if 'snippet_matcher' not in st.session_state:
        st.session_state.snippet_matcher = SnippetMatcher()
    if 'snippet_updater' not in st.session_state:
        st.session_state.snippet_updater = SnippetUpdater()
        
    # Show database information
    st.sidebar.header("Database Information")
    st.sidebar.info(f"Vector Database Location: {rag_manager.get_database_path()}")

    # Code Execution Controls
    st.sidebar.header("Code Execution")
    st.session_state.execute = st.sidebar.checkbox("Enable Code Execution", value=False)

    if st.session_state.execute:
        st.sidebar.warning("""
        ⚠️ Code execution is enabled. Only run code you trust.
        Security measures are in place, but use with caution.
        """)

    # Initialize messages if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm a RAG-enhanced chatbot. How can I help you today?"},
            {"role": "system", "content": "Please enter your query or topic to start the conversation"}
        ]

    # Conversation Management
    st.sidebar.header("Conversation Management")
    # Always show save conversation UI
    save_context = st.sidebar.text_input(
        "Optional context for this conversation", 
        key="conversation_context"
    )
    
    save_tags = st.sidebar.text_input(
        "Tags (comma-separated, optional)",
        key="conversation_tags"
    )
    
    # Save conversation button (always visible)
    if st.sidebar.button("Save Current Conversation", key="save_conversation_btn"):
        # Check if there are enough messages
        if len(st.session_state.messages) > 2:  # More than initial welcome message
            # Combine dialogue messages into a single text
            conversation_text = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}" 
                for msg in st.session_state.messages 
                if msg['role'] != 'system'
            ])
            
            # Process tags
            tags = [tag.strip() for tag in save_tags.split(",") if tag.strip()]
            
            # Add dialogue to RAG database
            rag_manager.add_dialogue(
                conversation_text, 
                context=save_context,
                tags=tags or ["conversation"]
            )
            st.sidebar.success("Conversation saved successfully!")
        else:
            st.sidebar.warning("Not enough messages to save.")

    # File Upload Sections
    st.sidebar.header("File Uploads")
    
    # PDF Article Upload
    with st.sidebar.expander("Upload PDF"):
        uploaded_pdf = st.file_uploader(
            "Upload PDF Article", 
            type=['pdf'], 
            key="article_pdf_upload"
        )
        
        if uploaded_pdf is not None:
            pdf_title = st.text_input(
                "PDF Title", 
                value=uploaded_pdf.name.replace('.pdf', ''),
                key="pdf_article_title"
            )
            pdf_tags = st.text_input(
                "PDF Tags (comma-separated)", 
                key="pdf_article_tags"
            )
            
            if st.button("Save PDF", key="save_pdf_btn"):
                try:
                    pdf_reader = pypdf.PdfReader(uploaded_pdf)
                    
                    # Extract text from all pages
                    article_text = "\n".join([
                        page.extract_text() for page in pdf_reader.pages
                    ])
                    
                    # Process tags
                    tags = [tag.strip() for tag in pdf_tags.split(",") if tag.strip()]
                    
                    # Add article to RAG database
                    rag_manager.add_article(
                        article_text, 
                        title=pdf_title, 
                        tags=tags
                    )
                    st.sidebar.success("PDF saved successfully!")
                
                except Exception as e:
                    st.sidebar.error(f"Error processing PDF: {e}")

    # Code File Upload
    with st.sidebar.expander("Upload Code File"):
        uploaded_code = st.file_uploader(
            "Upload Code File", 
            type=['py', 'js', 'ts', 'cpp', 'java', 'c', 'cs', 'rb', 'php', 'go', 'rs', 'swift', 'txt'],
            key="code_file_upload"
        )
        
        if uploaded_code is not None:
            code_title = st.text_input(
                "Code File Title", 
                value=uploaded_code.name,
                key="code_file_title"
            )
            code_tags = st.text_input(
                "Code File Tags (comma-separated)", 
                key="code_file_tags"
            )
            
            if st.button("Save Code File", key="save_code_btn"):
                # Parse code file
                code_content = CodeFileParser.parse_code_file(uploaded_code)
                
                if code_content:
                    # Process tags
                    tags = [tag.strip() for tag in code_tags.split(",") if tag.strip()]
                    
                    # Add code file to RAG database
                    rag_manager.add_article(
                        code_content, 
                        title=code_title, 
                        tags=tags or ["code"]
                    )
                    st.sidebar.success("Code file saved successfully!")
                else:
                    st.sidebar.error("Failed to parse code file.")

    # Chat interface
    # Chat interface with improved code execution and deployment
    # Store analysis results in session state
    for msg_idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                code_blocks = extract_code_blocks(message["content"])

                for block_idx, (language, code) in enumerate(code_blocks):
                    block_key = f"code_block_{msg_idx}_{block_idx}"
                    analysis_key = f"analysis_{block_key}"
                    selected_file_key = f"selected_file_{block_key}"

                    # Initialize session state for code blocks
                    if block_key not in st.session_state.code_blocks:
                        st.session_state.code_blocks[block_key] = {
                            'code': code,
                            'language': language,
                            'description': code.split('\n')[0] if code else "No description",
                            'executed': False,
                            'output': None,
                            'error': None,
                            'execution_time': None
                        }

                    expand_state = st.session_state.get(f"expand_state_{block_key}", True)

                    with st.expander(f"Code Block {block_idx + 1}", expanded=expand_state):
                        st.code(code, language=language)

                        # Execute section
                        if st.session_state.execute:
                            if st.button("Run", key=f"run_{block_key}"):
                                with st.spinner("Executing code..."):
                                    result = code_executor.execute_code(code)

                                    # Store execution results
                                    st.session_state.code_blocks[block_key].update({
                                        'executed': True,
                                        'output': result['output'],
                                        'error': result['error'],
                                        'execution_time': result['execution_time']
                                    })

                                if result['success']:
                                    if result['output']:
                                        st.success("Code executed successfully!")
                                        st.code(result['output'], language='text')
                                    else:
                                        st.success("Code executed successfully (no output).")
                                else:
                                    st.error("Execution Error:")
                                    st.code(result['error'], language='text')

                                st.info(f"Execution time: {result['execution_time']}s")

                        # Deployment section
                        st.markdown("### Deployment Options")
                        deployment_folder = st.text_input(
                            "Deployment Directory",
                            value=os.path.dirname(os.path.realpath(__file__)),
                            key=f"deploy_dir_{block_key}"
                        )

                        # Store analysis results in session state when analyze button is clicked
                        if st.button("Analyze Deployment Location", key=f"analyze_{block_key}"):
                            with st.spinner("Analyzing deployment location..."):
                                if not os.path.exists(deployment_folder):
                                    st.error("Deployment directory does not exist")
                                else:
                                    suitable_files = st.session_state.snippet_matcher.check_folder_for_snippet(
                                        deployment_folder,
                                        st.session_state.code_blocks[block_key]['code']
                                    )
                                    # Store analysis results in session state
                                    st.session_state[analysis_key] = suitable_files

                        # Display analysis results if they exist in session state
                        if analysis_key in st.session_state and st.session_state[analysis_key]:
                            suitable_files = st.session_state[analysis_key]
                            st.write("📁 Found suitable files for deployment:")

                            # Create radio buttons for file selection
                            file_options = [
                                f"{os.path.basename(file)} ({conf:.2f})"
                                for file, conf, _, _, _ in suitable_files
                            ]
                            
                            selected_file = st.radio(
                                "Select file to deploy to:",
                                file_options,
                                key=selected_file_key
                            )

                            # Get the index of selected file
                            selected_idx = file_options.index(selected_file)
                            file_path, confidence, matched_code, start_line, end_line = suitable_files[selected_idx]

                            # Show confidence metric
                            st.metric("Confidence Score", f"{confidence:.2%}")

                            # Show matched code from the file
                            st.markdown("### Matched Code from File:")
                            st.code(matched_code, language='python')

                            # Calculate updated code
                            with open(file_path, 'r') as f:
                                existing_code = f.read()

                            updated_code = st.session_state.snippet_updater.calculate_updated_code(
                                existing_code,
                                st.session_state.code_blocks[block_key]['code'],
                                start_line=start_line,
                                end_line=end_line
                            )

                            # Deploy button
                            if st.button(f"Deploy to {os.path.basename(file_path)}", key=f"deploy_{block_key}_{selected_idx}"):
                                try:
                                    backup_path = st.session_state.snippet_updater.backup_and_write_code(
                                        file_path, 
                                        updated_code
                                    )                                    
                                    st.success(f"Successfully deployed to {os.path.basename(file_path)}")
                                    st.info(f"Backup created at {backup_path}")
                                    st.session_state[f"expand_state_{block_key}"] = False
                                except Exception as e:
                                    st.error(f"Deployment failed: {str(e)}")
                                    if os.path.exists(backup_path):
                                        shutil.copy2(backup_path, file_path)
                                        st.warning("Restored from backup due to error")

                        elif analysis_key in st.session_state:
                            st.warning("No suitable files found for deployment")
    # User input handling
    if prompt := st.chat_input("What would you like to chat about?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chatbot.get_chat_response(st.session_state.messages, prompt)
                
            if response:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

def create_enhanced_diff_view(original_code: str, updated_code: str) -> str:
    """
    Creates an enhanced diff view with better syntax highlighting and visual indicators
    """
    import difflib
    
    diff = list(difflib.ndiff(original_code.splitlines(keepends=True), 
                             updated_code.splitlines(keepends=True)))
    
    diff_html = """
    <style>
        .diff-view {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            white-space: pre;
            margin: 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            line-height: 1.4;
        }
        .diff-line {
            display: flex;
            margin: 0;
            padding: 0 5px;
        }
        .diff-added {
            background-color: #e6ffe6;
            border-left: 3px solid #28a745;
        }
        .diff-removed {
            background-color: #ffe6e6;
            border-left: 3px solid #dc3545;
        }
        .diff-unchanged {
            border-left: 3px solid transparent;
        }
        .line-number {
            color: #6c757d;
            padding-right: 10px;
            user-select: none;
            min-width: 40px;
            text-align: right;
        }
        .line-content {
            flex-grow: 1;
        }
        .keyword { color: #0033cc; }
        .string { color: #008000; }
        .comment { color: #808080; font-style: italic; }
        .number { color: #0066cc; }
    </style>
    <div class="diff-view">
    """
    
    line_number = 1
    for line in diff:
        if line.startswith('+ '):
            class_name = 'diff-added'
            content = line[2:]
        elif line.startswith('- '):
            class_name = 'diff-removed'
            content = line[2:]
        elif line.startswith('  '):
            class_name = 'diff-unchanged'
            content = line[2:]
        else:
            continue
            
        # Basic syntax highlighting
        content = (content
            .replace('def ', '<span class="keyword">def </span>')
            .replace('class ', '<span class="keyword">class </span>')
            .replace('import ', '<span class="keyword">import </span>')
            .replace('from ', '<span class="keyword">from </span>')
            .replace('return ', '<span class="keyword">return </span>')
        )
        
        diff_html += f"""
        <div class="diff-line {class_name}">
            <span class="line-number">{line_number}</span>
            <span class="line-content">{content}</span>
        </div>
        """
        line_number += 1
    
    diff_html += "</div>"
    return diff_html

def extract_code_blocks(content: str) -> list[tuple]:
    """Extract code blocks from markdown content."""
    import re
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    return [(lang or 'python', code.strip()) for lang, code in matches]

if __name__ == "__main__":
    create_rag_chatbot_ui()# created backup
