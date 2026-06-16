# 钢琴教师 Agent 设计稿

## 1. 目标

构建一个面向个人练琴场景的钢琴教师 agent，具备以下能力：

1. 读取指定目录中的钢琴曲谱。
2. 支持 `MusicXML` 作为主要谱面格式，`PDF` 作为导入入口。
3. 在用户发出“开始练习”指令时启动 MIDI 录制。
4. 练习结束后，根据录制的 MIDI 日志与 `MusicXML` 做对比分析。
5. 以“严谨、和蔼、具体”的教师口吻输出评价与练习建议。
6. 持续维护曲目与练习进度，给出下一步练习方向。

核心原则：

- **LLM 负责教学表达与策略生成**
- **工具链负责谱面解析、MIDI 对齐、统计评分**
- **长期记忆只保存结构化结果，不保存不稳定的自然语言判断**

---

## 2. 角色划分

### 2.1 主控 Agent

职责：

- 接收用户意图
- 路由到子 agent 或外部工具
- 维护练习会话状态
- 写入长期记录

### 2.2 钢琴教师 Agent

人格目标：

- 严谨
- 和蔼
- 具体
- 少空话，重方法

职责：

- 解释分析结果
- 判断当前练习重点
- 提供可执行的练习建议
- 生成阶段性总结

### 2.3 谱面处理工具层

职责：

- 读取指定目录
- 识别 `PDF` / `MusicXML`
- 必要时将 `PDF` 转换为 `MusicXML`
- 校验转换结果

### 2.4 演奏分析工具层

职责：

- 启动 / 停止 MIDI 录制
- 解析 MIDI 日志
- 将 MIDI 与 `MusicXML` 对齐
- 生成结构化评分与问题定位

### 2.5 进度管理层

职责：

- 记录每首曲目的练习历史
- 维护错误热点、小节级问题、速度区间、阶段标签
- 生成下一次练习建议的输入

---

## 3. 总体架构

建议采用四层结构：

1. **交互层**
   - Hermes 看板
   - 对话窗口
   - 练习会话状态展示

2. **编排层**
   - 主控 agent
   - 子 agent
   - 任务状态机

3. **工具层**
   - 曲谱读取
   - PDF 转 MusicXML
   - MIDI 录制
   - MIDI 对齐分析

4. **数据层**
   - 曲库索引
   - 练习会话记录
   - 曲目长期画像

推荐原则：

- 谱面与演奏数据都转成结构化数据再交给 LLM
- 不要让 LLM 直接“看原始 MIDI 就下结论”
- 不要把一次练习的结果完全写死到自然语言里

---

## 4. 用户交互流程

### 4.1 选曲

用户可以说：

- “开始练习”
- “开始练习《月光》”
- “帮我看一下最近在练哪首”

系统行为：

- 若未指定曲目，列出当前目录下可用曲目
- 若指定曲目，加载对应谱面与历史记录
- 若该曲目尚无 `MusicXML`，优先检查是否能从 `PDF` 转换

### 4.2 开始练习

用户指令触发后：

1. 检查曲目状态
2. 启动 MIDI 录制
3. 记录 session id、开始时间、谱面版本
4. 告知用户进入练习状态

### 4.3 结束练习

用户说：

- “练习结束”
- “停一下”
- “我弹完了”

系统行为：

1. 停止录制
2. 解析 MIDI log
3. 与 `MusicXML` 做对齐分析
4. 生成结构化结果
5. 交给钢琴教师 agent 生成反馈
6. 更新长期进度记录

### 4.4 练后反馈

输出建议控制在三个层次：

1. 总评
2. 主要问题
3. 下一步练法

建议避免一次输出过多问题。优先给最有训练价值的 2 到 3 项。

---

## 5. 数据模型

### 5.1 曲目记录 `PieceRecord`

字段建议：

- `piece_id`
- `title`
- `composer`
- `source_dir`
- `musicxml_path`
- `pdf_path`
- `arrangement_note`
- `converted_from_pdf`
- `last_practiced_at`
- `practice_count`
- `current_stage`
- `known_issues`

### 5.2 练习会话 `PracticeSession`

字段建议：

- `session_id`
- `piece_id`
- `started_at`
- `ended_at`
- `midi_log_path`
- `musicxml_snapshot_path`
- `tempo_target`
- `analysis_status`
- `analysis_summary`

### 5.3 结构化分析结果 `PracticeAnalysis`

字段建议：

- `overall_score`
- `pitch_accuracy`
- `rhythm_accuracy`
- `timing_stability`
- `tempo_stability`
- `missed_notes`
- `extra_notes`
- `problem_measures`
- `problem_hands`
- `repetition_points`
- `recommended_next_steps`

### 5.4 长期画像 `PieceProgressProfile`

字段建议：

- `piece_id`
- `best_stable_tempo`
- `worst_measures`
- `recent_issue_patterns`
- `stage_label`
- `next_goal`
- `last_feedback_digest`

---

## 6. 工具接口建议

### 6.1 曲谱扫描

输入：

- 指定目录路径

输出：

- 曲目清单
- 文件类型
- 是否存在 `MusicXML`
- 是否需要转换

### 6.2 PDF 转 MusicXML

输入：

- PDF 路径

输出：

- `MusicXML` 路径
- 转换状态
- 可能的警告

要求：

- 转换结果必须可被人工快速校验
- 若版面复杂或多声部识别不确定，应标记为“需确认”

### 6.3 MIDI 录制

输入：

- 目标曲目
- 会话 id

输出：

- MIDI log 文件
- 录制时间区间
- 采样状态

### 6.4 MIDI 对齐分析

输入：

- `MusicXML`
- MIDI log

输出：

- 小节级对齐结果
- 错音、漏音、重复音
- 节奏偏差
- 速度波动
- 问题片段定位

---

## 7. 评分策略

第一版建议只覆盖可稳定量化的指标：

- 音高命中率
- 节奏准确率
- 时值偏差
- 速度稳定性
- 停顿次数
- 漏音与错音分布

暂不作为第一版重点的内容：

- 音色
- 触键质量
- 情绪表达
- 高级踏板细节

原因很直接：

- MIDI 对这些维度的观测不充分
- 先把技术性反馈做稳，再逐步扩展

---

## 8. 练习状态机

建议状态如下：

1. `idle`
2. `piece_selected`
3. `recording`
4. `recording_stopped`
5. `analyzing`
6. `feedback_ready`
7. `profile_updated`

状态迁移示例：

- `idle` -> `piece_selected`：用户选曲
- `piece_selected` -> `recording`：开始练习
- `recording` -> `recording_stopped`：结束练习
- `recording_stopped` -> `analyzing`：开始分析
- `analyzing` -> `feedback_ready`：生成反馈
- `feedback_ready` -> `profile_updated`：更新长期画像
- `profile_updated` -> `idle`：等待下一次练习

---

## 9. 输出风格约束

钢琴教师 agent 的输出应满足：

- 先给结论，再给依据
- 问题要定位到具体小节或片段
- 建议要可执行，最好能直接照着练
- 避免泛泛而谈
- 每次只聚焦最重要的几个问题

示例结构：

1. 总评：这次整体节奏比上次稳，但右手在连接处仍有提前。
2. 主要问题：第 17 到 20 小节右手音型不均匀，左手低音有漏音。
3. 下一步：分手慢练，先把第 17 到 20 小节稳定到目标速度的 70%，连续三遍无错后再提速 4 bpm。

---

## 10. MVP 范围

第一版只做最小闭环：

1. 扫描指定目录曲谱
2. 识别 `PDF` 与 `MusicXML`
3. 支持 `PDF` 转 `MusicXML`
4. 开始 / 停止 MIDI 录制
5. 完成一次练后分析
6. 输出教师式反馈
7. 保存 session 与曲目进度

暂不做：

- 复杂排版校验
- 自动生成完整练习课表
- 多乐器支持
- 复杂踏板识别
- 视频或音频联合分析

---

## 11. 风险与对策

### 11.1 PDF 转换质量不稳定

对策：

- 以 `MusicXML` 为主
- 转换结果必须可视化预览
- 对复杂谱面保留人工确认入口

### 11.2 MIDI 无法代表全部演奏质量

对策：

- 第一版聚焦技术性评价
- 不承诺完整艺术表达分析

### 11.3 对齐失败或自由速度导致误判

对策：

- 使用容错对齐
- 支持片段级分析
- 允许用户标记“从某小节重新开始”

### 11.4 反馈过多导致练习目标不清

对策：

- 每次只输出 2 到 3 个重点
- 优先给出下一次可执行目标

---

## 12. 推荐实施顺序

1. 建立曲库扫描与索引
2. 接入 `MusicXML` 读取
3. 接入 MIDI 录制
4. 实现 MIDI 与谱面对齐
5. 生成结构化分析结果
6. 加入教师 agent 的反馈模板
7. 建立练习历史与长期画像
8. 再做 PDF 转换与人工校验增强

---

## 13. 结论

这个系统最关键的不是“让模型像老师一样说话”，而是把练琴过程拆成可记录、可分析、可追踪的结构化链路。只要谱面、录制、对齐、评分、反馈这五段链路稳定，钢琴教师 agent 就能真正变成一个长期可用的练习伙伴。
