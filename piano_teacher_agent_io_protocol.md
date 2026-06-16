# 钢琴教师 Agent 输入输出协议

## 1. 目标

定义教师 agent 的输入边界、输出格式、风格约束和失败处理。目标是让教师 agent 只做教学解释和练习建议，不承担底层计算。

核心原则：

- 输入必须结构化
- 输出必须稳定
- 建议必须可执行
- 一次只聚焦少数关键问题

---

## 2. 教师 Agent 职责边界

教师 agent 负责：

- 解读本次练习分析结果
- 结合历史进度判断当前重点
- 输出总评、问题定位、下一步练法
- 控制反馈语气和教学节奏

教师 agent 不负责：

- 直接读取原始 MIDI
- 直接解析 `MusicXML`
- 自行计算分数
- 生成和底层分析冲突的事实判断

---

## 3. 输入协议

### 3.1 最小输入对象

```json
{
  "piece": {
    "piece_id": "string",
    "title": "string",
    "composer": "string|null",
    "current_stage": "string"
  },
  "session": {
    "session_id": "string",
    "practice_mode": "full_run|section_loop|free_play",
    "tempo_target_bpm": "number|null"
  },
  "analysis": {
    "overall_score": "number|null",
    "pitch_accuracy": "number|null",
    "rhythm_accuracy": "number|null",
    "timing_stability": "number|null",
    "tempo_stability": "number|null",
    "problem_measures": [
      {
        "measure_number": "number",
        "severity": "low|medium|high",
        "issue_tags": ["string"],
        "left_hand_issue_count": "number",
        "right_hand_issue_count": "number"
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
    "recommended_focus_measures": ["number"],
    "recommended_next_steps": ["string"],
    "warnings": ["string"]
  },
  "profile": {
    "practice_count": "number",
    "best_stable_tempo_bpm": "number|null",
    "recent_issue_patterns": ["string"],
    "worst_measures": ["number"],
    "current_goal": "string|null",
    "next_goal": "string|null",
    "last_feedback_digest": "string|null"
  }
}
```

### 3.2 输入约束

- 不直接传原始 MIDI 文件内容
- 不直接传完整 `MusicXML`
- `problem_measures` 最多传前 8 个
- `recommended_next_steps` 来自规则层，可作为建议草案

---

## 4. 输出协议

### 4.1 标准输出对象

```json
{
  "summary": "string",
  "key_issues": [
    {
      "title": "string",
      "measure_range": "string",
      "description": "string"
    }
  ],
  "practice_plan": [
    {
      "step": "string",
      "target": "string"
    }
  ],
  "progress_note": "string|null",
  "next_focus": "string|null",
  "confidence": "high|medium|low"
}
```

### 4.2 字段语义

- `summary`: 一两句总评，先讲结论
- `key_issues`: 最多 3 项，必须能定位到小节或片段
- `practice_plan`: 最多 3 步，必须是可直接执行的练法
- `progress_note`: 对比历史的短评价
- `next_focus`: 下次练习的唯一主目标
- `confidence`: 当分析存在告警时降低置信度

---

## 5. 语言风格约束

教师 agent 输出必须满足：

- 严谨
- 和蔼
- 具体
- 不夸张
- 不说空话

表达规则：

- 先说本次最重要的结论
- 用“小节 + 手 + 问题类型”定位问题
- 每条建议尽量带动作和条件
- 尽量避免模糊词，如“还行”“不错”“感觉上”

推荐表达：

- “第 17 到 20 小节右手节奏提前。”
- “左手低音在第 32 小节有连续漏音。”
- “先分手慢练到 60 bpm，连续三遍无错后再提速 4 bpm。”

不推荐表达：

- “整体挺好的。”
- “这一段再多练练。”
- “音乐性还可以再提升。”

---

## 6. 生成规则

### 6.1 总评生成规则

优先顺序：

1. 是否比上次更稳定
2. 本次最突出的问题类别
3. 当前阶段是否匹配当前表现

### 6.2 问题筛选规则

最多保留 3 项，优先级如下：

1. 高频且严重的小节问题
2. 直接阻碍继续提速的问题
3. 与当前阶段目标最相关的问题

### 6.3 练法生成规则

每条建议应包含：

- 练习对象
- 练习方式
- 速度或重复次数
- 进阶条件

标准模板：

`先对 <小节范围> 做 <分手/慢练/循环>，在 <速度或次数> 条件下完成，再进入下一步。`

---

## 7. 失败与降级处理

### 7.1 当分析结果存在警告

若 `warnings` 非空：

- 不输出过强结论
- `confidence` 至少降为 `medium`
- 明确说明这次评价更适合作为参考

### 7.2 当对齐为部分成功

应输出：

- 可确认的问题
- 无法可靠确认的部分不做判断

示例策略：

- 可以说“前半段节奏偏差较明显”
- 不要说“整首曲子的连贯性很差”，除非数据支持

### 7.3 当历史数据缺失

若没有 `profile` 或历史次数过少：

- 不生成趋势判断
- `progress_note` 可为空

---

## 8. Prompt 组装建议

系统层提示应固定两件事：

1. 你是严谨和蔼的钢琴教师
2. 你只能基于提供的数据做判断，不能补造事实

运行时输入应只包含：

- 曲目摘要
- 本次分析摘要
- 历史摘要
- 输出格式要求

不建议把：

- 全量 session 历史
- 完整中间对齐明细
- 大段原始工具日志

直接送进教师 agent。

---

## 9. 输出示例

```json
{
  "summary": "这次整体比上次更稳，主要问题集中在第 17 到 20 小节右手节奏提前，以及第 32 小节左手低音漏音。",
  "key_issues": [
    {
      "title": "右手节奏提前",
      "measure_range": "17-20",
      "description": "右手音型进入点偏早，导致和左手对位不齐。"
    },
    {
      "title": "左手低音漏音",
      "measure_range": "32",
      "description": "左手低音支撑不稳定，和声骨架被削弱。"
    }
  ],
  "practice_plan": [
    {
      "step": "第 17 到 20 小节分手慢练",
      "target": "从 60 bpm 开始，连续三遍无明显提前后再提速 4 bpm。"
    },
    {
      "step": "第 32 小节左手单独循环",
      "target": "每次循环 5 遍，确保低音全部落下后再合手。"
    }
  ],
  "progress_note": "和上次相比，整体节奏稳定性有提升。",
  "next_focus": "先把第 17 到 20 小节的左右手对齐做稳。",
  "confidence": "high"
}
```

---

## 10. 第一版验收标准

满足以下条件即可认为教师 agent 协议可进入实现：

1. 输入字段足以支持稳定反馈
2. 输出结构固定，不依赖自由长文
3. 每次反馈最多聚焦 3 个问题
4. 建议都能直接转成下一轮练习动作
