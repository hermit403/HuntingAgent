from typing import Dict, Any, Optional
import re
import json
from agents.base import BaseAgent
from models import AgentMessage, MessageType
from core.llm_client import llm_client


class SupervisorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="supervisor_agent",
            name="Supervisor Agent",
            role="Audit user operations and intent for security"
        )
        self.blocked_patterns = [
            r'rm\s+-rf\s+/',
            r'drop\s+database',
            r'delete\s+from\s+\w+\s+where\s+1=1',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'os\.system',
            r'subprocess\.call',
            r'pickle\.loads',
            r'marshal\.loads',
            r'child_process',
            r'execSync',
            r'spawn',
            r'process\.mainModule'
        ]
        self.suspicious_keywords = [
            'password', 'secret', 'token', 'debug',
            'exp', 'payload', 'shellcode', 'inject',
            'xss', 'csrf', 'rce', 'flag', 'CTF'
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id")
        task_content = task.get("description", "")
        code_content = task.get("code_content", "")

        self.logger.info(f"Auditing task for security: {task_id}")
        
        intent_analysis = await self._analyze_intent(task_content, code_content[:600])
        code_analysis = await self._analyze_code(code_content)
        risk_level = self._calculate_risk_level(intent_analysis, code_analysis)
        
        result = {
            "task_id": task_id,
            "risk_level": risk_level,
        }
        
        if risk_level in ["critical", "high"]:
            self.logger.warning(f"Task blocked due to {risk_level} risk")
            result.update({
                "status": "blocked",
                "reason": f"Security risk detected: {risk_level}",
                "safe": False
            })
        else:
            result.update({
                "status": "approved",
                "safe": True
            })
            
        return result
    
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        if message.message_type == MessageType.TASK:
            import json
            content = message.content
            task_data = {}
            if isinstance(content, str):
                try:
                    task_data = json.loads(content)
                except:
                    task_data = {"description": content}
            elif isinstance(content, dict):
                task_data = content
                
            return await self.process_task(task_data)
        
        return None
    
    async def _analyze_intent(self, content: str, code_snippet: str = "") -> Dict[str, Any]:
        analysis = {
            "malicious": False,
            "suspicious": False,
            "risk_score": 0,
            "detected_patterns": []
        }
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                analysis["malicious"] = True
                analysis["detected_patterns"].append(pattern)
                analysis["risk_score"] += 50
        
        for keyword in self.suspicious_keywords:
            if keyword.lower() in content.lower():
                analysis["suspicious"] = True
                analysis["risk_score"] += 10

        try:
            user_msg = f"Analyze: {content}"
            if code_snippet:
                user_msg += f"\nCode snippet: {code_snippet}"
            messages = [
                {
                    "role": "system",
                    "content": "You are a security analyst. Analyze the user's intent and code snippet, determine if it's malicious or safe. Return JSON with 'malicious' (boolean), 'risk_score' (5-100), and 'reason' (string)."
                },
                {
                    "role": "user",
                    "content": user_msg
                }
            ]
            response = await llm_client.chat_completion(
                messages=messages,
                temperature=0.5
            )
            if response.choices:
                llm_result = json.loads(response.choices[0].message.content)
                current_score = analysis["risk_score"]
                analysis.update(llm_result)
                analysis["risk_score"] = max(current_score, llm_result.get("risk_score", 0))
        except Exception as e:
            self.logger.error(f"LLM intent analysis failed: {str(e)}")
        
        return analysis
    
    async def _analyze_code(self, code: str) -> Dict[str, Any]:
        analysis = {
            "has_dangerous_functions": False,
            "has_hardcoded_secrets": False,
            "risk_score": 0,
            "issues": []
        }
        dangerous_functions = [
            'eval', 'exec', 'compile', 'open',
            'pickle.loads', 'marshal.loads',
            'subprocess.call', 'os.system', 'execSync',
            'child_process', 'process.mainModule',
            'mainModule.require', 'spawn'
        ]
        for func in dangerous_functions:
            if func in code:
                analysis["has_dangerous_functions"] = True
                analysis["risk_score"] += 25
                analysis["issues"].append(f"Dangerous function: {func}")
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        for pattern in secret_patterns:
            if re.search(pattern, code):
                analysis["has_hardcoded_secrets"] = True
                analysis["risk_score"] += 10
                analysis["issues"].append("Hardcoded secret detected")
        
        return analysis
    
    def _calculate_risk_level(
        self,
        intent: Dict[str, Any],
        code: Dict[str, Any]
    ) -> str:
        total_score = (
            intent.get("risk_score", 0) + code.get("risk_score", 0)
        )
        self.logger.info(f"Total risk score: {total_score}")
        if total_score >= 80:
            return "critical"
        elif total_score >= 60:
            return "high"
        elif total_score >= 40:
            return "medium"
        elif total_score >= 20:
            return "low"
        else:
            return "info"
