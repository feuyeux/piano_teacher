# Piano Teacher Agent 使用手册

本项目把 Hermes Agent、脚本式 Skill、Audiveris 谱面转换和本地钢琴练习分析流程串在一起。推荐让 Hermes 通过项目内 Skill 调用脚本完成练习流程；MCP server 保留为兼容入口。

## 1. 当前配置

### Hermes 模型

Hermes 已配置为：

```text
Provider: OpenAI Codex
Model: gpt-5.4
```

可用下面的命令检查：

```bash
hermes status
```

### MCP Server

Hermes 中已配置的 MCP server 名称是：

```text
piano-teacher
```

它的启动脚本是：

```text
/Users/zonghe/Downloads/piano_teacher/scripts/piano_teacher_mcp
```

可用下面的命令检查工具是否能被 Hermes 发现：

```bash
hermes mcp test piano-teacher
```

正常应看到 9 个工具：

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

### Audiveris 谱面转换

PDF 转 MusicXML 使用 Audiveris：

```text
/Applications/Audiveris.app/Contents/MacOS/Audiveris
```

项目配置在：

```text
app/settings.json
```

其中 `musicxml_converter_command` 当前指向 Audiveris，并会把转换输出写入 `scores/<piece_id>/`。

## 2. 目录说明

```text
app/                 业务代码、agent、workflow、MCP server
scripts/             MCP 启动脚本和模型 review helper
scores/              曲库和转换后的 MusicXML / normalized_score
sessions/            练习会话记录
profiles/            曲目长期练习画像
tests/               smoke tests
Por_una_cabeza_Feisi.pdf  示例钢琴谱 PDF
```

常用生成文件：

```text
scores/<piece_id>/<piece>.mxl          Audiveris 转出的 MusicXML
scores/<piece_id>/score_import_review.json
scores/<piece_id>/review_request.json
scores/<piece_id>/normalized_score.json
scores/piece_index.json
```

## 3. 日常使用流程

### 3.0 在 Hermes Dashboard 中用自然语言操作

推荐在项目目录下启动 Hermes，并使用 `skills/` 中的脚本式 Skill。主入口是：

```bash
scripts/hermes_piano_teacher "<你的自然语言请求>"
```

该入口会启用 Hermes 子 agent：主控 agent 负责路由和调用本地 workflow，练习反馈子 agent 负责把 MIDI/谱面对齐后的结构化分析转成练习建议，谱面导入复核子 agent 负责 review PDF 转 MusicXML 的风险。

准备曲目、刷新曲库、标准化谱面：

```bash
scripts/hermes_piano_teacher "帮我更新钢琴老师记忆，刷新曲库，并把 por-una-cabeza-feisi 准备好用于练习。"
```

手动更新老师记忆：

```text
请记住：我今天练 por-una-cabeza-feisi，目标是慢速稳定右手旋律，重点关注第13、17、18小节。
```

Mock 听练习并给反馈：

```bash
scripts/hermes_piano_teacher "请 mock 听我练习 por-una-cabeza-feisi 的前40个音，模式 rough，然后告诉我分数和下一步练法。"
```

读取老师记忆：

```bash
scripts/hermes_piano_teacher "查看 por-una-cabeza-feisi 的钢琴老师记忆。"
```

目前 dashboard 下的“听我练习”默认走 mock MIDI。等你连接真实 MIDI 设备后，再把 MIDI recorder 从 mock/stub 替换成真实输入调试。

如果仍想走 MCP，`piano-teacher` server 和工具列表仍可用；但后续开发优先维护 Skill + 脚本入口。

### 3.1 用 Hermes 导入 PDF 谱面

在 Hermes 中直接说类似下面的话：

```text
调用 review_score_import 工具处理 /Users/zonghe/Downloads/piano_teacher/Por_una_cabeza_Feisi.pdf，piece_id=por-una-cabeza-feisi。
```

成功时，Hermes 会返回类似：

```text
conversion.status: completed
quality_report.validation_status: valid
agent_decision: needs_manual_review
```

说明：

- `completed` 表示 Audiveris 已成功转出 `.mxl`
- `valid` 表示 MusicXML 能被解析，并且有小节和音符
- `needs_manual_review` 是正常的谨慎结论，表示 OMR 转谱仍建议人工对照 PDF 检查

示例输出文件：

```text
scores/por-una-cabeza-feisi/Por_una_cabeza_Feisi.mxl
scores/por-una-cabeza-feisi/score_import_review.json
```

### 3.2 刷新曲库

PDF 转成 MusicXML 后，刷新曲库索引：

```bash
python3 -m app.main refresh-library
```

也可以让 Hermes 调工具：

```text
调用 refresh_library 工具刷新曲库。
```

刷新后会更新：

```text
scores/piece_index.json
```

### 3.3 标准化谱面

标准化会把 MusicXML 转成项目内部使用的 `normalized_score.json`：

```bash
python3 -m app.main normalize-score por-una-cabeza-feisi
```

输出位置：

```text
scores/por-una-cabeza-feisi/normalized_score.json
```

也可以让 Hermes 调：

```text
调用 normalize_score 工具，piece_id 是 por-una-cabeza-feisi。
```

### 3.4 开始练习

创建练习会话：

```bash
python3 -m app.main start-practice por-una-cabeza-feisi
```

命令会返回 `session_id`，后续结束练习时要用。

当前 MIDI 录制是本地骨架/stub，真实硬件录制还需要继续接入 MIDI 设备。

### 3.5 结束练习并生成反馈

使用已有 MIDI fixture 或标准事件 JSON 做分析：

```bash
python3 -m app.main finish-practice <session_id> --midi-log-path <midi_log_path>
```

项目内已有测试 fixture：

```text
scores/minimal-piano-fixture/performance_fixture.json
```

结束练习后会生成：

```text
sessions/<session_id>/session.json
sessions/<session_id>/analysis.json
sessions/<session_id>/feedback.json
profiles/<piece_id>.json
```

## 4. 命令行快速参考

检查 Hermes：

```bash
hermes status
```

检查 MCP 工具：

```bash
hermes mcp test piano-teacher
```

测试 MCP server：

```bash
python3 tests/mcp_smoke_test.py
```

测试最小练习闭环：

```bash
python3 tests/smoke_test.py
```

导入 PDF：

```bash
python3 -m app.agents.score_import_review_agent \
  --pdf Por_una_cabeza_Feisi.pdf \
  --piece-id por-una-cabeza-feisi \
  --output-dir scores/por-una-cabeza-feisi \
  --audiveris-command "/Applications/Audiveris.app/Contents/MacOS/Audiveris -batch -export -output {output_dir} {input}" \
  --timeout-seconds 900
```

如果需要使用 Hermes GPT/Codex 做模型复核，可加：

```bash
--review-command /Users/zonghe/Downloads/piano_teacher/scripts/hermes_score_import_review
```

注意：Hermes 外层调用 MCP 工具时，MCP 启动脚本会默认关闭嵌套模型复核，避免 “Hermes 调工具，工具内部再调 Hermes” 导致超时。直接命令行运行时可以手动加 `--review-command`。

## 5. 工具说明

### prepare_piece

刷新曲库，并可选地标准化指定曲目。适合 dashboard 中“更新记忆/准备这首曲子/刷新曲库并标准化”这类自然语言请求。

输入：

```json
{
  "piece_id": "por-una-cabeza-feisi"
}
```

如果不传 `piece_id`，只刷新曲库。

输出包含：

```text
library
normalized
```

### refresh_library

扫描 `scores/`，更新曲库索引。

输入：无

主要输出：

```json
{
  "status": "completed",
  "piece_count": 2,
  "pieces": []
}
```

### review_score_import

将 PDF 转成 MusicXML，并生成转换质量报告。

输入：

```json
{
  "pdf_path": "/absolute/path/to/score.pdf",
  "piece_id": "piece-id"
}
```

也可以 review 已有 MusicXML：

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
accept                可进入后续流程
needs_manual_review   可解析，但建议人工复核
reject                转换失败或 MusicXML 无效
```

### normalize_score

把 `scores/<piece_id>/` 里的主 MusicXML 转成内部标准谱面。

输入：

```json
{
  "piece_id": "por-una-cabeza-feisi"
}
```

输出：

```text
scores/<piece_id>/normalized_score.json
```

### start_practice

创建练习会话。

输入：

```json
{
  "piece_id": "por-una-cabeza-feisi"
}
```

输出包含：

```text
session.session_id
```

### finish_practice

读取 MIDI 事件 JSON，和标准化谱面对齐分析，生成教师反馈。

输入：

```json
{
  "session_id": "...",
  "midi_log_path": "/absolute/path/to/performance_fixture.json"
}
```

输出包含：

```text
analysis.overall_score
feedback.summary
```

### listen_mock_practice

Mock 监听用户练习，自动生成一份 MIDI 事件 JSON，随后调用分析流程、更新老师记忆/profile，并生成教师反馈。适合设备尚未连接时在 Hermes dashboard 里验证练习对话。

输入：

```json
{
  "piece_id": "por-una-cabeza-feisi",
  "mock_mode": "rough",
  "max_notes": 40,
  "user_command": "请听我练习前40个音"
}
```

`mock_mode` 可选：

```text
clean
rough
pitch_errors
timing_errors
missed_notes
```

输出包含：

```text
session.session_id
analysis.overall_score
feedback.summary
profile
```

### update_teacher_memory

手动更新钢琴老师记忆，也就是 `profiles/<piece_id>.json` 中的长期画像字段。适合告诉老师“我今天想练什么”“下次提醒我什么”“重点关注哪些标签”。

输入：

```json
{
  "piece_id": "por-una-cabeza-feisi",
  "note": "用户希望先慢练右手旋律并检查八度记号。",
  "current_goal": "右手旋律慢速准确",
  "next_goal": "合手前复核第13、17、18小节",
  "teacher_focus_tags": ["right_hand", "slow_practice", "octave_shift"]
}
```

输出：

```text
profile
```

### get_teacher_memory

读取钢琴老师记忆。

输入：

```json
{
  "piece_id": "por-una-cabeza-feisi"
}
```

## 6. 示例：从 PDF 到可分析谱面

以下以 `Por_una_cabeza_Feisi.pdf` 为例：

```bash
python3 -m app.agents.score_import_review_agent \
  --pdf Por_una_cabeza_Feisi.pdf \
  --piece-id por-una-cabeza-feisi \
  --output-dir scores/por-una-cabeza-feisi \
  --audiveris-command "/Applications/Audiveris.app/Contents/MacOS/Audiveris -batch -export -output {output_dir} {input}" \
  --timeout-seconds 900
```

刷新曲库：

```bash
python3 -m app.main refresh-library
```

标准化谱面：

```bash
python3 -m app.main normalize-score por-una-cabeza-feisi
```

成功后检查：

```text
scores/por-una-cabeza-feisi/Por_una_cabeza_Feisi.mxl
scores/por-una-cabeza-feisi/normalized_score.json
```

## 7. 常见问题

### Hermes 显示模型不可用

先检查：

```bash
hermes status
```

当前应为：

```text
Provider: OpenAI Codex
Model: gpt-5.4
```

如果不是，可以重新设置：

```bash
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.4
hermes config set model.model gpt-5.4
hermes config set model.base_url https://chatgpt.com/backend-api/codex
hermes config set model.api_mode codex_responses
```

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

把 `musicxml_converter_command` 改成正确的可执行文件路径。

### MusicXML valid，但 agent_decision 是 needs_manual_review

这是正常情况。OMR 转谱可能存在：

- 节奏识别错误
- 左右手/声部分配错误
- 八度记号没有正确链接
- 连线、表情、文字标记漏识别

建议用 MuseScore 或其他打谱软件打开 `.mxl`，和原 PDF 对照关键小节。

### Hermes 调 PDF 工具超时

PDF 转换较慢，外层 Hermes 调 MCP 时通常需要 1 分钟左右。若超过 MCP 默认超时，可先直接用命令行转换：

```bash
python3 -m app.agents.score_import_review_agent \
  --pdf Por_una_cabeza_Feisi.pdf \
  --piece-id por-una-cabeza-feisi \
  --output-dir scores/por-una-cabeza-feisi \
  --audiveris-command "/Applications/Audiveris.app/Contents/MacOS/Audiveris -batch -export -output {output_dir} {input}" \
  --timeout-seconds 900
```

然后再让 Hermes 调 `refresh_library` 和 `normalize_score`。

## 8. 当前限制

- MIDI 录制仍是本地骨架，真实电子琴 MIDI 输入需要继续接入设备。
- PDF 转 MusicXML 依赖 Audiveris，转换质量需要人工复核。
- MCP 模式默认不做嵌套 Hermes 模型复核，避免工具调用超时。
- 教师反馈基于当前结构化分析数据，后续可以继续增强练习策略和长期画像。
