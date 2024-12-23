import os
import ast
from typing import List, Tuple, Dict
from difflib import unified_diff
import shutil

class SnippetMatcher:
    """Handles the logic for finding where code snippets best fit in existing code."""
    
    def check_folder_for_snippet(self, folder: str, snippet: str) -> List[Tuple[str, float, str, int, int]]:
        """
        Searches all Python files in the specified folder for the best placement for the snippet.
        Returns list of (file_path, confidence_score, matched_code, start_line, end_line)
        """
        if not os.path.exists(folder):
            raise ValueError(f"Folder not found: {folder}")
        if not snippet.strip():
            raise ValueError("Snippet cannot be empty")

        # Validate snippet syntax
        try:
            ast.parse(snippet)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in snippet: {str(e)}")

        placements = []
        python_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.py')]

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as file:
                    target_code = file.read()
                if not target_code.strip():
                    continue

                scores = self._calculate_matching_scores(target_code, snippet)
                confidence = self._calculate_confidence_score(scores)

                if confidence > 0.3:
                    # First, match based on the full snippet
                    match_start, match_end = self._find_best_match(target_code, snippet)
                    
                    # Now, match the last 5 lines separately
                    snippet_last_5_lines = "\n".join(snippet.splitlines()[-5:])
                    match_start_end, match_end_end = self._find_best_match(target_code, snippet_last_5_lines)
                    
                    # Choose the best match: If end match gives a larger end line, use it
                    if match_end_end > match_end:
                        match_end = match_end_end
                    
                    lines = target_code.splitlines()
                    matched_code = "\n".join(lines[match_start - 1:match_end])
                    

                    if match_start != -1:
                        placements.append((py_file, confidence, matched_code, match_start, match_end))

            except Exception as e:
                print(f"Error processing {py_file}: {str(e)}")
                continue

        return sorted(placements, key=lambda x: x[1], reverse=True)[:2]

    def _calculate_matching_scores(self, target_code: str, snippet: str) -> Dict[str, float]:
        """Calculates various matching scores between target code and snippet."""
        snippet_first_line = snippet.splitlines()[0].strip()
        snippet_last_lines = snippet.splitlines()[-3:]  # Adjust the last 3 lines (can be customized)
        
        scores = {
            'first_line_match': self._first_line_match(target_code, snippet_first_line),
            'string_match': self._string_similarity(target_code, snippet),
            'ast_similarity': self._ast_similarity(target_code, snippet),
            'keyword_match': self._keyword_match(target_code, snippet),
            'end_line_match': self._end_line_match(target_code, snippet_last_lines)
        }
        return scores

    def _first_line_match(self, target_code: str, first_line: str) -> float:
        """Specifically matches the first line of the snippet in the target code."""
        target_lines = target_code.splitlines()
        for line in target_lines:
            if line.strip() == first_line:
                return 1.0
            elif first_line in line.strip():
                return 0.8
        return 0.0

    def _end_line_match(self, target_code: str, last_lines: List[str]) -> float:
        """Matches the last few lines of the snippet to the target code."""
        target_lines = target_code.splitlines()
        for i in range(len(target_lines) - len(last_lines) + 1):
            if all(last_lines[j].strip() in target_lines[i + j].strip() for j in range(len(last_lines))):
                return 1.0  # Full match of last lines
            elif any(last_lines[j].strip() in target_lines[i + j].strip() for j in range(len(last_lines))):
                return 0.8  # Partial match
        return 0.0

    def _string_similarity(self, target_code: str, snippet: str) -> float:
        """Calculates string-based similarity."""
        if snippet in target_code:
            return 1.0
        return len(set(snippet.split()) & set(target_code.split())) / len(set(snippet.split()))

    def _ast_similarity(self, target_code: str, snippet: str) -> float:
        """Calculates similarity based on AST structures."""
        try:
            target_ast = ast.parse(target_code)
            snippet_ast = ast.parse(snippet)
            return len(list(ast.walk(snippet_ast))) / len(list(ast.walk(target_ast)))
        except Exception:
            return 0.0

    def _keyword_match(self, target_code: str, snippet: str) -> float:
        """Calculates similarity based on matching keywords."""
        try:
            snippet_keywords = {node.id for node in ast.walk(ast.parse(snippet)) 
                              if isinstance(node, ast.Name)}
            target_keywords = {node.id for node in ast.walk(ast.parse(target_code)) 
                             if isinstance(node, ast.Name)}
            if not snippet_keywords:
                return 0.0
            return len(snippet_keywords & target_keywords) / len(snippet_keywords)
        except Exception:
            return 0.0

    def _calculate_confidence_score(self, scores: Dict[str, float]) -> float:
        """Calculates weighted confidence score with emphasis on first and last line matching."""
        weights = {
            'first_line_match': 0.3,  # Adjusted weight for first line matching
            'string_match': 0.2,
            'ast_similarity': 0.2,
            'keyword_match': 0.1,
            'end_line_match': 0.2  # Added weight for end line match
        }
        return sum(scores[key] * weights.get(key, 0) for key in scores)

    def _find_best_match(self, target_code: str, snippet: str) -> Tuple[int, int]:
        """Finds the best matching segment in the target code."""
        lines = target_code.splitlines()
        snippet_lines = snippet.splitlines()
        first_line = snippet_lines[0].strip()
        
        best_match_score = 0
        best_start = -1
        best_end = -1

        # Match first line
        for i, line in enumerate(lines):
            if first_line in line.strip():
                match_score = 1  # Start with a score for first line match
                for j in range(1, min(len(snippet_lines), len(lines) - i)):
                    if snippet_lines[j].strip() in lines[i + j].strip():
                        match_score += 1
                
                # Now, try to match the last lines separately
                end_line_score = self._end_line_match(target_code, snippet_lines[-3:])  # Adjust number of lines if needed
                match_score += end_line_score
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_start = i + 1
                    best_end = i + len(snippet_lines)

        return best_start, best_end


import os
import shutil
from typing import List

class SnippetUpdater:
    """Handles the logic for updating code with new snippets while maintaining proper indentation."""

    def calculate_updated_code(self, existing_code: str, snippet: str, start_line: int, end_line: int) -> str:
        """Returns the updated code with the snippet properly indented."""
        lines = existing_code.splitlines()

        # Get the indentation of the first line of the target block being replaced
        target_indentation = self._get_block_indentation(lines, start_line)

        # Get the indentation of the first line of the snippet
        snippet_indentation = self._get_snippet_indentation(snippet)

        # Adjust the snippet indentation to match the target block's indentation
        adjusted_snippet = self._adjust_snippet_indentation(snippet, target_indentation, snippet_indentation)

        # Replace the target block
        updated_lines = lines[:start_line - 1] + adjusted_snippet.splitlines() + lines[end_line:]
        return "\n".join(updated_lines)

    def _get_block_indentation(self, all_lines: List[str], start_line: int) -> str:
        """Determines the correct indentation for the first line of the target block."""
        if start_line - 1 < len(all_lines):
            first_line = all_lines[start_line - 1]
            return first_line[:len(first_line) - len(first_line.lstrip())]
        return ""

    def _get_snippet_indentation(self, snippet: str) -> str:
        """Determines the indentation of the first line of the snippet."""
        lines = snippet.splitlines()
        if lines:
            first_line = lines[0]
            return first_line[:len(first_line) - len(first_line.lstrip())]
        return ""

    def _adjust_snippet_indentation(self, snippet: str, target_indentation: str, snippet_indentation: str) -> str:
        """Adjusts snippet indentation to match target while preserving relative indentation."""
        lines = snippet.splitlines()
        if not lines:
            return snippet

        # Calculate the difference in indentation between the snippet's first line and target indentation
        indent_diff = len(target_indentation) - len(snippet_indentation)

        # Adjust each line's indentation
        adjusted_lines = []
        for line in lines:
            if not line.strip():  # Keep blank lines as they are
                adjusted_lines.append(line)
                continue

            # Remove existing indentation and apply the new indentation
            stripped = line[len(snippet_indentation):] if len(line) > len(snippet_indentation) else line.lstrip()
            adjusted_lines.append(f"{target_indentation}{stripped}")

        return "\n".join(adjusted_lines)

    def backup_and_write_code(self, file_path: str, updated_code: str) -> str:
        """Creates a backup and writes the updated code to the file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        backup_path = f"{os.path.splitext(file_path)[0]}.old"
        shutil.copy2(file_path, backup_path)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_code)

        return backup_path
