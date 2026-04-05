# Ecology Harness

[English](README.md) | [简体中文](README.zh-CN.md)

Ecology Harness 是一个面向生态数据分析与推理工作流的 Python Agent Harness 基座。

当前版本优先把通用 Harness 内核搭完整，先提供稳定的运行时、工具、技能、记忆、会话、多智能体与插件机制，后续再在此基础上持续叠加生态领域能力。

## 启动界面

![Ecology Harness 启动截图](imgs/start_img.png)

## 项目包含的能力

- 模块化包结构，便于后续持续扩展
- CLI + REPL 双入口，支持自然语言与 slash command 混合使用
- 事件驱动的终端交互界面
- Agent loop 与工具调用闭环
- 对齐 `nano-claude-code` 的 provider 抽象层
- 内置支持 `mock`、`anthropic`、`openai`、`gemini`、`kimi`、`qwen`、`zhipu`、`deepseek`、`ollama`、`lmstudio`、`custom`
- 会话持久化、恢复与上下文压缩
- 可配置 Sandbox、权限策略与审计
- 工具注册系统与内置通用工具
- 双 scope 记忆系统与自动 `MEMORY.md`
- 多智能体与子智能体协同机制
- Markdown skill 系统
- MCP 与 plugin 扩展骨架
- 标准库 `unittest` 测试集

## 快速开始

### 一键安装

```bash
bash scripts/install.sh
```

带开发依赖：

```bash
bash scripts/install.sh --with-dev
```

如果你更习惯 `uv`：

```bash
bash scripts/install.sh --uv
```

### 从源码安装

```bash
git clone <your-repo-url>
cd EcologyHarness

python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .

# 可选：安装开发依赖
python3 -m pip install -e '.[dev]'
```

也可以使用 `uv`：

```bash
uv sync
uv run eh --help
```

安装完成后，推荐直接使用：

```bash
eh --help
```

`eh` 是推荐入口；`ecology-harness` 与 `python3 -m ecology_harness` 仍然可用。

如果暂时不想安装，也可以直接源码运行：

```bash
PYTHONPATH=src python3 -m ecology_harness --help
```

## 运行示例

```bash
# 查看状态
eh status

# 查看内置工具
eh tools

# 查看插件与 MCP
eh plugins
eh mcp

# 查看支持的模型来源
eh providers

# 直接进入 REPL
eh repl

# 单轮 prompt
eh "summarize this repository in 5 bullets"

# 显式 prompt 命令
eh prompt '/tool Read {"path":"README.md"}'

# 恢复最近一次会话
eh --resume latest repl
```

默认情况下，`--prompt` 和 `--repl` 会显示中间 trace，包括步骤、工具调用和结果摘要。可以用 `--quiet` 关闭，也可以用 `--json` 获取结构化输出。

REPL 是有状态的，新的输入会继续沿用当前会话，直到你执行 `/reset` 或 `/new`。

## REPL 常用命令

```text
/help
/status
/config
/permissions
/model sonnet
/session
/plugins
/mcp
/tool Read {"path":"README.md"}
/tool TaskCreate {"title":"Inspect project"}
/trace off
/new
```

常用命令列表：

- `/help`
- `/status`
- `/config`
- `/permissions`
- `/model`
- `/session`
- `/cost`
- `/tools`
- `/skills`
- `/plugins`
- `/mcp`
- `/memories`
- `/tasks`
- `/providers`
- `/sandbox`
- `/trace on`
- `/trace off`
- `/new`
- `/reset`
- `/clear`
- `/quit`

## 记忆、会话与压缩

当前运行时已经具备比较完整的长任务支撑能力：

- 项目记忆和用户记忆会按当前 prompt 做相关性排序后再注入
- 会话会以结构化快照形式持久化，包含 `session_id`、时间戳、消息历史与压缩元信息
- 上下文过长时会自动生成 continuation summary，而不是简单截断
- 压缩摘要会尽量保留最近请求、工具使用、待办、关键文件与时间线

这部分实现参考了 `claw-code` 的 session 与 compaction 思路，并结合本项目的轻量 Python 架构做了适配。

## 多智能体与协同

子智能体层已经不只是简单并发调用，而是有明确的协作结构：

- 内置 agent type 包括 `planner`、`coordinator`、`coder`、`reviewer`、`researcher`、`tester`
- 委派时会附带 ownership、预期产出、依赖关系与上游上下文摘要
- 后台子智能体会跟踪 handoff、dependency 与 coordination notes
- 内部 agent 协调任务与用户任务分开持久化，避免污染主任务编号

查看内置 agent 类型：

```bash
eh prompt '/tool ListAgentTypes {}'
```

## 模型来源

当前支持的模型来源与 `nano-claude-code` 保持同一大类：

- `anthropic`
- `openai`
- `gemini`
- `kimi`
- `qwen`
- `zhipu`
- `deepseek`
- `ollama`
- `lmstudio`
- `custom`
- `mock`

可以直接查看：

```bash
eh providers
```

示例：

```bash
export ANTHROPIC_API_KEY=your_key
eh --provider anthropic --model claude-sonnet-4-6 prompt "Summarize this repository."
```

```bash
export OPENAI_API_KEY=your_key
eh --provider openai --model gpt-4o-mini --base-url https://api.openai.com/v1 prompt "Inspect the workspace."
```

```bash
eh --provider ollama --model ollama/qwen2.5-coder prompt "Inspect the workspace."
```

## 内置工具

### 文件与搜索

- `Read`
- `Write`
- `Edit`
- `Glob`
- `Grep`

### Runtime 与 Web

- `Bash`
- `WebFetch`
- `WebSearch`
- `GetDiagnostics`
- `NotebookEdit`
- `SandboxStatus`
- `Agent`
- `SendMessage`
- `CheckAgentResult`
- `ListAgentTasks`
- `ListAgentTypes`
- `PluginList`
- `PluginRead`
- `ListMcpServersTool`
- `ListMcpToolsTool`
- `MCPTool`
- `ListMcpResourcesTool`
- `ReadMcpResourceTool`
- `McpAuthTool`

### 记忆与技能

- `MemorySave`
- `MemoryList`
- `MemoryRead`
- `MemoryDelete`
- `MemorySearch`
- `Skill`
- `SkillList`
- `SkillRead`

### 任务

- `TaskCreate`
- `TaskList`
- `TaskGet`
- `TaskUpdate`

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests/unit -v
```

如果已经安装了开发依赖，也可以直接运行：

```bash
python3 -m unittest discover -s tests/unit -v
```

## 项目结构

```text
src/ecology_harness/
  app.py                 # 依赖装配
  cli.py                 # CLI + REPL
  runtime/               # agent loop, providers, prompt 组装
  tools/                 # 工具协议、注册与内置工具
  memory/                # 持久记忆
  skills/                # Markdown skill 系统
  tasks/                 # 任务持久化
  permissions/           # 权限与执行策略
  agents/                # 子智能体管理
```

## 下一步方向

下一层会逐步补充生态领域能力：

- 面向数据集、表格分析、遥感、GIS 的生态工具
- 生态领域 memory schema 与 skill pack
- 面向生态推理任务的 benchmark 与 evaluation harness
