from typing import Dict, Any, List, Optional
import logging
import threading
from tools.base import BaseTool
from core.llm_client import llm_client
import json


class SkillRegistry:
    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger("SkillRegistry")
        self._lock = threading.RLock()
    
    def register_skill(self, skill_name: str, skill_info: Dict[str, Any]):
        with self._lock:
            self.skills[skill_name] = skill_info
            self.logger.info(f"Registered skill: {skill_name}")
    
    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.skills.get(skill_name)
    
    def list_skills(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.skills.values())

    def unregister_skill(self, skill_name: str):
        with self._lock:
            if skill_name in self.skills:
                del self.skills[skill_name]
                self.logger.info(f"Unregistered skill: {skill_name}")
    
    def register_tool(self, tool: BaseTool):
        with self._lock:
            self.tools[tool.tool_id] = tool
            self.logger.info(f"Registered tool: {tool.tool_id}")
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        with self._lock:
            return self.tools.get(tool_id)
    
    async def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.get_skill(skill_name)

        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")

        tools = skill.get("tools", [])
        allowed_tools = self._normalize_allowed_tools(skill.get("allowed_tools"))
        filtered_tools = self._filter_tools_by_allowlist(tools, allowed_tools)

        tool_schemas = [self._to_tool_schema(t) for t in filtered_tools]
        messages = self._build_messages(skill, params)

        assistant_message = None
        tool_calls = []
        if tool_schemas:
            response = await llm_client.chat_completion(
                messages=messages,
                model=skill.get("model"),
                temperature=0.2,
                tools=tool_schemas,
                tool_choice="auto"
            )
        else:
            response = await llm_client.chat_completion(
                messages=messages,
                model=skill.get("model"),
                temperature=0.2
            )

        if response.choices:
            assistant_message = response.choices[0].message.content
            tool_calls = response.choices[0].message.tool_calls or []

        results = []
        for call in tool_calls:
            tool_name = call.get("function", {}).get("name")
            if not tool_name:
                continue
            if allowed_tools and tool_name not in allowed_tools:
                results.append({
                    "tool_id": tool_name,
                    "success": False,
                    "error": "Tool not allowed by skill policy"
                })
                continue

            tool = self.get_tool(tool_name)
            if not tool:
                results.append({
                    "tool_id": tool_name,
                    "success": False,
                    "error": "Tool not registered"
                })
                continue

            args_text = call.get("function", {}).get("arguments", "{}")
            try:
                args = json.loads(args_text) if isinstance(args_text, str) else (args_text or {})
            except json.JSONDecodeError:
                args = {}

            if not tool.validate_params(args):
                results.append({
                    "tool_id": tool_name,
                    "success": False,
                    "error": "Invalid parameters"
                })
                continue

            try:
                with tool.sandbox():
                    result = await tool.execute(args)
                    results.append({
                        "tool_id": tool_name,
                        "success": True,
                        "result": result
                    })
            except Exception as e:
                self.logger.error(f"Tool execution failed: {str(e)}")
                results.append({
                    "tool_id": tool_name,
                    "success": False,
                    "error": str(e)
                })

        return {
            "skill_name": skill_name,
            "assistant_message": assistant_message,
            "tool_calls": tool_calls,
            "results": results
        }
    
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.get_tool(tool_id)
        
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        
        if not tool.validate_params(params):
            raise ValueError(f"Invalid parameters for tool: {tool_id}")
        
        try:
            with tool.sandbox():
                result = await tool.execute(params)
                return {
                    "success": True,
                    "result": result
                }
        except Exception as e:
            self.logger.error(f"Tool execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _normalize_allowed_tools(self, allowed_tools: Any) -> List[str]:
        if allowed_tools is None:
            return []
        if isinstance(allowed_tools, list):
            return [str(t).strip() for t in allowed_tools if str(t).strip()]
        if isinstance(allowed_tools, str):
            if not allowed_tools.strip():
                return []
            if "," in allowed_tools:
                return [t.strip() for t in allowed_tools.split(",") if t.strip()]
            return [allowed_tools.strip()]
        return []

    def _filter_tools_by_allowlist(self, tools: List[Dict[str, Any]], allowed: List[str]) -> List[Dict[str, Any]]:
        if not allowed or "*" in allowed:
            return tools
        return [t for t in tools if t.get("name") in allowed]

    def _to_tool_schema(self, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        parameters = tool_info.get("parameters") or {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        }
        return {
            "type": "function",
            "function": {
                "name": tool_info.get("name"),
                "description": tool_info.get("description", ""),
                "parameters": parameters
            }
        }

    def _build_messages(self, skill: Dict[str, Any], params: Dict[str, Any]) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        skill_content = (skill.get("content") or "").strip()
        if skill_content:
            messages.append({
                "role": "system",
                "content": "You are a tool-using agent. Follow the skill instructions strictly.\n" + skill_content
            })
        if isinstance(params.get("messages"), list):
            for m in params["messages"]:
                if isinstance(m, dict) and "role" in m and "content" in m:
                    messages.append({"role": m["role"], "content": m["content"]})
        else:
            user_content = (
                params.get("input")
                or params.get("query")
                or params.get("prompt")
                or json.dumps(params, ensure_ascii=False)
            )
            messages.append({"role": "user", "content": user_content})

        return messages


skill_registry = SkillRegistry()
