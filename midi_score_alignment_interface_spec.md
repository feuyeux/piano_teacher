# MIDI 与谱面对齐接口定义

## 1. 目标

定义 MIDI 解析、标准谱面读取、对齐分析、评分输出之间的接口边界。目标是让工具层可独立实现和替换，且教师 agent 只消费稳定的结构化结果。

第一版范围限制：

- 单首曲目
- 单次会话
- 顺序演奏
- 不处理复杂反复记号
- 不要求支持任意跳段重练

---

## 2. 模块边界

建议拆成四个模块：

1. `score_loader`
   - 读取 `normalized_score.json`
2. `midi_parser`
   - 读取 MIDI log，输出标准事件流
3. `aligner`
   - 将演奏事件与谱面音符对齐
4. `analyzer`
   - 聚合问题并输出评分报告

核心原则：

- `aligner` 不负责写教学文案
- `analyzer` 不依赖大模型
- 所有中间结果尽量可落盘调试

---

## 3. 输入输出总览

### 3.1 Score Loader 输入

```json
{
  "normalized_score_path": "scores/<piece_id>/normalized_score.json"
}
```

### 3.2 Score Loader 输出

```json
{
  "piece_id": "string",
  "score_revision_id": "string",
  "measure_count": "number",
  "notes": [
    {
      "note_id": "string",
      "measure_number": "number",
      "hand": "left|right|unknown",
      "pitch_midi": "number|null",
      "onset_division": "number",
      "duration_division": "number",
      "is_rest": "boolean"
    }
  ]
}
```

### 3.3 MIDI Parser 输入

```json
{
  "midi_log_path": "sessions/<session_id>/performance.mid"
}
```

### 3.4 MIDI Parser 输出

```json
{
  "session_id": "string",
  "ticks_per_beat": "number|null",
  "events": [
    {
      "event_id": "string",
      "type": "note|pedal",
      "pitch_midi": "number|null",
      "velocity": "number|null",
      "start_ms": "number",
      "end_ms": "number|null",
      "channel": "number|null"
    }
  ]
}
```

### 3.5 Aligner 输入

```json
{
  "score": "ScoreLoaderOutput",
  "performance": "MidiParserOutput",
  "options": {
    "timing_tolerance_ms": 180,
    "pitch_match_mode": "strict",
    "allow_partial_alignment": true
  }
}
```

### 3.6 Aligner 输出

```json
{
  "alignment_status": "completed|partial|failed",
  "note_matches": [
    {
      "score_note_id": "string",
      "event_id": "string|null",
      "measure_number": "number",
      "hand": "left|right|unknown",
      "expected_pitch_midi": "number|null",
      "performed_pitch_midi": "number|null",
      "timing_offset_ms": "number|null",
      "duration_offset_ms": "number|null",
      "match_type": "matched|missed|extra|pitch_error|timing_error"
    }
  ],
  "extra_events": ["string"],
  "warnings": ["string"]
}
```

### 3.7 Analyzer 输入

```json
{
  "alignment": "AlignerOutput",
  "score": "ScoreLoaderOutput",
  "performance": "MidiParserOutput"
}
```

### 3.8 Analyzer 输出

输出应符合 `PracticeAnalysis`。

---

## 4. 标准中间结构

### 4.1 PerformedNote

用于 MIDI 解析后的音符事件。

```json
{
  "event_id": "string",
  "pitch_midi": "number",
  "velocity": "number",
  "start_ms": "number",
  "end_ms": "number",
  "duration_ms": "number",
  "channel": "number|null"
}
```

### 4.2 ScoreNote

用于对齐的标准谱面音符。

```json
{
  "note_id": "string",
  "measure_number": "number",
  "hand": "left|right|unknown",
  "pitch_midi": "number|null",
  "onset_division": "number",
  "duration_division": "number",
  "is_rest": "boolean"
}
```

### 4.3 NoteMatch

用于记录单个谱面音符与演奏音符的对应关系。

```json
{
  "score_note_id": "string",
  "event_id": "string|null",
  "measure_number": "number",
  "match_type": "matched|missed|extra|pitch_error|timing_error",
  "expected_pitch_midi": "number|null",
  "performed_pitch_midi": "number|null",
  "timing_offset_ms": "number|null",
  "duration_offset_ms": "number|null",
  "hand": "left|right|unknown"
}
```

---

## 5. 对齐流程建议

### 5.1 第一版推荐流程

1. 读取 `NormalizedScore`
2. 将可演奏音符线性展开
3. 解析 MIDI 为 `PerformedNote` 列表
4. 去除明显无效事件
5. 按时间顺序做基础匹配
6. 输出逐音符匹配结果
7. 聚合到小节级错误

### 5.2 第一版不处理的问题

- 自由回放段落识别
- 任意从中间小节开始的非显式局部练习
- 装饰音与复杂连音的高级建模
- 踏板与旋律层次的艺术性评价

---

## 6. 对齐规则

### 6.1 音高匹配

规则：

- 默认严格按 `pitch_midi` 匹配
- 若谱面是和弦，允许同一拍内相邻事件窗口内匹配多个音

### 6.2 时值与节奏匹配

规则：

- `timing_offset_ms` 用于衡量实际起音与期望起音的偏差
- `duration_offset_ms` 用于衡量实际时值偏差
- 第一版节奏准确率主要基于起音偏差而不是完整乐句形态

### 6.3 漏音定义

规则：

- 谱面音符在窗口内找不到可接受的事件，则标记为 `missed`

### 6.4 额外音定义

规则：

- 演奏事件未被任何谱面音符吸收，则标记为 `extra`

### 6.5 错音定义

规则：

- 时间位置接近，但 `pitch_midi` 不一致，可标记为 `pitch_error`

---

## 7. 配置项建议

```json
{
  "timing_tolerance_ms": 180,
  "duration_tolerance_ratio": 0.35,
  "chord_spread_tolerance_ms": 90,
  "min_note_duration_ms": 30,
  "partial_alignment_min_ratio": 0.6
}
```

说明：

- `timing_tolerance_ms`: 起音容差
- `duration_tolerance_ratio`: 时值偏差允许比例
- `chord_spread_tolerance_ms`: 和弦内滚奏容差
- `min_note_duration_ms`: 过滤误触
- `partial_alignment_min_ratio`: 最低可接受部分对齐比例

---

## 8. 小节级聚合接口

### 8.1 输入

`NoteMatch[]`

### 8.2 输出

```json
{
  "measure_summaries": [
    {
      "measure_number": "number",
      "issue_count": "number",
      "severity": "low|medium|high",
      "issue_tags": ["pitch", "rhythm", "timing", "pause", "extra_note", "missed_note"],
      "left_hand_issue_count": "number",
      "right_hand_issue_count": "number",
      "avg_timing_offset_ms": "number|null"
    }
  ],
  "worst_measure_numbers": ["number"],
  "issue_summary_tags": ["string"]
}
```

用途：

- 供评分器计算总结果
- 供教师 agent 定位重点片段

---

## 9. 评分接口

### 9.1 输入

```json
{
  "measure_summaries": "MeasureSummary[]",
  "note_matches": "NoteMatch[]",
  "performance_stats": {
    "performed_note_count": "number",
    "estimated_tempo_bpm": "number|null",
    "pause_count": "number"
  }
}
```

### 9.2 输出

```json
{
  "overall_score": "number",
  "pitch_accuracy": "number",
  "rhythm_accuracy": "number",
  "timing_stability": "number",
  "tempo_stability": "number",
  "missed_notes_count": "number",
  "extra_notes_count": "number",
  "repeated_note_count": "number"
}
```

要求：

- 分数算法可复算
- 分数变化对用户可解释

---

## 10. 错误处理约定

### 10.1 Parser 失败

返回：

```json
{
  "status": "failed",
  "error_code": "midi_parse_failed",
  "message": "string"
}
```

### 10.2 Score 无效

返回：

```json
{
  "status": "failed",
  "error_code": "invalid_normalized_score",
  "message": "string"
}
```

### 10.3 对齐质量不足

返回：

```json
{
  "alignment_status": "partial",
  "warnings": ["low_alignment_ratio"]
}
```

原则：

- 第一版允许部分成功
- 只要能明确指出不可靠，就不要硬给高置信评价

---

## 11. 调试文件建议

建议额外落盘三个中间文件：

- `parsed_midi.json`
- `alignment_debug.json`
- `measure_summary.json`

原因：

- 这是后续排查对齐问题最直接的证据链
- 比只看最终评分更容易定位算法问题

---

## 12. 第一版验收标准

满足以下条件即可认为接口定义可进入实现：

1. 能从 `normalized_score.json` 读取标准音符序列
2. 能从 MIDI log 读取标准事件流
3. 能输出逐音符对齐结果
4. 能聚合出小节级问题
5. 能稳定生成 `PracticeAnalysis`
