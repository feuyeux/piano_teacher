# Piano Teacher Agent

[English README](README.md)

Piano Teacher Agent 是一个本地钢琴练习助手，把谱面导入、MusicXML 标准化、MIDI 与琴谱对齐分析、Hermes Skill 和长期练习记忆串成一个可持续使用的练习系统。

目标体验是自然语言对话：你告诉 Hermes 准备曲目、开始练习、结束练习、查看反馈、记录学习成果、安排下一步练习。底层 Python workflow 负责确定性的谱面解析、MIDI 对齐、评分、落盘和 profile 更新；Hermes 子 agent 负责更高层的谱面导入 review 和教学反馈表达。

## 核心能力

- 从 PDF 或已有 MusicXML/MXL 导入并复核钢琴谱。
- 将 MusicXML 标准化为内部使用的 `normalized_score.json`。
- 创建练习会话，并把 MIDI 事件日志与标准化谱面对齐分析。
- 生成结构化练习反馈：分数、问题小节、问题标签、练习步骤、下一步重点。
- 在 `profiles/` 中维护每首曲子的长期学习画像。
- 提供脚本式 Hermes Skill，让主 agent 通过脚本协调 workflow，不依赖 MCP。
- 保留 MCP server 作为旧 Hermes dashboard/tool 流程的兼容入口。

## 架构概览

```text
Hermes / 用户请求
  -> piano-teacher-conductor skill
  -> scripts/hermes_piano_teacher
  -> app.agents.ConductorAgent
  -> workflow 层
  -> 确定性 services/tools
  -> 练习反馈子 agent 或谱面导入复核子 agent
  -> sessions/, profiles/, scores/
```

主要目录：

- `app/agents/`：主控 agent、钢琴教师反馈 agent、谱面导入复核 agent。
- `app/workflows/`：开始练习、结束练习、mock 听练习、标准化谱面、刷新曲库。
- `app/services/`：评分、对齐、MIDI 解析、profile 更新、曲库逻辑。
- `app/tools/`：Audiveris 封装、MusicXML reader、MIDI parser、score aligner。
- `skills/`：项目内 Hermes/Codex Skill。
- `scripts/`：Skill 入口、Hermes 子 agent helper、MCP 兼容入口。
- `scores/`：曲库、导入的 MusicXML/MXL、标准化谱面、review 报告。
- `sessions/`：练习会话、分析结果、反馈、mock MIDI log。
- `profiles/`：每首曲子的长期练习记忆。

## 快速开始

进入项目根目录：

```bash
cd /Users/zonghe/Downloads/piano_teacher
```

准备曲目：

```bash
scripts/hermes_piano_teacher "准备 minimal-piano-fixture"
```

运行一次 mock 练习并生成反馈：

```bash
scripts/hermes_piano_teacher "mock 听我练习 minimal-piano-fixture 前24个音 rough 模式"
```

查看学习进度和下一步计划：

```bash
scripts/hermes_piano_teacher "查看 minimal-piano-fixture 的学习进度和计划"
```

复核 PDF 谱面导入：

```bash
scripts/hermes_piano_teacher "复核琴谱 PDF /Users/zonghe/Downloads/piano_teacher/Por_una_cabeza_Feisi.pdf"
```

## 直接命令行

不通过 Hermes，也可以直接跑同样的 workflow：

```bash
python3 -m app.main refresh-library
python3 -m app.main normalize-score minimal-piano-fixture
python3 -m app.main start-practice minimal-piano-fixture
python3 -m app.main finish-practice <session_id> --midi-log-path scores/minimal-piano-fixture/performance_fixture.json
python3 -m app.main listen-mock-practice minimal-piano-fixture --mock-mode rough --max-notes 24
python3 -m app.main ask "查看 minimal-piano-fixture 的学习进度和计划"
```

## Hermes Skills

项目内置三个本地 Skill：

- `skills/piano-teacher-conductor`：自然语言主控，负责协调练习 workflow。
- `skills/piano-practice-reviewer`：练习反馈子 agent，用于把 MIDI-vs-score 分析转成教学建议。
- `skills/score-import-reviewer`：谱面导入复核子 agent，用于检查 PDF/MusicXML 导入质量。

`AGENTS.md` 会提示 Hermes/Codex 优先使用这些脚本式 Skill，而不是 MCP。MCP 兼容入口仍在 `scripts/piano_teacher_mcp`。

## 验证

Smoke tests：

```bash
python3 tests/smoke_test.py
python3 tests/dashboard_flow_smoke_test.py
python3 tests/natural_language_conductor_smoke_test.py
python3 tests/mcp_smoke_test.py
python3 -m compileall app scripts tests
```

Skill 校验使用 Hermes venv，因为其中包含 `yaml`：

```bash
/Users/zonghe/.hermes/hermes-agent/venv/bin/python \
  /Users/zonghe/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  /Users/zonghe/Downloads/piano_teacher/skills/piano-teacher-conductor
```

对 `piano-practice-reviewer` 和 `score-import-reviewer` 重复执行同样校验。

## 运行要求

- Python 3.11 或兼容 Python 3。
- Hermes CLI，用于自然语言对话和子 agent workflow。
- Audiveris，用于 PDF 转 MusicXML：

```text
/Applications/Audiveris.app/Contents/MacOS/Audiveris
```

项目路径配置在 `app/settings.json`。更通用的配置模板见 `app/settings.example.json`。

## 当前限制

- 真实硬件 MIDI 录制仍是 stub；当前支持 mock MIDI 和 JSON MIDI fixture。
- PDF 转 MusicXML 质量依赖 Audiveris，正式练习分析前建议人工复核。
- LLM 子 agent 只在确定性结构化数据生成之后做 review 和教学表达，不直接计算分数。
- 仓库中已提交的 session/profile JSON 目前作为开发 fixture 和示例数据。

更详细的日常操作见 `USER_MANUAL.md`。
