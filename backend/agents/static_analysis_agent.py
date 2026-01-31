from typing import Dict, Any
import subprocess
import json
import tempfile
import os
from agents.base import BaseAgent
from models import AgentMessage, MessageType
from core.llm_client import llm_client


class StaticAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="static_analysis_agent",
            name="Static Analysis Agent",
            role="Perform code security audit and static analysis"
        )
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id")
        code_content = task.get("code_content")
        
        from api.websocket import manager
        
        self.logger.info(f"Starting static analysis for task: {task_id}")
        await manager.send_task_update(task_id, "running", 35.0, "StaticAnalysis: Starting tool execution...")
        
        results = []
        
        if code_content:
            await manager.send_task_update(task_id, "running", 36.0, "StaticAnalysis: Running 'bandit' security scanner...")
            bandit_results = await self._run_bandit(code_content)
            results.extend(bandit_results)
            await manager.send_task_update(task_id, "running", 37.0, "StaticAnalysis: Running 'flake8' linter...")
            flake8_results = await self._run_flake8(code_content)
            results.extend(flake8_results)
            await manager.send_task_update(task_id, "running", 38.0, "StaticAnalysis: Performing LLM-based deep code audit...")
            llm_analysis = await self._llm_code_analysis(code_content, task)
            results.extend(llm_analysis)
        return {
            "status": "completed",
            "task_id": task_id,
            "results": results
        }
    
    async def handle_message(self, message: AgentMessage):
        if message.message_type == MessageType.TASK:
            import json
            content = message.content
            task_data = {}
            if isinstance(content, str):
                try:
                    task_data = json.loads(content)
                except:
                    task_data = {"task_id": "unknown", "code_content": content}
            elif isinstance(content, dict):
                task_data = content
            return await self.process_task(task_data)
        return None
    
    async def _run_bandit(self, code: str) -> list:
        results = []
        import asyncio
        import functools
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            loop = asyncio.get_running_loop()
            run_cmd = functools.partial(
                subprocess.run,
                ['bandit', '-f', 'json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            result = await loop.run_in_executor(None, run_cmd)
            
            os.unlink(temp_file)
            
            if result.stdout:
                bandit_output = json.loads(result.stdout)
                for issue in bandit_output.get('results', []):
                    results.append({
                        "severity": self._map_bandit_severity(issue.get('issue_severity')),
                        "category": "security",
                        "description": issue.get('issue_text'),
                        "file_path": issue.get('filename'),
                        "line_number": issue.get('line_number'),
                        "code_snippet": issue.get('code', '')[:200]
                    })
        except Exception as e:
            self.logger.error(f"Bandit analysis failed: {str(e)}")
        
        return results
    
    async def _run_flake8(self, code: str) -> list:
        results = []
        import asyncio
        import functools
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            loop = asyncio.get_running_loop()
            run_cmd = functools.partial(
                subprocess.run,
                ['flake8', '--format=json', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            result = await loop.run_in_executor(None, run_cmd)
            
            os.unlink(temp_file)
            
            if result.stdout:
                try:
                    flake8_output = json.loads(result.stdout)
                    for filename, issues in flake8_output.items():
                        for issue in issues:
                            results.append({
                                "severity": "low",
                                "category": "style",
                                "description": f"{issue.get('code')}: {issue.get('text')}",
                                "file_path": issue.get('filename'),
                                "line_number": issue.get('line_number'),
                                "code_snippet": ''
                            })
                except json.JSONDecodeError:
                    self.logger.warning(f"Flake8 produced invalid JSON: {result.stdout}")
            if result.stderr:
                 self.logger.warning(f"Flake8 stderr: {result.stderr}")   
        except Exception as e:
            self.logger.error(f"Flake8 analysis failed: {str(e)}")
        
        return results
    
    async def _llm_code_analysis(self, code: str, task_data: Dict[str, Any] = {}) -> list:
        results = []
        
        title = task_data.get("title", "N/A")
        description = task_data.get("description", "N/A")
        priority = task_data.get("priority", "N/A")

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a code security expert. Analyze the provided code for security vulnerabilities, bugs, and code quality issues. Return ONLY a JSON array with objects containing severity, category, description, and line_number fields. Do not include markdown formatting."
                },
                {
                    "role": "user",
                    "content": f"""Analyze this code.
Task Context:
- Title: {title}
- Description: {description}
- Priority: {priority}

Code:
{code}"""
                }
            ]
            
            response = await llm_client.chat_completion(
                messages=messages,
                temperature=0.5
            )
            
            if response.choices:
                content = response.choices[0].message.content
                self.logger.info(f"LLM Response content: {content}")
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    analysis = json.loads(content)
                    if isinstance(analysis, list):
                        results.extend(analysis)
                    elif isinstance(analysis, dict) and "issues" in analysis:
                         results.extend(analysis["issues"])
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse LLM response: {e}. Content: {content}")
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {str(e)}")
        
        return results
    
    def _map_bandit_severity(self, severity: str) -> str:
        mapping = {
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low"
        }
        return mapping.get(severity, "info")
