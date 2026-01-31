from typing import Dict, Any, Optional, List
from agents.base import BaseAgent
from models import AgentMessage, MessageType
from core.llm_client import llm_client

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="coordinator_agent",
            name="Coordinator Agent",
            role="Intelligent task orchestration with ReAct-style reasoning"
        )
        self.active_tasks = {}
        self.max_iterations = 8
        self.available_agents = {
            "static_analysis_agent": "Performs static code analysis using Bandit, Flake8, and LLM",
            "skill_agent": "Executes custom skills and external tools for advanced analysis",
            "supervisor_agent": "Security intent verification and risk assessment"
        }
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id")
        self.logger.info(f"Coordinating task: {task_id}")
        
        await self.send_message(
            "supervisor_agent",
            f"Intent analysis for task: {task_id}",
            MessageType.TASK
        )
        return {
            "status": "coordinating",
            "task_id": task_id
        }
    
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        if message.message_type == MessageType.TASK:
            return await self._handle_task_message(message)
        elif message.message_type == MessageType.RESPONSE:
            return await self._handle_response_message(message)
        
        return None
    
    async def _handle_task_message(self, message: AgentMessage) -> Dict[str, Any]:
        content = message.content
        import json
        
        task_data = None
        if isinstance(content, dict):
            task_data = content
        elif isinstance(content, str):
            try:
                task_data = json.loads(content)
            except json.JSONDecodeError:
                if "New task received" in content:
                    task_id = content.split(":")[-1].strip()
                    self.active_tasks[task_id] = {
                        "status": "pending",
                        "steps": []
                    }
                    return {"status": "task_received", "task_id": task_id}
                return {"status": "unknown_message_format"}
        
        if task_data:
            task_id = task_data.get("task_id", "unknown")
            self.active_tasks[task_id] = {
                "status": "pending",
                "steps": [],
                "task_data": task_data
            }
            self.logger.info(f"Task received: {task_id}")
            return await self.process_task(task_data)
        return {"status": "error", "message": "Invalid task content"}
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id")
        self.logger.info(f"[ReAct] Coordinating task: {task_id}")
        
        from api.websocket import manager
        await manager.send_task_update(task_id, "running", 10.0, "Coordinator: Initializing ReAct workflow...")

        if task_id not in self.active_tasks:
            self.active_tasks[task_id] = {
                "status": "pending",
                "task_data": task,
                "iteration": 0,
                "executed_actions": [],
                "observations": [],
                "findings": [],
                "supervisor_passed": False
            }
            
        import json
        await self.send_message(
            "supervisor_agent",
            json.dumps(task),
            MessageType.TASK
        )
        return {
            "status": "coordinating",
            "task_id": task_id
        }

    async def _handle_response_message(self, message: AgentMessage) -> Dict[str, Any]:
        sender = message.sender_id
        content = message.content
        import json
        from database import get_db, AuditResult, Task
        from datetime import datetime
        from api.websocket import manager
        
        data = {}
        try:
            data = json.loads(content) if isinstance(content, str) else content
        except:
            data = {"raw_content": content}
        task_id = data.get("task_id")
        
        if sender == "supervisor_agent":
            is_safe = data.get("safe", False)
            if is_safe and task_id:
                task_state = self.active_tasks.get(task_id, {})
                if "observations" not in task_state:
                    task_state["observations"] = []
                if "executed_actions" not in task_state:
                    task_state["executed_actions"] = []
                if "findings" not in task_state:
                    task_state["findings"] = []
                if "iteration" not in task_state:
                    task_state["iteration"] = 0
                    
                task_state["supervisor_passed"] = True
                task_state["observations"].append({
                    "step": "supervisor_check",
                    "result": "safe",
                    "risk_level": data.get("risk_level", "low")
                })
                self.logger.info(f"[ReAct] Task {task_id} passed supervisor check. Entering decision loop...")
                await manager.send_task_update(task_id, "running", 20.0, "Coordinator: Security Verified. Analyzing next action...")

                await self._react_loop(task_id, task_state)
            else:
                self.logger.warning(f"[ReAct] Task blocked by supervisor: {data}")
                if task_id:
                    await manager.send_task_update(task_id, "failed", 100.0, f"Security Risk: {data.get('reason', 'Rejected')}")
                    await manager.broadcast({
                        "type": "log_update",
                        "task_id": task_id,
                        "message": f"Task Blocked: {data.get('reason', 'Security supervisor rejected request')}"
                    })
                    
                    db = next(get_db())
                    try:
                        task = db.query(Task).filter(Task.task_id == task_id).first()
                        if task:
                            task.status = "failed"
                            task.error_message = data.get("reason", "Blocked by security supervisor")
                            task.completed_at = datetime.now()
                            db.commit()
                    except Exception as e:
                        self.logger.error(f"Failed to update task status: {e}")
                    finally:
                        db.close()
        
        elif sender == "static_analysis_agent":
             self.logger.info(f"[ReAct] Received static analysis results for {task_id}")
             results = data.get("results", [])
             
             task_state = self.active_tasks.get(task_id)
             if not task_state:
                 self.logger.error(f"[ReAct] Task state not found for {task_id}")
                 return None
             task_state["observations"].append({
                 "step": "static_analysis",
                 "agent": "static_analysis_agent",
                 "results_count": len(results),
                 "findings": results
             })
             task_state["findings"].extend(results)
             task_state["executed_actions"].append("static_analysis")

             await self._react_loop(task_id, task_state)
        
        elif sender == "skill_agent":
             self.logger.info(f"[ReAct] Received skill execution results for {task_id}")
             skill_result = data.get("result", {})
             skill_name = data.get("skill_name", "unknown")
             status = data.get("status")
             error = data.get("error")
             
             task_state = self.active_tasks.get(task_id)
             if not task_state:
                 self.logger.error(f"[ReAct] Task state not found for {task_id}")
                 return None
             if "observations" not in task_state:
                 task_state["observations"] = []
             if "executed_actions" not in task_state:
                 task_state["executed_actions"] = []
             if "findings" not in task_state:
                 task_state["findings"] = []
             if status == "error" or data.get("success") is False:
                 task_state["observations"].append({
                     "step": "skill_execution",
                     "agent": "skill_agent",
                     "skill_name": skill_name,
                     "status": "error",
                     "error": error or data
                 })
                 task_state["executed_actions"].append(f"skill:{skill_name}:failed")
                 await self._mark_task_failed(task_id, f"Skill execution failed: {error or skill_name}")
                 return None
             task_state["observations"].append({
                 "step": "skill_execution",
                 "agent": "skill_agent",
                 "skill_name": skill_name,
                 "result": skill_result
             })
             task_state["executed_actions"].append(f"skill:{skill_name}")
             if isinstance(skill_result, dict) and "findings" in skill_result:
                 task_state["findings"].extend(skill_result["findings"])
             # 继续 ReAct 循环决策
             await self._react_loop(task_id, task_state)
        
        return None

    def _parse_task_parameters(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        import json
        params = task_data.get("parameters")
        if not params:
            return {}
        if isinstance(params, dict):
            return params
        if isinstance(params, str):
            try:
                return json.loads(params)
            except json.JSONDecodeError:
                return {"raw": params}
        return {}

    def _get_available_skill_names(self) -> List[str]:
        from tools.registry import skill_registry
        skills = skill_registry.list_skills()
        return [s.get("name") for s in skills if s.get("name")]

    def _get_requested_skill_name(self, task_state: Dict[str, Any]) -> Optional[str]:
        task_data = task_state.get("task_data", {})
        params = self._parse_task_parameters(task_data)
        for key in ["skill_name", "skill", "skillName"]:
            val = params.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        for key in ["skill_name", "skill"]:
            val = task_data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return None

    def _resolve_skill_name(self, task_state: Dict[str, Any], decision: Dict[str, Any]) -> Optional[str]:
        available = self._get_available_skill_names()
        decision_name = decision.get("skill_name") if isinstance(decision, dict) else None
        if isinstance(decision_name, str) and decision_name.strip() and decision_name in available:
            return decision_name
        requested = self._get_requested_skill_name(task_state)
        if requested and requested in available:
            return requested
        return available[0] if available else None

    async def _mark_task_failed(self, task_id: str, reason: str):
        from database import get_db, Task
        from datetime import datetime
        from api.websocket import manager

        await manager.send_task_update(task_id, "failed", 100.0, f"Coordinator: {reason}")
        await manager.broadcast({
            "type": "log_update",
            "task_id": task_id,
            "message": f"Task Failed: {reason}"
        })
        
        db = next(get_db())
        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = reason
                task.completed_at = datetime.now()
                db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update task status: {e}")
            db.rollback()
        finally:
            db.close()

        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
    
    async def _react_loop(self, task_id: str, task_state: Dict[str, Any]):
        from api.websocket import manager
        import json
        
        task_state["iteration"] += 1
        iteration = task_state["iteration"]
        self.logger.info(f"[ReAct] Task {task_id} - Iteration {iteration}/{self.max_iterations}")
        if iteration > self.max_iterations:
            self.logger.warning(f"[ReAct] Task {task_id} reached max iterations. Finalizing...")
            await self._finalize_task(task_id, task_state)
            return
        # Reasoning: 使用 LLM 决策下一步行动
        progress = 20.0 + (iteration * 10)
        await manager.send_task_update(task_id, "running", progress, f"Coordinator: Thinking... (Round {iteration})")
        decision = await self._make_decision(task_state)
        
        self.logger.info(f"[ReAct] Decision for {task_id}: {decision['action']}")
        # Action: 根据决策执行行动
        if decision["action"] == "static_analysis":
            if "static_analysis" in task_state["executed_actions"]:
                self.logger.warning(f"[ReAct] Skipping duplicate static_analysis for {task_id}")
                await self._finalize_task(task_id, task_state)
                return
            await self.send_message(
                "static_analysis_agent",
                json.dumps(task_state["task_data"]),
                MessageType.TASK
            )
        
        elif decision["action"] == "skill_execution":
            skill_name = self._resolve_skill_name(task_state, decision)
            if not skill_name:
                self.logger.error(f"[ReAct] No available skill to execute for {task_id}")
                await self._mark_task_failed(task_id, "No available skill to execute")
                return
            skill_key = f"skill:{skill_name}"
            if skill_key in task_state["executed_actions"]:
                self.logger.warning(f"[ReAct] Skipping duplicate {skill_key} for {task_id}")
                await self._finalize_task(task_id, task_state)
                return
            
            await self.send_message(
                "skill_agent",
                json.dumps({
                    "task_id": task_id,
                    "skill_name": skill_name,
                    "params": {
                        "code": task_state["task_data"].get("code_content", ""),
                        "previous_findings": task_state.get("findings", [])
                    }
                }),
                MessageType.TASK
            )
        
        elif decision["action"] == "finalize":
            self.logger.info(f"[ReAct] Task {task_id} - LLM decided to finalize")
            await self._finalize_task(task_id, task_state)
        
        else:
            self.logger.error(f"[ReAct] Unknown action: {decision['action']}")
            await self._finalize_task(task_id, task_state)
    
    async def _make_decision(self, task_state: Dict[str, Any]) -> Dict[str, str]:
        import json
        from tools.registry import skill_registry
        executed_actions = task_state.get("executed_actions", [])
        observations = task_state.get("observations", [])
        findings = task_state.get("findings", [])
        iteration = task_state.get("iteration", 0)
        available_skills = [s.get("name") for s in skill_registry.list_skills() if s.get("name")]
        available_skills_text = ", ".join(available_skills) if available_skills else "None"
        
        task_data = task_state.get("task_data", {})
        task_title = task_data.get("title", "N/A")
        task_desc = task_data.get("description", "N/A")
        task_priority = task_data.get("priority", "N/A")

        context = f"""You are an intelligent code audit coordinator using ReAct (Reasoning + Acting) approach.

Task: Audit the code for security vulnerabilities and code quality issues.
Task Info:
- Title: {task_title}
- Description: {task_desc}
- Priority: {task_priority}

Current State:
- Iteration: {iteration}/{self.max_iterations}
- Executed Actions: {', '.join(executed_actions) if executed_actions else 'None yet'}
- Findings So Far: {len(findings)} issues found

Observation History:
{json.dumps(observations, indent=2, ensure_ascii=False)}

Available Actions:
1. "static_analysis" - Run Bandit, Flake8, and LLM-based code analysis (comprehensive, always run first)
2. "skill_execution" - Execute skills ONLY if:
   - User explicitly requested it (e.g., "调用skill", "use skill")
   - Code is complex or static analysis is insufficient
   - Previous findings need deeper investigation
3. "finalize" - Complete the audit and save results

Available Skills:
- {available_skills_text}

CRITICAL Decision Rules:
- ALWAYS start with "static_analysis" if not done yet
- ONLY choose "skill_execution" if there's a compelling reason (see above)
- If static analysis completed and no strong reason for skill → choose "finalize"
- DONOT repeat the same action
- Prioritize efficiency: finalize when analysis is sufficient

Respond with ONLY a JSON object:
{{"action": "static_analysis|skill_execution|finalize", "reason": "brief explanation", "skill_name": "(if skill_execution, choose from available skills)"}}"""
        
        try:
            response = await llm_client.chat_completion(
                messages=[{
                    "role": "system",
                    "content": "You are a decision-making assistant for code audit coordination. Always respond with valid JSON only."
                }, {
                    "role": "user",
                    "content": context
                }],
                temperature=0.3
            )
            
            if response.choices:
                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                decision = json.loads(content)
                self.logger.info(f"[ReAct] LLM Decision: {decision['action']} - {decision.get('reason', '')}")
                return decision
        except Exception as e:
            self.logger.error(f"[ReAct] Decision making failed: {e}")

        if "static_analysis" not in executed_actions:
            return {"action": "static_analysis", "reason": "No static analysis performed yet"}
        elif iteration >= self.max_iterations:
            return {"action": "finalize", "reason": "Max iterations reached"}
        elif len(findings) > 0 and available_skills:
            preferred = available_skills[0]
            if f"skill:{preferred}" not in executed_actions:
                return {"action": "skill_execution", "skill_name": preferred, "reason": "Deep analysis needed"}
            return {"action": "finalize", "reason": "Skill already executed"}
        else:
            return {"action": "finalize", "reason": "Sufficient analysis completed"}
    
    async def _finalize_task(self, task_id: str, task_state: Dict[str, Any]):
        from database import get_db, AuditResult, Task
        from datetime import datetime
        from api.websocket import manager
        import uuid
        
        self.logger.info(f"[ReAct] Finalizing task {task_id}")
        await manager.send_task_update(task_id, "processing_results", 85.0, "Coordinator: Consolidating findings...")
        
        findings = task_state.get("findings", [])
        
        db = next(get_db())
        try:
            if findings:
                for finding in findings:
                    db_result = AuditResult(
                        result_id=str(uuid.uuid4()),
                        task_id=task_id,
                        severity=str(finding.get("severity", "info")).lower(),
                        category=str(finding.get("category", "security")).lower(),
                        description=finding.get("description", ""),
                        file_path=finding.get("file_path", ""),
                        line_number=finding.get("line_number"),
                        code_snippet=finding.get("code_snippet", "")
                    )
                    db.add(db_result)

            summary = None
            try:
                import json
                task_data = task_state.get("task_data", {})
                observations = task_state.get("observations", [])
                summary_prompt = f"""
Analyze the following audit findings and provide a summary.

Task Context:
- Title: {task_data.get('title', 'N/A')}
- Description: {task_data.get('description', 'N/A')}
- Priority: {task_data.get('priority', 'N/A')}

Agent Observations (raw, include all agents):
{json.dumps(observations, indent=2, ensure_ascii=False)}
Findings Count: {len(findings)}
Findings Data:
{json.dumps([
    {k: v for k, v in f.items() if k in ['severity', 'category', 'description', 'file_path', 'line_number', 'code_snippet']}
    for f in findings
], indent=2, ensure_ascii=False)}

Please provide a Chinese summary, including:
1. Overall security assessment
2. Key issues identified
3. Concrete remediation recommendations
Keep it under 250 words.
"""
                response = await llm_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a senior security auditor."},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.4
                )
                if response.choices:
                    summary = response.choices[0].message.content.strip()
            except Exception as e:
                self.logger.error(f"[ReAct] Failed to generate summary: {e}")

            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                task.status = "completed"
                task.completed_at = datetime.now()
                if summary:
                    task.result_summary = summary
            
            db.commit()
            self.logger.info(f"[ReAct] Saved {len(findings)} findings for task {task_id}")

            if summary:
                 await manager.broadcast({
                    "type": "task_summary",
                    "task_id": task_id,
                    "summary": summary
                })
            
            iteration = task_state.get("iteration", 0)
            msg = f"Coordinator: Audit Complete ({iteration} rounds). {len(findings)} issues found." if findings else f"Coordinator: Audit Complete ({iteration} rounds). No issues found."
            await manager.send_task_update(task_id, "completed", 100.0, msg)

            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
        except Exception as e:
            self.logger.error(f"[ReAct] Failed to finalize task {task_id}: {e}")
            db.rollback()
        finally:
            db.close()
