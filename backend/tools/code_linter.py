from typing import Dict, Any
import subprocess
import json
import tempfile
import os
from tools.base import BaseTool


class CodeLinter(BaseTool):
    def __init__(self):
        super().__init__(
            tool_id="code_linter",
            name="Code Linter",
            description="Check code style and quality using Flake8"
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        
        if not code:
            return {"error": "No code provided"}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['flake8', '--format=json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.unlink(temp_file)
            
            if result.stdout:
                issues = json.loads(result.stdout)
                return {
                    "issues": issues,
                    "total": len(issues)
                }
            else:
                return {"issues": [], "total": 0}
        except subprocess.TimeoutExpired:
            return {"error": "Linting timeout"}
        except Exception as e:
            self.logger.error(f"Code linting failed: {str(e)}")
            return {"error": str(e)}
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return "code" in params and isinstance(params["code"], str)
