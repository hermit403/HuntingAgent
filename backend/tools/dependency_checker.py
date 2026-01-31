from typing import Dict, Any
import subprocess
import json
import tempfile
import os
from tools.base import BaseTool


class DependencyChecker(BaseTool):
    def __init__(self):
        super().__init__(
            tool_id="dependency_checker",
            name="Dependency Checker",
            description="Check for known vulnerabilities in dependencies using Safety"
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requirements = params.get("requirements", "")
        
        if not requirements:
            return {"error": "No requirements provided"}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(requirements)
                temp_file = f.name
            
            result = subprocess.run(
                ['safety', 'check', '-r', temp_file, '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            os.unlink(temp_file)
            
            if result.stdout:
                vulnerabilities = json.loads(result.stdout)
                return {
                    "vulnerabilities": vulnerabilities,
                    "total": len(vulnerabilities)
                }
            else:
                return {"vulnerabilities": [], "total": 0}
        except subprocess.TimeoutExpired:
            return {"error": "Dependency check timeout"}
        except Exception as e:
            self.logger.error(f"Dependency check failed: {str(e)}")
            return {"error": str(e)}
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return "requirements" in params and isinstance(params["requirements"], str)
