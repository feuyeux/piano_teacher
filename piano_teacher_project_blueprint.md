# 钢琴教师 Agent 项目草图

## 1. 目标

给第一版工程实现提供一个可落地的代码骨架草图。重点不是框架选型，而是把模块边界、目录结构、入口流程和核心接口先固定下来。

第一版目标：

- 跑通单次练习闭环
- 支持曲库扫描
- 支持 `MusicXML` 标准化
- 支持 MIDI 录制与分析
- 支持教师 agent 输出反馈

---

## 2. 推荐目录结构

```text
/app
  /agents
    conductor_agent.py
    piano_teacher_agent.py
    score_import_review_agent.py
  /services
    score_library_service.py
    score_normalizer_service.py
    pdf_conversion_service.py
    midi_recording_service.py
    midi_parsing_service.py
    alignment_service.py
    analysis_service.py
    profile_service.py
    feedback_service.py
  /models
    piece_record.py
    practice_session.py
    practice_analysis.py
    piece_progress_profile.py
    normalized_score.py
  /repositories
    piece_repository.py
    session_repository.py
    profile_repository.py
  /workflows
    start_practice_workflow.py
    finish_practice_workflow.py
    generate_feedback_workflow.py
  /tools
    audiveris_runner.py
    musicxml_quality.py
    musicxml_reader.py
    midi_recorder.py
    midi_parser.py
    score_aligner.py
    pdf_to_musicxml.py
  /prompts
    piano_teacher_system_prompt.txt
    feedback_format_prompt.txt
  /schemas
    piece_record.schema.json
    practice_session.schema.json
    practice_analysis.schema.json
    piece_progress_profile.schema.json
    normalized_score.schema.json
  /utils
    paths.py
    ids.py
    time_utils.py
    json_io.py
    logger.py
  config.py
  settings.example.json
  main.py
/scores
/sessions
/profiles
/docs
```

说明：

- `services` 放业务逻辑
- `tools` 放偏底层、可替换的工具封装
- `workflows` 串联一次完整动作
- `repositories` 负责文件落盘和读取
- `models` 对应数据模型定义

---

## 3. 模块职责草图

### 3.1 `conductor_agent`

职责：

- 接收 Hermes 或上层指令
- 判断当前用户意图
- 调用对应 workflow
- 聚合输出结果

建议接口：

```python
class ConductorAgent:
    def handle_command(self, text: str) -> dict: ...
```

### 3.2 `piano_teacher_agent`

职责：

- 只处理教学解释与建议生成
- 输入固定为结构化分析结果和长期画像

建议接口：

```python
class PianoTeacherAgent:
    def generate_feedback(self, payload: dict) -> dict: ...
```

### 3.3 `score_library_service`

职责：

- 扫描曲库目录
- 生成 `PieceRecord`
- 维护曲目索引

建议接口：

```python
class ScoreLibraryService:
    def scan_library(self) -> list[dict]: ...
    def refresh_index(self) -> list[dict]: ...
    def get_piece(self, piece_id: str) -> dict | None: ...
```

### 3.4 `score_normalizer_service`

职责：

- 读取 `MusicXML`
- 输出 `NormalizedScore`
- 写入标准化结果

建议接口：

```python
class ScoreNormalizerService:
    def normalize(self, piece_id: str, musicxml_path: str) -> dict: ...
```

### 3.5 `pdf_conversion_service`

职责：

- 调用外部工具完成 PDF 转 `MusicXML`
- 产出状态与日志

建议接口：

```python
class PdfConversionService:
    def convert(self, piece_id: str, pdf_path: str) -> dict: ...
```

### 3.5.1 `score_import_review_agent`

职责：

- 调用 Audiveris 将 `PDF` 转为 `MusicXML`
- 对转换结果做确定性结构校验
- 将转换日志和谱面摘要交给模型 review
- 输出 `score_import_review.json`，供主控 agent 判断是否进入标准化和练习分析

建议接口：

```python
class ScoreImportReviewAgent:
    def run(
        self,
        piece_id: str,
        output_dir: str,
        pdf_path: str | None = None,
        musicxml_path: str | None = None,
    ) -> dict: ...
```

命令行入口：

```bash
python3 -m app.agents.score_import_review_agent --pdf scores/demo/demo.pdf
python3 -m app.agents.score_import_review_agent --musicxml scores/demo/demo.mxl
```

### 3.6 `midi_recording_service`

职责：

- 启动 / 停止 MIDI 录制
- 创建和更新 `PracticeSession`

建议接口：

```python
class MidiRecordingService:
    def start(self, piece_id: str, practice_mode: str = "full_run") -> dict: ...
    def stop(self, session_id: str) -> dict: ...
```

### 3.7 `alignment_service`

职责：

- 读取标准谱面和 MIDI 事件
- 输出音符级对齐结果

建议接口：

```python
class AlignmentService:
    def align(self, normalized_score_path: str, midi_log_path: str) -> dict: ...
```

### 3.8 `analysis_service`

职责：

- 基于对齐结果生成 `PracticeAnalysis`

建议接口：

```python
class AnalysisService:
    def analyze(self, session_id: str, alignment_result: dict) -> dict: ...
```

### 3.9 `profile_service`

职责：

- 更新和读取 `PieceProgressProfile`

建议接口：

```python
class ProfileService:
    def update_from_analysis(self, piece_id: str, analysis: dict) -> dict: ...
    def get_profile(self, piece_id: str) -> dict | None: ...
```

### 3.10 `feedback_service`

职责：

- 组装教师 agent 输入
- 调用 `piano_teacher_agent`
- 返回标准反馈结构

建议接口：

```python
class FeedbackService:
    def generate(self, piece: dict, session: dict, analysis: dict, profile: dict | None) -> dict: ...
```

---

## 4. Repository 草图

### 4.1 `piece_repository`

职责：

- 保存 `PieceRecord`
- 保存 `piece_index.json`
- 读取曲目信息

核心方法：

```python
save_piece(piece: dict) -> None
save_index(pieces: list[dict]) -> None
load_index() -> list[dict]
get_piece(piece_id: str) -> dict | None
```

### 4.2 `session_repository`

职责：

- 保存单次 session 数据
- 保存分析结果

核心方法：

```python
create_session(session: dict) -> None
update_session(session_id: str, patch: dict) -> dict
save_analysis(session_id: str, analysis: dict) -> None
load_session(session_id: str) -> dict | None
```

### 4.3 `profile_repository`

职责：

- 保存和读取曲目画像

核心方法：

```python
load_profile(piece_id: str) -> dict | None
save_profile(piece_id: str, profile: dict) -> None
```

---

## 5. Workflow 草图

### 5.1 开始练习流程

文件：

- `start_practice_workflow.py`

流程：

1. 解析用户指令中的曲目
2. 查找 `PieceRecord`
3. 检查是否存在可用 `MusicXML`
4. 如无 `MusicXML`，尝试 PDF 转换
5. 检查是否存在 `NormalizedScore`
6. 如无则先标准化谱面
7. 创建 `PracticeSession`
8. 启动 MIDI 录制
9. 返回开始状态

建议接口：

```python
class StartPracticeWorkflow:
    def run(self, piece_id: str | None) -> dict: ...
```

### 5.2 结束练习流程

文件：

- `finish_practice_workflow.py`

流程：

1. 停止 MIDI 录制
2. 读取 `PracticeSession`
3. 加载标准谱面
4. 解析 MIDI
5. 执行对齐
6. 生成 `PracticeAnalysis`
7. 保存分析结果
8. 更新 `PieceProgressProfile`
9. 生成教师反馈
10. 返回练后反馈

建议接口：

```python
class FinishPracticeWorkflow:
    def run(self, session_id: str) -> dict: ...
```

### 5.3 查询进度流程

文件：

- `generate_feedback_workflow.py`

流程：

1. 读取曲目画像
2. 读取最近一次 session 和分析
3. 生成进度总结

建议接口：

```python
class ProgressWorkflow:
    def run(self, piece_id: str) -> dict: ...
```

---

## 6. 命令路由草图

建议先用最简单的规则路由，不要一开始就做复杂自然语言解析。

可支持命令：

- `开始练习`
- `开始练习 <曲名>`
- `结束练习`
- `我弹得怎么样`
- `最近进度如何`
- `刷新曲库`

建议路由逻辑：

```python
def route_command(text: str) -> dict:
    if text.startswith("开始练习"):
        return {"intent": "start_practice", "piece_name": "..."}
    if text in ["结束练习", "练习结束", "我弹完了"]:
        return {"intent": "finish_practice"}
    if text in ["我弹得怎么样", "给我点评一下"]:
        return {"intent": "review_last_session"}
    if text in ["最近进度如何", "看看我的进度"]:
        return {"intent": "show_progress"}
    if text == "刷新曲库":
        return {"intent": "refresh_library"}
    return {"intent": "fallback"}
```

---

## 7. 配置草图

建议 `settings.example.json`：

```json
{
  "score_library_path": "./scores",
  "session_output_path": "./sessions",
  "profile_output_path": "./profiles",
  "piece_index_path": "./scores/piece_index.json",
  "musicxml_converter_command": "",
  "midi_input_device": "",
  "timing_tolerance_ms": 180,
  "duration_tolerance_ratio": 0.35,
  "min_note_duration_ms": 30,
  "partial_alignment_min_ratio": 0.6
}
```

原则：

- 本地差异通过配置解决
- 不在业务代码里写死设备名和工具路径

---

## 8. 数据流草图

### 8.1 曲库扫描

```text
scores/ -> score_library_service -> PieceRecord[] -> piece_repository -> piece_index.json
```

### 8.2 开始练习

```text
command -> conductor_agent -> start_practice_workflow
-> score check / normalize
-> session_repository.create_session
-> midi_recording_service.start
-> session.json
```

### 8.3 结束练习

```text
command -> conductor_agent -> finish_practice_workflow
-> midi_recording_service.stop
-> midi_parsing_service
-> alignment_service
-> analysis_service
-> session_repository.save_analysis
-> profile_service.update_from_analysis
-> feedback_service.generate
```

---

## 9. 第一版 API 草图

如果后面要暴露给 Hermes 或其他 UI，可以先准备这几个应用层接口：

```python
refresh_library() -> dict
list_pieces() -> list[dict]
start_practice(piece_name: str | None) -> dict
stop_practice() -> dict
review_last_session() -> dict
show_progress(piece_name: str | None) -> dict
```

返回建议统一结构：

```json
{
  "status": "ok|error",
  "message": "string",
  "data": {}
}
```

---

## 10. 第一版非目标

先明确不做这些，避免工程发散：

- 实时边弹边评
- 多用户支持
- Web 前端复杂可视化
- 高级踏板艺术性分析
- 音频和视频联合分析
- 任意片段自由重练自动识别

---

## 11. 推荐实现顺序

按这个顺序最稳：

1. `models`
2. `repositories`
3. `score_library_service`
4. `score_normalizer_service`
5. `midi_recording_service`
6. `midi_parsing_service`
7. `alignment_service`
8. `analysis_service`
9. `profile_service`
10. `piano_teacher_agent` 和 `feedback_service`
11. `workflows`
12. `main.py`

原因：

- 先把数据和落盘打稳
- 再把可计算链路接起来
- 最后再接 agent 和入口层

---

## 12. 下一步最值得补的内容

这份草图确认后，下一步建议直接产出两类东西：

1. `main.py` 和各 service 的空实现骨架
2. 第一版 `JSON Schema` 和示例数据文件

这样就可以开始真正搭工程，而不是继续停留在概念层。
