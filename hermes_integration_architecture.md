# 钢琴教师 Agent — Hermes 集成架构分析

## 一、子 Agent 划分

子 Agent 的特征是：**需要自主判断、维护内部状态、可能调用多个工具**，且具有独立人格或决策逻辑。

| 子 Agent | 职责 | 依据 |
|---|---|---|
| **Conductor Agent（主控 Agent）** | 接收用户意图 → 路由到对应 workflow → 调度工具/子 agent → 维护练习状态机 | 设计稿 §2.1：主控 agent 负责意图路由、会话状态维护、写入长期记录 |
| **Piano Teacher Agent（钢琴教师 Agent）** | 接收结构化分析结果 + 历史画像 → 生成教学反馈（总评/问题/练法） | 设计稿 §2.2：独立人格，只做教学解释与建议生成；IO 协议单独定义 |

**为什么其他模块不做成子 agent？**

- 谱面处理、MIDI 对齐、评分等都是**确定性的计算链路**，不需要 LLM 自主判断
- 文档核心原则明确：「LLM 负责教学表达与策略生成，工具链负责谱面解析、MIDI 对齐、统计评分」
- 教师 agent 不负责直接读取原始 MIDI / MusicXML / 自行计算分数

---

## 二、工具（Tool）划分

工具的特征是：**输入输出明确、逻辑确定性、可独立替换**。

| 工具 | 对应 Service / 底层封装 | 说明 |
|---|---|---|
| **`scan_library`** | ScoreLibraryService | 扫描曲库目录，生成 PieceRecord 索引 |
| **`normalize_score`** | ScoreNormalizerService | MusicXML → NormalizedScore 标准化 |
| **`convert_pdf`** | PdfConversionService | PDF → MusicXML，调用外部工具 |
| **`start_recording`** | MidiRecordingService | 启动 MIDI 录制 |
| **`stop_recording`** | MidiRecordingService | 停止 MIDI 录制 |
| **`parse_midi`** | MidiParsingService | MIDI log → 标准事件流（PerformedNote[]） |
| **`load_score`** | ScoreLoader | 读取 NormalizedScore 供对齐用 |
| **`align`** | AlignmentService | 谱面 vs MIDI 对齐，输出 NoteMatch[] |
| **`analyze`** | AnalysisService | 聚合 NoteMatch → PracticeAnalysis 评分报告 |
| **`update_profile`** | ProfileService | 更新 PieceProgressProfile |
| **`get_profile`** | ProfileService | 读取曲目长期画像 |
| **`save_session` / `load_session`** | SessionRepository | 练习会话的持久化 |
| **`save_piece` / `get_piece`** | PieceRepository | 曲目记录的持久化 |

---

## 三、Skill 划分

Skill 的特征是：**复合操作流程、需要知道「怎么做」的知识**，但核心逻辑通过编排工具完成，本身不需要独立决策。

| Skill | 编排的工具 | 说明 |
|---|---|---|
| **`start_practice`** | scan_library → normalize_score → save_session → start_recording | 开始练习 workflow 的完整编排 |
| **`finish_practice`** | stop_recording → parse_midi → load_score → align → analyze → save_session → update_profile | 结束练习 workflow 的完整编排 |
| **`review_session`** | load_session → get_profile → (调用 Teacher Agent) | 查看最近一次练习反馈 |
| **`show_progress`** | get_profile → (调用 Teacher Agent) | 查看曲目长期进度 |
| **`refresh_library`** | scan_library | 刷新曲库索引 |

Skill 和 Workflow 的关系：文档中的 **workflow 层**（`start_practice_workflow`、`finish_practice_workflow` 等）天然对应 Hermes 的 Skill——它们串联多个工具完成一个完整用户意图。

---

## 四、整体处理流程

```
用户指令
  │
  ▼
┌─────────────────────────────┐
│  Conductor Agent（主控）      │  意图识别 + 状态机管理
│  路由到对应 Skill            │
└──────────┬──────────────────┘
           │
     ┌─────┼─────┬──────────┬──────────────┐
     ▼     ▼     ▼          ▼              ▼
  start   finish  review   show         refresh
 practice practice session  progress    library
 (Skill)  (Skill) (Skill)  (Skill)     (Skill)
     │     │
     │     │  ┌─── finish_practice 详细流程 ───┐
     │     │  │ stop_recording                   │
     │     │  │ parse_midi                       │
     │     │  │ load_score                       │
     │     │  │ align                            │
     │     │  │ analyze → PracticeAnalysis       │
     │     │  │ update_profile                   │
     │     │  │ ┌─────────────────────────┐      │
     │     │  │ │ Piano Teacher Agent      │      │
     │     │  │ │ (子 Agent)               │      │
     │     │  │ │ 输入: analysis+profile   │      │
     │     │  │ │ 输出: 教学反馈 JSON      │      │
     │     │  │ └─────────────────────────┘      │
     │     │  └──────────────────────────────────┘
     │
     │  ┌─── start_practice 详细流程 ───┐
     │  │ scan_library / get_piece       │
     │  │ normalize_score (如需要)       │
     │  │ convert_pdf (如需要)           │
     │  │ save_session                   │
     │  │ start_recording                │
     │  └────────────────────────────────┘
```

### 关键状态机流转

```
idle → piece_selected → recording → recording_stopped → analyzing → feedback_ready → profile_updated → idle
```

### 数据流向

1. **谱面链路**：`scores/` → scan_library → PieceRecord → normalize_score → NormalizedScore（供对齐消费）
2. **录制链路**：用户触发 → start_recording → MIDI log → stop_recording
3. **分析链路**：MIDI log + NormalizedScore → parse_midi → align → analyze → PracticeAnalysis
4. **反馈链路**：PracticeAnalysis + PieceProgressProfile → **Piano Teacher Agent** → 结构化教学反馈
5. **画像链路**：PracticeAnalysis → update_profile → PieceProgressProfile（供下次反馈用）

---

## 五、总结

| 分类 | 组件 | 数量 |
|---|---|---|
| **子 Agent** | Conductor Agent、Piano Teacher Agent | 2 |
| **工具** | scan_library, normalize_score, convert_pdf, start/stop_recording, parse_midi, load_score, align, analyze, update/get_profile, save/load_session, save/get_piece | ~13 |
| **Skill** | start_practice, finish_practice, review_session, show_progress, refresh_library | 5 |

核心设计原则始终是文档反复强调的：**工具层做确定性计算，LLM 只做教学表达**。Conductor Agent 做调度，Piano Teacher Agent 做教学，中间链路全部是工具。
