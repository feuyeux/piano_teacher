# 钢琴教师 Agent 数据模型定义

## 1. 目标

定义第一版系统所需的核心数据模型，统一字段名、类型、状态值和落盘格式。所有结构默认可序列化为 `JSON`。

基本约束：

- 时间统一使用 ISO 8601 UTC 字符串
- 路径统一使用项目内相对路径
- 枚举值固定，避免自由文本污染
- 第一版优先保证稳定和可追溯，不追求字段最少

---

## 2. 通用约定

### 2.1 标识符规则

- `piece_id`: 曲目标识，建议使用稳定 slug，如 `beethoven-moonlight-mvt1`
- `session_id`: 练习会话标识，建议使用 `piece_id + timestamp`
- `score_revision_id`: 谱面版本标识，建议由文件 hash 或时间戳生成

### 2.2 通用状态值

`analysis_status`:

- `pending`
- `running`
- `completed`
- `failed`

`session_status`:

- `created`
- `recording`
- `stopped`
- `analyzing`
- `completed`
- `failed`

`score_source_type`:

- `musicxml`
- `pdf_converted`

`validation_status`:

- `valid`
- `warning`
- `invalid`

---

## 3. PieceRecord

用途：

- 描述一首曲目的主记录
- 由曲库扫描器维护

字段定义：

```json
{
  "piece_id": "string",
  "title": "string",
  "composer": "string|null",
  "aliases": ["string"],
  "source_dir": "string",
  "primary_musicxml_path": "string|null",
  "pdf_paths": ["string"],
  "musicxml_paths": ["string"],
  "score_source_type": "musicxml|pdf_converted|null",
  "score_revision_id": "string|null",
  "converted_from_pdf": "boolean",
  "conversion_status": "not_needed|pending|completed|failed",
  "validation_status": "valid|warning|invalid",
  "arrangement_note": "string|null",
  "difficulty_level": "beginner|intermediate|advanced|null",
  "measure_count": "number|null",
  "part_count": "number|null",
  "has_piano_hands_mapping": "boolean",
  "last_practiced_at": "string|null",
  "practice_count": "number",
  "current_stage": "new_piece|note_learning|rhythm_stabilizing|hands_together|tempo_building|musical_refining|maintenance",
  "known_issues": ["string"],
  "created_at": "string",
  "updated_at": "string"
}
```

约束：

- `primary_musicxml_path` 为后续分析默认入口
- `musicxml_paths` 支持多版本谱面
- `known_issues` 只记录短标签，不记录长段自然语言

---

## 4. PracticeSession

用途：

- 描述一次具体练习
- 是录制、分析、反馈、画像更新的主索引

字段定义：

```json
{
  "session_id": "string",
  "piece_id": "string",
  "session_status": "created|recording|stopped|analyzing|completed|failed",
  "started_at": "string",
  "ended_at": "string|null",
  "score_revision_id": "string|null",
  "musicxml_snapshot_path": "string|null",
  "normalized_score_path": "string|null",
  "midi_input_device": "string|null",
  "midi_log_path": "string|null",
  "raw_event_count": "number",
  "tempo_target_bpm": "number|null",
  "practice_mode": "full_run|section_loop|free_play",
  "section_start_measure": "number|null",
  "section_end_measure": "number|null",
  "user_command": "string|null",
  "analysis_status": "pending|running|completed|failed",
  "analysis_path": "string|null",
  "analysis_summary": "string|null",
  "error_message": "string|null",
  "created_at": "string",
  "updated_at": "string"
}
```

约束：

- `musicxml_snapshot_path` 用于锁定本次分析使用的谱面版本
- `practice_mode` 为后续支持局部练习预留
- `analysis_summary` 只放简短摘要，不替代完整报告

---

## 5. PracticeAnalysis

用途：

- 保存工具层输出的结构化分析结果
- 是教师 agent 的主要输入

字段定义：

```json
{
  "analysis_id": "string",
  "session_id": "string",
  "piece_id": "string",
  "generated_at": "string",
  "analysis_version": "string",
  "alignment_status": "completed|partial|failed",
  "aligned_note_count": "number",
  "expected_note_count": "number",
  "performed_note_count": "number",
  "overall_score": "number|null",
  "pitch_accuracy": "number|null",
  "rhythm_accuracy": "number|null",
  "timing_stability": "number|null",
  "tempo_stability": "number|null",
  "missed_notes_count": "number",
  "extra_notes_count": "number",
  "repeated_note_count": "number",
  "pedal_event_count": "number|null",
  "estimated_tempo_bpm": "number|null",
  "best_measure_range": ["number", "number"],
  "worst_measure_range": ["number", "number"],
  "problem_measures": [
    {
      "measure_number": "number",
      "severity": "low|medium|high",
      "issue_tags": ["pitch", "rhythm", "timing", "pause", "extra_note", "missed_note"],
      "left_hand_issue_count": "number",
      "right_hand_issue_count": "number",
      "notes": "string|null"
    }
  ],
  "problem_hands": {
    "left": {
      "issue_count": "number",
      "dominant_tags": ["string"]
    },
    "right": {
      "issue_count": "number",
      "dominant_tags": ["string"]
    }
  },
  "issue_summary_tags": ["string"],
  "recommended_focus_measures": ["number"],
  "recommended_next_steps": ["string"],
  "warnings": ["string"]
}
```

评分范围建议：

- `overall_score`: `0-100`
- `pitch_accuracy`: `0-1`
- `rhythm_accuracy`: `0-1`
- `timing_stability`: `0-1`
- `tempo_stability`: `0-1`

约束：

- 第一版所有评分都必须能由确定性算法复算
- `recommended_next_steps` 可以先由规则生成，后续再交给教师 agent润色

---

## 6. PieceProgressProfile

用途：

- 聚合某首曲子的长期练习状态
- 为教师 agent 提供持续教学上下文

字段定义：

```json
{
  "piece_id": "string",
  "stage_label": "new_piece|note_learning|rhythm_stabilizing|hands_together|tempo_building|musical_refining|maintenance",
  "practice_count": "number",
  "total_practice_minutes": "number",
  "last_practiced_at": "string|null",
  "best_stable_tempo_bpm": "number|null",
  "latest_tempo_bpm": "number|null",
  "recent_issue_patterns": ["string"],
  "worst_measures": ["number"],
  "improving_measures": ["number"],
  "plateau_measures": ["number"],
  "last_three_scores": ["number"],
  "current_goal": "string|null",
  "next_goal": "string|null",
  "last_feedback_digest": "string|null",
  "teacher_focus_tags": ["string"],
  "updated_at": "string"
}
```

约束：

- `recent_issue_patterns` 使用短标签，如 `right_hand_rhythm_unstable`
- `last_feedback_digest` 控制在一两句话，避免长期积累过多自然语言噪声

---

## 7. NormalizedScore

用途：

- 作为 `MusicXML` 解析后的内部标准谱面格式
- MIDI 对齐只依赖该格式，不直接依赖原始 XML

字段定义：

```json
{
  "piece_id": "string",
  "score_revision_id": "string",
  "title": "string",
  "composer": "string|null",
  "time_signature": "string|null",
  "key_signature": "string|null",
  "default_tempo_bpm": "number|null",
  "division_unit": "number",
  "measure_count": "number",
  "measures": [
    {
      "measure_number": "number",
      "beats": "number|null",
      "beat_unit": "number|null",
      "notes": [
        {
          "note_id": "string",
          "pitch_midi": "number|null",
          "pitch_name": "string|null",
          "voice": "number|null",
          "staff": "1|2|null",
          "hand": "left|right|unknown",
          "is_rest": "boolean",
          "onset_division": "number",
          "duration_division": "number",
          "tie_start": "boolean",
          "tie_stop": "boolean",
          "chord_index": "number|null"
        }
      ]
    }
  ],
  "created_at": "string"
}
```

约束：

- `staff` 和 `hand` 尽量都保留，避免后续只靠其中一个字段
- `pitch_midi` 对休止符为空

---

## 8. 文件落盘建议

建议路径：

- `scores/piece_index.json`
- `scores/<piece_id>/normalized_score.json`
- `sessions/<session_id>/session.json`
- `sessions/<session_id>/analysis.json`
- `profiles/<piece_id>.json`

文件职责：

- `session.json` 记录生命周期和路径引用
- `analysis.json` 记录一次完整分析
- `profile.json` 只保存该曲的聚合状态

---

## 9. 第一版最小必需字段

如果要快速起步，下面字段不能省：

- `PieceRecord.piece_id`
- `PieceRecord.primary_musicxml_path`
- `PracticeSession.session_id`
- `PracticeSession.piece_id`
- `PracticeSession.midi_log_path`
- `PracticeSession.session_status`
- `PracticeAnalysis.session_id`
- `PracticeAnalysis.overall_score`
- `PracticeAnalysis.problem_measures`
- `PieceProgressProfile.piece_id`
- `PieceProgressProfile.stage_label`
- `PieceProgressProfile.next_goal`

---

## 10. 变更原则

后续扩展字段时遵循以下规则：

1. 新字段优先追加，不改旧字段语义
2. 枚举值新增前先检查上游兼容性
3. 教师 agent 输入字段保持小而稳
4. 工具层产生的明细数据可以丰富，但传给 LLM 的摘要要克制
