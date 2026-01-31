from typing import Dict, Any
import json
import asyncio
import os
from pathlib import Path
from tools.base import BaseTool
from tools.registry import skill_registry

class JSEvaluatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            tool_id="js_evaluator",
            name="JS Evaluator",
            description="Execute JavaScript code using Node.js vm module"
        )
        self.executor_script = Path(__file__).parent / "executor.js"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code")
        if not code:
            raise ValueError("Code parameter is required")
        context = params.get("context", {})
        payload = json.dumps({
            "code": code,
            "context": context
        })

        def _get_heap_mb() -> int:
            env_heap = os.getenv("TOOL_NODE_HEAP_MB")
            if env_heap and env_heap.isdigit():
                return int(env_heap)
            env_limit = os.getenv("TOOL_MAX_MEMORY", "256")
            if env_limit.lower().endswith("m") and env_limit[:-1].isdigit():
                return max(32, int(env_limit[:-1]) // 2)
            if env_limit.isdigit():
                return max(32, int(env_limit) // 2)
            return 128

        try:
            env = os.environ.copy()
            env["NODE_OPTIONS"] = f"--max-old-space-size={_get_heap_mb()}"
            process = await asyncio.create_subprocess_exec(
                "node",
                str(self.executor_script),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            stdout, stderr = await process.communicate(input=payload.encode())
            if process.returncode != 0 and stderr:
                 error_msg = stderr.decode().strip()
                 self.logger.error(f"Node process error: {error_msg}")
                 return {"error": f"Process error: {error_msg}", "context": {}}
            output_str = stdout.decode().strip()
            if not output_str:
                 return {"result": None, "context": {}}
            try:
                output = json.loads(output_str)
                if "error" in output:
                    return {"error": output["error"], "context": {}}
                return {"result": output.get("result"), "context": {}} 
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON output from executor: {output_str}", "context": {}}
        except Exception as e:
            self.logger.error(f"JS Execution error: {str(e)}")
            return {
                "error": str(e),
                "context": {}
            }

tool_instance = JSEvaluatorTool()
skill_registry.register_tool(tool_instance)

tools = [
    {
        "name": "js_evaluator",
        "description": "Execute JavaScript code using Node.js vm",
        "function": "execute"
    }
]
