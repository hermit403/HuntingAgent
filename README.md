# HuntingAgent

HuntingAgent 是一个基于多Agent协同的轻量级代码审计系统。
<p align="left">
  <img src="https://skillicons.dev/icons?i=python,fastapi,vue,vite,ts,nodejs,docker" />
</p>

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少256MB可用内存
- 至少1GB可用磁盘空间

## 功能特性

- 多Agent协同
  - 用户交互Agent（UserAgent）：与前端交互，处理用户请求
  - 协调Agent（CoordinatorAgent）：管理任务分发和Agent协调
  - 审计Agent（StaticAnalysisAgent）：执行静态代码分析
  - Skill Agent（SkillAgent）：管理工具/Skills，参考Claude Skills
  - 监管Agent（SupervisorAgent）：审计用户操作和意图

- Skills支持
  - 支持SKILL.md格式
  - 支持渐进式加载
  - 支持工具脚本

- 代码审计功能
  - 静态分析：漏洞扫描、代码规范检查
  - 工具集成：Bandit、Flake8
  - LLM智能分析：使用OpenAI兼容API

## 快速开始

1. 克隆仓库
```bash
git clone <repository-url>
cd HuntingAgent
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env并填入你的API密钥，默认使用的是百炼服务
```

3. 本地构建前端
```bash
cd frontend
npm install
npm run build
cd ..
```

4. 启动服务
```bash
# docker-compose
docker-compose up -d --build
# docker
# docker build -t huntingagent:latest .
# docker run -d --name huntingagent -p 8000:8000 huntingagent:latest
```

5. 访问应用
- 前端：http://localhost:8000

## Skills格式

系统支持Claude Skills的SKILL.md格式：

```markdown
---
name: skill-name
description: What this skill does and when to use it
allowed-tools: Read, Grep, Bash(npm:*)
model: gemini-3-flash
---

# Skill Title
## When to Use
- Condition 1
- Condition 2
## Instructions
Detailed instructions...
```

### 创建自定义Skill

1. 在`skills/`目录下创建新文件夹
2. 创建`SKILL.md`文件
3. 可选：创建`tool.py`文件实现工具函数

## 开发

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 部署

### Docker部署
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 查看日志
```bash
docker-compose logs -f
```

## 配置说明

环境变量配置（.env文件）：

- `OPENAI_API_KEY`：API密钥
- `OPENAI_BASE_URL`：API基础URL
- `OPENAI_MODEL`：使用的模型名
- `JWT_SECRET_KEY`：JWT密钥
- `DATABASE_URL`：数据库URL（默认：sqlite:///./huntingagent.db）
- `TOOL_TIMEOUT`：工具超时时间（默认：30秒）
- `TOOL_MAX_MEMORY`：工具最大内存（默认：256M）

## 故障排除

1. Docker容器无法启动
   - 检查端口8000是否被占用
   - 查看Docker日志：`docker-compose logs`

2. 前端无法连接后端
   - 检查.env文件配置是否正确
   - 确认API密钥是否可用

3. Agent无法启动
   - 验证数据库是否存在以及连接情况
   - 查看Docker日志：`docker-compose logs`
