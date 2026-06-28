# Piano Teacher Agent

Piano Teacher Agent 是一个本地钢琴练习助手。它把谱面导入、MusicXML 标准化、MIDI 与琴谱对齐分析、Hermes/Codex 项目技能、长期练习记忆和基础乐理讲解连成一个可以日常使用的练琴系统。

最推荐的使用方式是自然语言对话：你说“准备这首曲子”“听我练前 24 个音”“结束练习并分析 MIDI”“讲一下节奏和拍子”，系统会调用本地确定性 workflow 完成解析、对齐、评分和落盘，再让教学子 agent 把结果整理成可执行的练习建议。

## 核心能力

- 刷新曲库，识别 `scores/` 下的 MusicXML/MXL/PDF 导入结果。
- 将 MusicXML/MXL 标准化为 `normalized_score.json`，用于练习分析。
- 创建练习会话，分析 JSON MIDI 事件与谱面的偏差。
- 使用 mock MIDI 跑完整练习闭环，适合没有硬件 MIDI 设备时测试和练习。
- 生成结构化反馈：总体评分、问题小节、问题标签、下一步练习计划。
- 维护每首曲子的长期学习画像，保存目标、关注点和历史反馈摘要。
- 复核 PDF 或 MusicXML 导入质量，降低 OMR 转谱错误进入练习分析的风险。
- 从本地 `knowledge/` 读取基础乐理知识，在平时问答和练习反馈里穿插解释。

## 日常入口

进入项目根目录：

```bash
cd /path/to/piano_teacher
```

启动 Hermes CLI：

```bash
scripts/start_hermes_piano_teacher_cli
```

启动后直接说：

```text
你能做什么
列出曲库里有哪些曲子
准备 minimal-piano-fixture
mock 听我练习 minimal-piano-fixture 前24个音 rough 模式
查看 minimal-piano-fixture 的学习进度和计划
讲一下节奏和拍子
```

仓库根目录的 `AGENTS.md` 会让 Hermes 优先调用：

```bash
scripts/hermes_piano_teacher "<你的原话>"
```

所以在 Hermes 对话里不用手动复制命令。需要直接从 shell 调用时，也可以运行同一个脚本：

```bash
scripts/hermes_piano_teacher "mock 听我练习 minimal-piano-fixture 前24个音 rough 模式"
```

## 常用命令

自然语言主控：

```bash
scripts/hermes_piano_teacher "你能做什么"
scripts/hermes_piano_teacher "列出曲库里有哪些曲子"
scripts/hermes_piano_teacher "准备 minimal-piano-fixture"
scripts/hermes_piano_teacher "查看 minimal-piano-fixture 的学习进度和计划"
scripts/hermes_piano_teacher "解释一下和弦"
```

不经过 Hermes 的底层 CLI：

```bash
python3 -m app.main refresh-library
python3 -m app.main normalize-score minimal-piano-fixture
python3 -m app.main start-practice minimal-piano-fixture
python3 -m app.main finish-practice <session_id> --midi-log-path scores/minimal-piano-fixture/performance_fixture.json
python3 -m app.main listen-mock-practice minimal-piano-fixture --mock-mode rough --max-notes 24
python3 -m app.main ask "讲一下节奏和拍子"
```

复核谱面导入：

```bash
python3 -m app.main review-score-import \
  --pdf-path /absolute/path/score.pdf \
  --piece-id my-piece
```

## 项目结构

```text
app/         业务代码、agent、workflow、services、tools
config/      示例配置
knowledge/   本地基础乐理知识库
profiles/    每首曲子的长期练习画像
scores/      曲库、谱面、标准化结果、导入复核结果
scripts/     Hermes/Codex 入口和子 agent helper
sessions/    练习会话、MIDI log、analysis、feedback
skills/      项目内 Hermes/Codex skills
tests/       smoke tests
```

关键模块：

- `app/agents/conductor_agent.py`：自然语言主控，负责识别意图并调用 workflow。
- `app/workflows/`：刷新曲库、准备曲目、开始/结束练习、mock 听练习。
- `app/services/feedback_service.py`：组合练习分析、profile 和乐理上下文，生成教学反馈。
- `app/services/theory_knowledge_service.py`：读取并检索本地乐理知识库。
- `knowledge/music_theory_basics.json`：基础乐理条目。
- `skills/piano-teacher-conductor/`：Hermes/Codex 对话入口技能。

## 数据策略

仓库保留少量 fixture 和示例数据，方便 smoke test 运行。日常练习产生的新 `sessions/`、个人 `profiles/`、新导入的 `scores/<piece_id>/` 默认不应提交；这些路径由 `.gitignore` 保护。

如果确实要把一首新曲目作为 fixture 纳入仓库，先确认谱面版权和数据体积，再显式 `git add -f` 对应文件。

## 配置

默认配置在：

```text
app/settings.json
```

便携模板在：

```text
app/settings.example.json
```

PDF 转 MusicXML 依赖 Audiveris。当前默认路径：

```text
/Applications/Audiveris.app/Contents/MacOS/Audiveris
```

## 验证

常用 smoke tests：

```bash
python3 tests/smoke_test.py
python3 tests/natural_language_conductor_smoke_test.py
python3 tests/dashboard_flow_smoke_test.py
python3 tests/mcp_smoke_test.py
```

语法检查：

```bash
python3 -m compileall app scripts tests
```

为了避免验证时产生 `.pyc`，可以加：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/smoke_test.py
```

## 当前限制

- PDF 转 MusicXML 依赖 OMR，正式练习分析前建议人工复核。
- 真实硬件 MIDI 录制仍在持续完善；当前最稳定的是 mock MIDI 和 JSON MIDI fixture。
- Hermes 子 agent 负责教学表达和复核建议，不替代本地确定性对齐、评分和数据落盘。

更详细的日常操作见 `USER_MANUAL.md`。
