from typing import Dict, Any, Optional, List
import re
import importlib.util
from pathlib import Path
import threading
import time
import yaml
from agents.base import BaseAgent
from models import AgentMessage, MessageType
from tools.registry import skill_registry


class SkillAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="skill_agent",
            name="Skill Agent",
            role="Manage tools and skills"
        )
        self.skills_dir = Path("skills")
        self.skills_dir.mkdir(exist_ok=True)
        self._skill_index: Dict[str, Dict[str, Any]] = {}
        self._load_skills()
        self._start_watch_thread()
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self._load_skills()
        skill_name = task.get("skill_name")
        params = task.get("params", {})
        task_id = task.get("task_id")
        
        self.logger.info(f"Executing skill: {skill_name}")
        try:
            result = await skill_registry.execute_skill(skill_name, params)
            print("-" * 20)
            print(f"Skill Execution Result ({skill_name}):")
            print(result)
            print("-" * 20)
            return {
                "status": "completed",
                "task_id": task_id,
                "skill_name": skill_name,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Skill execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "task_id": task_id,
                "skill_name": skill_name,
                "error": str(e)
            }
    
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        if message.message_type == MessageType.TASK:
            import json
            try:
                task_data = json.loads(message.content) if isinstance(message.content, str) else message.content
                return await self.process_task(task_data)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse task data: {e}")
                return {"status": "error", "error": f"Invalid task format: {str(e)}"}
        
        return None
    
    def _load_skills(self):
        current_paths = set()
        for skill_path in self.skills_dir.glob("*/SKILL.md"):
            current_paths.add(str(skill_path))
            try:
                mtime = skill_path.stat().st_mtime
                cached = self._skill_index.get(str(skill_path))
                if not cached or cached.get("mtime", 0) < mtime:
                    skill_name = self._load_claude_skill(skill_path)
                    self._skill_index[str(skill_path)] = {"mtime": mtime, "name": skill_name}
            except Exception as e:
                self.logger.error(f"Failed to load skill {skill_path}: {str(e)}")

        removed_paths = set(self._skill_index.keys()) - current_paths
        for path in removed_paths:
            skill_name = self._skill_index.get(path, {}).get("name")
            if skill_name:
                skill_registry.unregister_skill(skill_name)
            self._skill_index.pop(path, None)
    
    def _load_claude_skill(self, skill_path: Path) -> str:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)

        if not frontmatter_match:
            raise ValueError("Invalid SKILL.md format")

        frontmatter_text = frontmatter_match.group(1)
        skill_content = frontmatter_match.group(2)

        frontmatter = yaml.safe_load(frontmatter_text) or {}

        skill_name = frontmatter.get('name', skill_path.parent.name)
        skill_description = frontmatter.get('description', '')
        allowed_tools = frontmatter.get('allowed-tools', None)
        model = frontmatter.get('model', None)

        tool_script = skill_path.parent / "tool.py"
        tools = []

        if tool_script.exists():
            tools = self._load_tool_script(tool_script)

        skill_info = {
            "name": skill_name,
            "description": skill_description,
            "allowed_tools": allowed_tools,
            "model": model,
            "content": skill_content,
            "tools": tools,
            "path": str(skill_path)
        }

        skill_registry.register_skill(skill_name, skill_info)
        self.logger.info(f"Loaded Claude skill: {skill_name}")
        return skill_name
    
    def _load_tool_script(self, tool_path: Path) -> List[Dict[str, Any]]:
        tools = []
        
        spec = importlib.util.spec_from_file_location("tool_module", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'tools'):
            for tool in module.tools:
                tools.append({
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "function": tool.get("function"),
                    "parameters": tool.get("parameters")
                })
        
        return tools
    
    async def register_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        skill_name = skill_data.get("name")
        
        skill_dir = self.skills_dir / skill_name
        skill_dir.mkdir(exist_ok=True)
        
        skill_file = skill_dir / "SKILL.md"
        
        frontmatter = f"""---
name: {skill_name}
description: {skill_data.get('description', '')}
allowed-tools: {skill_data.get('allowed_tools', '')}
model: {skill_data.get('model', '')}
---

{skill_data.get('content', '')}
"""
        
        with open(skill_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
        self._load_claude_skill(skill_file)
        return {"status": "registered", "skill_name": skill_name}
    
    async def list_skills(self) -> List[Dict[str, Any]]:
        self._load_skills()
        return skill_registry.list_skills()

    def _start_watch_thread(self):
        def _watch():
            while True:
                try:
                    self._load_skills()
                except Exception as e:
                    self.logger.warning(f"Skill watcher error: {e}")
                time.sleep(2.0)

        thread = threading.Thread(target=_watch, daemon=True)
        thread.start()
