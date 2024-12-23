import os
import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
import ast
import builtins
from typing import Dict, Any, Optional
import threading
import time
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from queue import Queue

class CodeExecutionManager:
    """
        CodeExecutionManager: A class for managing the execution of Python code in a controlled and safe environment.

        This class enables the execution of Python code while enforcing safety controls such as restricting the usage of certain built-ins, modules, and operations. It ensures that the code runs within a specified timeout and captures the output and errors of the execution. The manager also checks the code for unsafe operations or imports before execution to prevent potentially harmful actions.

        Attributes:
        - timeout: The maximum time (in seconds) allowed for code execution.
        - safe_builtins: A set of built-in Python functions and types that are allowed for use in the executed code.
        - allowed_modules: A set of modules that are allowed to be imported in the executed code.
        - result_queue: A queue for passing results between threads, used to capture execution output, error messages, and other details.

        Methods:
        - __init__(timeout=30): Initializes the CodeExecutionManager with a specified timeout and safety settings.
        - _is_safe_code(code): Analyzes the code's Abstract Syntax Tree (AST) to ensure it does not contain unsafe operations, imports, or dangerous calls (e.g., eval, exec).
        - execute_code(code): Executes the provided code in a controlled environment with output capture. It ensures the code is safe to execute, and returns a dictionary containing the success status, output, error message (if any), and execution time.

        Example usage:
        - Initialize the manager using `CodeExecutionManager(timeout=60)`.
        - Use the `execute_code` method to run Python code, such as:
        result = manager.execute_code("x = 2 + 2")
        print(result)
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the code execution manager with safety controls.
        
        :param timeout: Maximum execution time in seconds
        """
        self.timeout = timeout
        self.safe_builtins = {
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytes', 'chr', 
            'dict', 'dir', 'divmod', 'enumerate', 'filter', 'float', 'format', 
            'frozenset', 'hash', 'hex', 'int', 'isinstance', 'issubclass', 'len', 
            'list', 'map', 'max', 'min', 'next', 'oct', 'ord', 'pow', 'print', 
            'range', 'repr', 'reversed', 'round', 'set', 'slice', 'sorted', 
            'str', 'sum', 'tuple', 'type', 'zip'
        }
        
        self.allowed_modules = {
            'math', 'random', 'datetime', 'collections', 'itertools', 
            'functools', 'operator', 'string', 're', 'json', 'copy'
        }
        
        # Queue for passing results between threads
        self.result_queue = Queue()
    
    def _is_safe_code(self, code: str) -> bool:
        """Check if the code is safe to execute by analyzing the AST."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Check for unsafe built-in usage
                if isinstance(node, ast.Name) and node.id not in self.safe_builtins:
                    if node.id in dir(builtins):
                        return False
                
                # Check for unsafe imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] not in self.allowed_modules:
                            return False
                
                if isinstance(node, ast.ImportFrom):
                    if node.module.split('.')[0] not in self.allowed_modules:
                        return False
                
                # Check for dangerous operations
                if isinstance(node, ast.Delete):
                    return False
                
                # Check for eval and exec calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in {'eval', 'exec'}:
                            return False
                
                # Check for attribute access that might be dangerous
                if isinstance(node, ast.Attribute):
                    if node.attr.startswith('__'):
                        return False
            
            return True
        except SyntaxError:
            return False
    
    # Rest of the class implementation remains the same...
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code in a controlled environment with output capture."""
        if not self._is_safe_code(code):
            return {
                'success': False,
                'output': '',
                'error': 'Code contains unsafe operations or imports',
                'execution_time': 0
            }
        
        # Get the current Streamlit context
        ctx = get_script_run_ctx()
        
        # Capture stdout and stderr
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        def execute():
            # Set the Streamlit context in the execution thread
            if ctx:
                from streamlit.runtime.scriptrunner import add_script_run_ctx
                add_script_run_ctx(threading.current_thread(), ctx)
            
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                try:
                    # Create a new dictionary for local variables
                    local_vars = {}
                    restricted_globals = {
                        '__builtins__': dict((name, getattr(builtins, name))
                                           for name in self.safe_builtins)
                    }
                    
                    # Execute the code
                    exec(code, restricted_globals, local_vars)
                    
                    self.result_queue.put({
                        'success': True,
                        'output': output_buffer.getvalue(),
                        'error': '',
                        'local_vars': local_vars
                    })
                except Exception as e:
                    self.result_queue.put({
                        'success': False,
                        'output': output_buffer.getvalue(),
                        'error': f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                        'local_vars': {}
                    })
        
        # Create and start execution thread
        start_time = time.time()
        execution_thread = threading.Thread(target=execute)
        execution_thread.start()
        
        # Wait for execution with timeout
        execution_thread.join(timeout=self.timeout)
        execution_time = time.time() - start_time
        
        if execution_thread.is_alive():
            # Timeout occurred
            return {
                'success': False,
                'output': output_buffer.getvalue(),
                'error': f'Execution timed out after {self.timeout} seconds',
                'execution_time': self.timeout
            }
        
        # Get the result from the queue
        result = self.result_queue.get()
        result['execution_time'] = round(execution_time, 3)
        
        return result


# class CodeExecutionManager:
#     def __init__(self, timeout: int = 30):
#         """
#         Initialize the code execution manager with safety controls.
        
#         :param timeout: Maximum execution time in seconds
#         """
#         self.timeout = timeout
#         self.safe_builtins = {
#             'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytes', 'chr', 
#             'dict', 'dir', 'divmod', 'enumerate', 'filter', 'float', 'format', 
#             'frozenset', 'hash', 'hex', 'int', 'isinstance', 'issubclass', 'len', 
#             'list', 'map', 'max', 'min', 'next', 'oct', 'ord', 'pow', 'print', 
#             'range', 'repr', 'reversed', 'round', 'set', 'slice', 'sorted', 
#             'str', 'sum', 'tuple', 'type', 'zip'
#         }
        
#         self.allowed_modules = {
#             'math', 'random', 'datetime', 'collections', 'itertools', 
#             'functools', 'operator', 'string', 're', 'json', 'copy'
#         }
        
#         # Queue for passing results between threads
#         self.result_queue = Queue()
    
#     def _is_safe_code(self, code: str) -> bool:
#         """Check if the code is safe to execute by analyzing the AST."""
#         try:
#             tree = ast.parse(code)
            
#             for node in ast.walk(tree):
#                 if isinstance(node, ast.Name) and node.id not in self.safe_builtins:
#                     if node.id in dir(builtins):
#                         return False
                
#                 if isinstance(node, ast.Import):
#                     for alias in node.names:
#                         if alias.name.split('.')[0] not in self.allowed_modules:
#                             return False
                
#                 if isinstance(node, ast.ImportFrom):
#                     if node.module.split('.')[0] not in self.allowed_modules:
#                         return False
                
#                 if isinstance(node, (ast.Delete, ast.Exec)):
#                     return False
                
#             return True
#         except SyntaxError:
#             return False
    
#     def execute_code(self, code: str) -> Dict[str, Any]:
#         """Execute code in a controlled environment with output capture."""
#         if not self._is_safe_code(code):
#             return {
#                 'success': False,
#                 'output': '',
#                 'error': 'Code contains unsafe operations or imports',
#                 'execution_time': 0
#             }
        
#         # Get the current Streamlit context
#         ctx = get_script_run_ctx()
        
#         # Capture stdout and stderr
#         output_buffer = io.StringIO()
#         error_buffer = io.StringIO()
        
#         def execute():
#             # Set the Streamlit context in the execution thread
#             if ctx:
#                 from streamlit.runtime.scriptrunner import add_script_run_ctx
#                 add_script_run_ctx(threading.current_thread(), ctx)
            
#             with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
#                 try:
#                     # Create a new dictionary for local variables
#                     local_vars = {}
#                     restricted_globals = {
#                         '__builtins__': dict((name, getattr(builtins, name))
#                                            for name in self.safe_builtins)
#                     }
                    
#                     # Execute the code
#                     exec(code, restricted_globals, local_vars)
                    
#                     self.result_queue.put({
#                         'success': True,
#                         'output': output_buffer.getvalue(),
#                         'error': '',
#                         'local_vars': local_vars
#                     })
#                 except Exception as e:
#                     self.result_queue.put({
#                         'success': False,
#                         'output': output_buffer.getvalue(),
#                         'error': f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
#                         'local_vars': {}
#                     })
        
#         # Create and start execution thread
#         start_time = time.time()
#         execution_thread = threading.Thread(target=execute)
#         execution_thread.start()
        
#         # Wait for execution with timeout
#         execution_thread.join(timeout=self.timeout)
#         execution_time = time.time() - start_time
        
#         if execution_thread.is_alive():
#             # Timeout occurred
#             return {
#                 'success': False,
#                 'output': output_buffer.getvalue(),
#                 'error': f'Execution timed out after {self.timeout} seconds',
#                 'execution_time': self.timeout
#             }
        
#         # Get the result from the queue
#         result = self.result_queue.get()
#         result['execution_time'] = round(execution_time, 3)
        
#         return result

@st.cache_resource
def get_code_executor():
    """Get or create a CodeExecutionManager instance."""
    return CodeExecutionManager()