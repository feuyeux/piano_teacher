# Piano Teacher Agent 使用手册

这份手册面向日常使用：如何准备曲目、开始练习、结束练习、查看反馈、复核 PDF 转谱，以及排查常见问题。项目介绍和架构概览见 `README.md`。

## 1. 推荐入口

在项目根目录执行：

```bash
cd /Users/zonghe/Downloads/piano_teacher
```

推荐使用脚本式 Hermes Skill 入口：

```bash
scripts/start_hermes_piano_teacher_cli
```

启动后直接在 Hermes CLI 里说：

```text
准备 por-una-cabeza-feisi
mock 听我练习 por-una-cabeza-feisi 的前40个音，模式 rough
查看 por-una-cabeza-feisi 的学习进度和下一步计划
请记住 por-una-cabeza-feisi：目标是慢速稳定右手旋律，下次目标是合手前复核第13小节，重点关注 right_hand timing
```

也可以不进入交互 CLI，直接调用同一个主控脚本：

```bash
scripts/hermes_piano_teacher "<自然语言请求>"
```

这个入口会启用 Hermes 子 agent：

- 主控 agent：识别意图，调用本地 workflow。
- 练习反馈子 agent：把 MIDI/谱面对齐后的结构化分析转成练习建议。
- 谱面导入复核子 agent：review PDF/MusicXML 转谱风险。

如果不用包装脚本，也可以在项目根目录直接运行 `hermes chat --cli`。关键是从项目根目录启动，让 Hermes 读取 `AGENTS.md`。

MCP server 仍保留为兼容入口，但后续优先维护 Skill + 脚本入口。

## 2. 当前配置

Hermes 状态检查：

```bash
hermes status
```

项目当前使用的配置文件：

```text
app/settings.json
```

PDF 转 MusicXML 使用 Audiveris：

```text
/Applications/Audiveris.app/Contents/MacOS/Audiveris
```

MCP 兼容入口：

```text
scripts/piano_teacher_mcp
```

检查 MCP 工具：

```bash
hermes mcp test piano-teacher
```

正常工具列表包含：

```text
refresh_library
normalize_score
prepare_piece
start_practice
finish_practice
listen_mock_practice
update_teacher_memory
get_teacher_memory
review_score_import
```

## 3. 目录说明

```text
app/                 业务代码、agent、workflow、services、tools
skills/              Hermes/Codex 本地 Skill
scripts/             Skill 入口、MCP 启动脚本、Hermes 子 agent helper
scores/              曲库、MusicXML/MXL、normalized_score、转谱 review
sessions/            练习会话、MIDI log、analysis、feedback
profiles/            曲目长期练习画像
tests/               smoke tests
config/              示例配置
```

常见输出：

```text
scores/<piece_id>/normalized_score.json
scores/<piece_id>/score_import_review.json
scores/<piece_id>/review_request.json
sessions/<session_id>/session.json
sessions/<session_id>/analysis.json
sessions/<session_id>/feedback.json
profiles/<piece_id>.json
```

## 4. 自然语言使用流程

准备曲目：

```bash
scripts/hermes_piano_teacher "准备 por-una-cabeza-feisi"
```

Mock 听练习并生成反馈：

```bash
scripts/hermes_piano_teacher "mock 听我练习 por-una-cabeza-feisi 的前40个音，模式 rough，然后告诉我分数和下一步练法。"
```

查看学习进度：

```bash
scripts/hermes_piano_teacher "查看 por-una-cabeza-feisi 的学习进度和下一步计划。"
```

复核 PDF 谱面导入：

```bash
scripts/hermes_piano_teacher "复核琴谱 PDF /Users/zonghe/Downloads/piano_teacher/Por_una_cabeza_Feisi.pdf"
```

当前真实 MIDI 录制仍是本地骨架。设备未接入时，用 `mock 听我练习` 流程验证完整对话和分析闭环。

## 5. 直接命令行流程

刷新曲库：

```bash
python3 -m app.main refresh-library
```

标准化谱面：

```bash
python3 -m app.main normalize-score por-una-cabeza-feisi
```

开始练习：

```bash
python3 -m app.main start-practice por-una-cabeza-feisi
```

命令会返回 `session.session_id`。结束练习时使用这个 ID：

```bash
python3 -m app.main finish-practice <session_id> --midi-log-path <midi_log_path>
```

使用测试 MIDI fixture：

```bash
python3 -m app.main finish-practice <session_id> --midi-log-path scores/minimal-piano-fixture/performance_fixture.json
```

一条命令跑 mock 练习闭环：

```bash
python3 -m app.main listen-mock-practice minimal-piano-fixture --mock-mode rough --max-notes 24
```

自然语言 CLI：

```bash
python3 -m app.main ask "查看 minimal-piano-fixture 的学习进度和计划"
```

## 6. PDF 到可分析谱面

使用主 CLI review PDF：

```bash
python3 -m app.main review-score-import \
  --pdf-path Por_una_cabeza_Feisi.pdf \
  --piece-id por-una-cabeza-feisi
```

也可以直接运行 score import agent：

```bash
python3 -m app.agents.score_import_review_agent \
  --pdf Por_una_cabeza_Feisi.pdf \
  --piece-id por-una-cabeza-feisi \
  --output-dir scores/por-una-cabeza-feisi \
  --audiveris-command "/Applications/Audiveris.app/Contents/MacOS/Audiveris -batch -export -output {output_dir} {input}" \
  --timeout-seconds 900
```

如果要显式使用 Hermes 做模型复核：

```bash
python3 -m app.agents.score_import_review_agent \
  --pdf Por_una_cabeza_Feisi.pdf \
  --piece-id por-una-cabeza-feisi \
  --output-dir scores/por-una-cabeza-feisi \
  --review-command /Users/zonghe/Downloads/piano_teacher/scripts/hermes_score_import_review
```

成功后通常会看到：

```text
conversion.status: completed
quality_report.validation_status: valid
agent_decision: needs_manual_review
```

`needs_manual_review` 是正常的谨慎结论。OMR 转谱进入正式练习分析前，建议用 MuseScore 或其他打谱软件对照 PDF 检查。

完成导入后刷新和标准化：

```bash
python3 -m app.main refresh-library
python3 -m app.main normalize-score por-una-cabeza-feisi
```

## 7. 工具说明

### `prepare_piece`

刷新曲库，并可选地标准化指定曲目。

```json
{
  "piece_id": "por-una-cabeza-feisi"
}
```

输出包含 `library` 和 `normalized`。

### `refresh_library`

扫描 `scores/`，更新 `scores/piece_index.json`。

### `review_score_import`

将 PDF 转成 MusicXML，或 review 已有 MusicXML/MXL，并生成转换质量报告。

```json
{
  "pdf_path": "/absolute/path/to/score.pdf",
  "piece_id": "piece-id"
}
```

也支持：

```json
{
  "musicxml_path": "/absolute/path/to/score.mxl",
  "piece_id": "piece-id"
}
```

主要输出字段：

```text
conversion.status
quality_report.validation_status
musicxml_path
agent_decision
model_review
```

常见 `agent_decision`：

```text
accept
needs_manual_review
reject
```

### `normalize_score`

把主 MusicXML/MXL 转成内部标准谱面：

```text
scores/<piece_id>/normalized_score.json
```

### `start_practice`

创建练习会话，返回 `session.session_id`。

### `finish_practice`

读取 MIDI 事件 JSON，和标准化谱面对齐，生成分析、反馈并更新 profile。

### `listen_mock_practice`

自动生成一份 mock MIDI 事件 JSON，并立即跑分析和反馈。适合没有真实 MIDI 设备时验证练习流程。

`mock_mode` 可选：

```text
clean
rough
pitch_errors
timing_errors
missed_notes
```

### `update_teacher_memory`

手动更新 `profiles/<piece_id>.json` 中的长期画像字段。

```json
{
  "piece_id": "por-una-cabeza-feisi",
  "note": "用户希望先慢练右手旋律并检查八度记号。",
  "current_goal": "右手旋律慢速准确",
  "next_goal": "合手前复核第13、17、18小节",
  "teacher_focus_tags": ["right_hand", "slow_practice", "octave_shift"]
}
```

### `get_teacher_memory`

读取曲目的长期练习画像。

## 8. 验证命令

最小练习闭环：

```bash
python3 tests/smoke_test.py
```

Dashboard/mock 流程：

```bash
python3 tests/dashboard_flow_smoke_test.py
```

自然语言主控流程：

```bash
python3 tests/natural_language_conductor_smoke_test.py
```

MCP 兼容入口：

```bash
python3 tests/mcp_smoke_test.py
```

语法检查：

```bash
python3 -m compileall app scripts tests
```

Skill 校验：

```bash
/Users/zonghe/.hermes/hermes-agent/venv/bin/python \
  /Users/zonghe/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  /Users/zonghe/Downloads/piano_teacher/skills/piano-teacher-conductor
```

对 `piano-practice-reviewer` 和 `score-import-reviewer` 重复执行同样校验。

## 9. 常见问题

### Hermes 显示模型不可用

先检查：

```bash
hermes status
```

如果模型配置不对，再检查 Hermes 配置。当前项目不要求把模型配置写入仓库。

### MCP 工具找不到

检查：

```bash
hermes mcp list
hermes mcp test piano-teacher
```

`piano-teacher` 应指向：

```text
/Users/zonghe/Downloads/piano_teacher/scripts/piano_teacher_mcp
```

### PDF 转换失败，提示找不到 Audiveris

检查 Audiveris 是否存在：

```bash
/Applications/Audiveris.app/Contents/MacOS/Audiveris -help
```

如果路径不同，修改：

```text
app/settings.json
```

把 `musicxml_converter_command` 改成正确路径。

### MusicXML valid，但 `agent_decision` 是 `needs_manual_review`

这是正常情况。OMR 转谱可能存在：

- 节奏识别错误
- 左右手/声部分配错误
- 八度记号没有正确链接
- 连线、表情、文字标记漏识别

建议打开 `.mxl` 与原 PDF 对照重点小节。

### Hermes 调 PDF 工具超时

PDF 转换较慢。可以先直接用命令行完成转换和 review，再让 Hermes 做后续 `refresh_library` 和 `normalize_score`。

## 10. 当前限制

- MIDI 录制仍是本地骨架，真实电子琴 MIDI 输入还需要继续接入设备。
- PDF 转 MusicXML 依赖 Audiveris，转换质量需要人工复核。
- MCP 模式默认不做嵌套 Hermes 模型复核，避免工具调用超时。
- 教师反馈基于当前结构化分析数据，后续可以继续增强练习策略和长期画像。
