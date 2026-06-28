# Piano Teacher Agent 使用手册

这份手册面向日常练琴。你可以把系统当成一个本地钢琴老师：它会帮你准备谱面、听一段练习、分析问题、记录目标，也可以在合适的时候讲一点乐理。

## 1. 启动

进入项目目录：

```bash
cd /path/to/piano_teacher
```

启动交互式 Hermes：

```bash
scripts/start_hermes_piano_teacher_cli
```

启动后直接输入自然语言，例如：

```text
你能做什么
列出曲库里有哪些曲子
准备 minimal-piano-fixture
mock 听我练习 minimal-piano-fixture 前24个音 rough 模式
查看 minimal-piano-fixture 的学习进度和计划
```

不进入交互模式时，可以直接调用：

```bash
scripts/hermes_piano_teacher "查看 minimal-piano-fixture 的学习进度和计划"
```

## 2. 推荐练习流程

第一次使用或新增谱面后：

```text
列出曲库里有哪些曲子
准备 <piece_id>
mock 听我练习 <piece_id> 前24个音 rough 模式
查看 <piece_id> 的学习进度和计划
请记住 <piece_id>：目标是慢速稳定，下次目标是保持当前速度完整弹奏，重点关注 timing
```

持续练习时：

```text
查看 <piece_id> 的学习进度和计划
mock 听我练习 <piece_id> 前40个音 timing_errors 模式
请记住 <piece_id>：下次目标是把问题小节慢速连起来，重点关注 left_hand timing
```

想补一点乐理时：

```text
讲一下节奏和拍子
解释一下和弦
什么是音程
踏板为什么会让声音变糊
```

## 3. 曲库和准备曲目

查看或刷新曲库：

```text
列出曲库里有哪些曲子
刷新曲库
曲库里有什么
```

准备曲目：

```text
准备 minimal-piano-fixture
准备 por-una-cabeza-feisi
标准化 minimal-piano-fixture
```

准备曲目会刷新 `scores/piece_index.json`，并生成或更新：

```text
scores/<piece_id>/normalized_score.json
```

练习分析依赖这个标准化谱面，所以正式练习前建议先准备一次。

## 4. Mock 听练习

没有真实 MIDI 设备时，优先使用 mock 听练习。它会生成模拟 MIDI 事件并立即跑分析。

```text
mock 听我练习 minimal-piano-fixture 前24个音 rough 模式
模拟听我练 por-una-cabeza-feisi 前40个音，重点看节奏
听我练习 minimal-piano-fixture 前32个音 clean 模式
```

可用模式：

```text
clean          接近正确演奏
rough          混合错音和时值偏差
pitch_errors   偏向音高错误
timing_errors  偏向节奏/时值错误
missed_notes   偏向漏音
```

常见输出：

```text
sessions/<session_id>/mock_midi_log.json
sessions/<session_id>/analysis.json
sessions/<session_id>/feedback.json
profiles/<piece_id>.json
```

## 5. 结束一次 MIDI 练习

如果已经有 MIDI 事件 JSON，可以结束最近一次练习并分析：

```text
结束 minimal-piano-fixture 练习，midi 在 /absolute/path/performance.json
完成这次练习，MIDI 在 /absolute/path/performance.json
finish practice, midi at /absolute/path/performance.json
```

系统会读取 MIDI 事件，和标准化谱面对齐，生成 `analysis.json`、`feedback.json`，并更新 `profiles/<piece_id>.json`。

路径要用绝对路径，并以 `.json` 结尾。测试 fixture 示例：

```text
/path/to/piano_teacher/scores/minimal-piano-fixture/performance_fixture.json
```

## 6. 查看和更新老师记忆

查看长期学习画像：

```text
查看 minimal-piano-fixture 的学习进度和计划
看 por-una-cabeza-feisi 的老师记忆
show progress for minimal-piano-fixture
```

记录下一步目标：

```text
请记住 minimal-piano-fixture：目标是慢速稳定，下次目标是保持当前速度完整弹奏，重点关注 left_hand timing
记录一下 por-una-cabeza-feisi：阶段是分手慢练，目标是右手旋律稳定，下次目标是合手前复核第13小节，重点关注 right_hand timing
```

常见字段：

```text
stage_label
current_goal
next_goal
teacher_focus_tags
last_feedback_digest
```

## 7. 乐理问答

基础乐理知识保存在：

```text
knowledge/music_theory_basics.json
```

你可以直接问：

```text
讲一下节奏和拍子
解释一下音阶和调号
什么是连奏和断奏
和弦怎么帮助左手伴奏练习
```

结束练习时，反馈也会根据分析结果挑选相关乐理点。例如节奏问题会补充节拍、时值或细分的提示；错音问题会更倾向音高、音程或调号提示。

## 8. 导入和复核谱面

复核 PDF：

```text
复核琴谱 PDF /absolute/path/score.pdf
导入并检查 /absolute/path/score.pdf
```

复核已有 MusicXML/MXL：

```text
复核 MusicXML /absolute/path/score.musicxml
检查 MXL /absolute/path/score.mxl
```

输出通常在：

```text
scores/<piece_id>/review_request.json
scores/<piece_id>/score_import_review.json
```

常见结论：

```text
accept
needs_manual_review
reject
```

`needs_manual_review` 不代表失败。PDF OMR 经常会漏掉声部、连线、八度记号、节奏或左右手分配；正式用于练习分析前，建议用 MuseScore 等工具对照原谱检查。

## 9. 直接命令行

自然语言入口：

```bash
scripts/hermes_piano_teacher "你能做什么"
scripts/hermes_piano_teacher "准备 minimal-piano-fixture"
scripts/hermes_piano_teacher "mock 听我练习 minimal-piano-fixture 前24个音 rough 模式"
scripts/hermes_piano_teacher "解释一下和弦"
```

底层 workflow：

```bash
python3 -m app.main refresh-library
python3 -m app.main normalize-score minimal-piano-fixture
python3 -m app.main start-practice minimal-piano-fixture
python3 -m app.main finish-practice <session_id> --midi-log-path scores/minimal-piano-fixture/performance_fixture.json
python3 -m app.main listen-mock-practice minimal-piano-fixture --mock-mode rough --max-notes 24
python3 -m app.main ask "讲一下节奏和拍子"
```

复核导入：

```bash
python3 -m app.main review-score-import \
  --pdf-path /absolute/path/score.pdf \
  --piece-id my-piece
```

## 10. 文件和清理

日常运行会生成：

```text
sessions/<session_id>/
profiles/<piece_id>.json
scores/<piece_id>/
```

这些通常是个人练习数据或导入数据，默认不需要提交。`.gitignore` 已经忽略新的运行产物和缓存；如果要把某个新谱面作为测试 fixture 纳入仓库，需要手动确认后再强制添加。

## 11. 常见问题

### 不知道能说什么

说：

```text
你能做什么
```

主控会返回当前项目支持的能力和例句。

### 找不到曲目

先说：

```text
列出曲库里有哪些曲子
```

然后使用返回的 `piece_id`。

### 提示需要路径

复核谱面和结束练习时使用绝对路径：

```text
复核琴谱 PDF /absolute/path/score.pdf
结束 <piece_id> 练习，midi 在 /absolute/path/performance.json
```

### PDF 转换失败

检查 Audiveris：

```bash
/Applications/Audiveris.app/Contents/MacOS/Audiveris -help
```

如果路径不同，修改 `app/settings.json` 里的 `musicxml_converter_command`。

### 运行测试后工作区变脏

练习测试会更新 `sessions/`、`profiles/` 或 `scores/piece_index.json`。这些是运行数据。提交前只暂存源码、文档和明确要保留的 fixture。

## 12. 验证

常用验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/smoke_test.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/natural_language_conductor_smoke_test.py
PYTHONDONTWRITEBYTECODE=1 python3 -m app.main ask "解释一下和弦"
```

MCP 兼容入口仍可测：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/mcp_smoke_test.py
```
