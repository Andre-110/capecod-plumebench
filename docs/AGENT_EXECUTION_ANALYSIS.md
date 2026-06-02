# CapeCod-PlumeBench Agent 执行过程问题分析

## 1. 本次观察对象

Run ID:

```text
capecod-agent-hardv2-001
```

任务版本：

```text
CapeCod-PlumeBench hard-v2
```

当前观察窗口：

```text
120 分钟（完整 2h run）
```

当前最高分：

```text
10.898 / 100
```

当前轨迹摘要：

```text
agent-1   6.499
auto-1    6.499
agent-2   8.828
auto-2    7.120
agent-10  9.796
agent-28 10.142
agent-54 10.553
agent-72 10.857
agent-83 10.811
agent-85 10.872
agent-114 10.898
auto-24 10.898
```

阶段判断：

```text
30min 内最高分：10.013 / 100
60min 内最高分：10.553 / 100
90min 内最高分：10.872 / 100
120min 内最高分：10.898 / 100
```

这说明 hard-v2 已经显著压住了短时间冲分，并且满足 2h 仍低于 30 的验收上限；但也暴露出一个设计问题：Agent 有学习行为，但提升幅度很小，没有进入 15-30 分的中等区间。

## 2. Agent 实际做了什么

从 `agent_output.txt` 看，Agent 没有停留在 baseline，而是做了比较典型的科研建模尝试：

1. 读取公开数据和 starter 代码。
2. 提交 baseline，确认初始得分。
3. 分析 `public_wells.csv`、`public_observations.csv`、`prediction_requests.csv`、`public_site_config.json`。
4. 用公开观测数据估计 plume centerline、depth axis、transport coordinate。
5. 写 public rolling validation 脚本，在 public 年份上调参。
6. 用 transport-coordinate interpolation 替换全局中位数 baseline。
7. 改写 `model.py`，实现：
   - censored value 处理；
   - analyte-specific 背景、peak、decay、retardation；
   - source-year / transport-coordinate 距离；
   - plume centerline 和 depth axis；
   - IDW / kernel smoothing；
   - metric grid 估计 plume front、centerline、mass proxy。
8. 改写 `monitoring_plan.py`，实现：
   - candidate 未来浓度预测；
   - threshold proximity；
   - plume front / margin coverage；
   - existing-well gap；
   - budgeted greedy selection；
   - spatial diversity。
9. 多次提交并根据 aggregate score 试参数。

这些行为说明 Agent 在做有效工作，不是无效空跑。

## 3. Agent 卡住的主要原因

### 3.1 只能看到 aggregate feedback，无法定位分项短板

hard-v2 当前只返回：

```text
CASE aggregate OK score=...
TOTAL_SCORE ...
```

Agent 无法知道自己是：

- hidden concentration prediction 差；
- risk classification 差；
- plume metrics 差；
- monitoring plan 差；
- report/format 差。

从行为看，它只能用黑盒分数做 hill-climb。由于每轮分数变化很小，Agent 很快陷入局部调参。

这是 hard-v2 压分成功的关键机制，但也会降低“可学习性”。如果验收要求“2h 有一些提升”，完全 aggregate feedback 可能过硬。

### 3.2 Public validation 与 hidden scoring 分布差异过大

Agent 主要依据 public 数据构造模型。它能通过 public rolling validation 找到一套合理的 transport-coordinate predictor，但 hidden 中存在：

- 更远未来年份；
- future plume acceleration；
- lateral drift；
- analyte-specific rebound；
- localized hidden anomalies；
- 更陡的评分函数。

这些 hidden 机制没有充分 public signal 暗示。Agent 能学到公开数据的平滑趋势，但学不到 hidden 局部异常，因此分数停在 10 左右。

这说明当前题目“防快速冲分”做得很好，但“可学习提升”偏弱。

### 3.3 评分函数非常陡，普通改进无法转化成明显得分

hard-v2 的核心分集中在：

```text
hidden concentration prediction: 45
threshold risk classification: 20
plume metrics: 26
```

且 prediction / metrics 的评分曲线比较陡。Agent 的平滑外推模型能改善一些趋势，但只要没有猜中 hidden anomaly，核心分提升有限。

结果是：

```text
baseline 6.499
public-informed model 10-11
```

中间缺少一个自然的 15-25 分台阶。

### 3.4 Agent 过度优化公开数据与启发式特征

日志显示 Agent 反复做 public rolling validation，例如训练到某一年、预测后续公开年份。这个策略在真实任务中合理，但在当前 hidden 设计下收益有限。

问题是 public 后验不足以识别 hidden 的 future drift/anomaly。Agent 会持续优化：

- plume centerline；
- source-year；
- IDW kernel；
- grid mass scale；
- monitoring candidate score。

但这些优化对 hidden 只有小幅收益，最终在 10.8 左右平台化。

### 3.5 输出要求没有强制不确定性建模

题面鼓励 uncertainty-aware monitoring，但当前必须输出主要还是：

```text
predictions.csv
plume_metrics.json
monitoring_plan.json
```

没有强制提交：

- prediction uncertainty；
- posterior samples；
- scenario ensemble；
- calibration diagnostics；
- model class evidence；
- out-of-distribution risk estimate。

因此 Agent 自然选择 deterministic smoother，而不是做多情景鲁棒预测。对于地下水这类不确定性强的任务，这会限制中高分能力区分。

## 4. 这次执行暴露出的题目设计问题

### 问题 A：当前 hard-v2 对 30min 标准很好，但对 2h 标准可能太硬

验收标准是：

```text
30min < 15
2h 有一些提升但 < 30
```

当前表现：

```text
30min best ≈ 10.013
60min best ≈ 10.553
90min best ≈ 10.872
120min best ≈ 10.898
```

实测满足“不超过 30”，但“有一些提升”偏弱。2h 从 starter baseline 的 6.499 提高到 10.898，绝对提升约 4.399 分，仍未形成 15-30 分的中间能力层。

如果验收方希望看到明显学习曲线，当前 hard-v2 需要增加可学习中间层。

### 问题 B：hidden anomaly 需要更可解释

如果 hidden anomaly 完全没有 public 线索，会被质疑为“不可学”。更合理的方式是：

- public config 明确说明存在 aquifer heterogeneity / local recharge / preferential pathway；
- public observations 中给出弱信号；
- hidden 只改变强度和位置，而不是凭空出现；
- 评分报告说明 hidden 是真实 groundwater 中常见的不确定性，而不是随机造点。

### 问题 C：反馈粒度可能需要分阶段

完全 aggregate 可以防冲分，但会削弱 2h 学习。可以考虑：

- 30min 以前只给 aggregate；
- 30min 后给 coarse category feedback；
- 或每次只给一个粗分箱：

```text
prediction_quality: low / medium / high
metric_quality: low / medium / high
plan_quality: low / medium / high
```

不暴露具体子分，但给 Agent 一点方向。

### 问题 D：当前 monitoring plan 分数太小

Monitoring plan 只有 6 分，而且 hidden utility 不可见。Agent 现在能从 3.265 附近涨到一些，但总体不影响总分。

如果希望考察地下水工程决策，而不是只考浓度预测，应提高 monitoring 的影响，但要避免简单规则拿高分。

建议：

```text
prediction: 40
risk: 18
metrics: 20
monitoring: 15
format/report: 7
```

同时 monitoring 要依赖 uncertainty coverage，而不是只依赖 predicted concentration。

## 5. 后续如何制定评判标准

建议分成四档，而不是只看总分。

### 0-10 分：格式和弱 baseline

特征：

- 能生成 required outputs；
- 不崩溃；
- 使用历史均值、简单 IDW 或 naive trend；
- 对 hidden future/risk 几乎没有预测能力。

当前 starter baseline：

```text
6.499 / 100
```

### 10-15 分：公开数据平滑建模

特征：

- 能读 public data；
- 能做 centerline / depth / source-year / IDW；
- 能改善 public rolling validation；
- 对 hidden anomaly 和 future drift 仍无能为力。

当前 Agent：

```text
10.898 / 100
```

### 15-30 分：可学习的鲁棒地下水模型

应该要求：

- 显式建立 scenario ensemble；
- 对未来年份做不确定性扩展；
- 对风险阈值做 calibration；
- monitoring plan 体现 uncertainty coverage；
- plume metrics 不只是从预测均值网格读 front。

2h 合格提升目标应落在这个区间：

```text
15-30 / 100
```

### 30 分以上：超过验收上限的强模型

若 2h 内超过 30，说明题目太容易或 feedback 太多。  
这类解法可能已经成功推断 hidden 机制，不符合当前验收约束。

## 6. 后续题目规则建议

### 6.1 保留的规则

建议保留：

- work 不含 hidden；
- hidden scorer root-only；
- runner 用户执行提交代码；
- no network；
- aggregate-only 或 coarse-only feedback；
- reference = 100；
- starter < 10；
- 30min < 15。

### 6.2 需要调整的规则

建议调整：

1. 增加 public hint，让 hidden anomaly 有科学可学习性。
2. 引入 uncertainty 输出要求：

```text
prediction_intervals.csv
scenario_summary.json
uncertainty_report.md
```

3. 将 2h 目标区间设计为：

```text
starter: 5-8
30min: 8-14
2h: 15-25
reference: 90-100
```

4. 增加 coarse feedback，而不是永久完全 aggregate：

```text
MODEL_FEEDBACK: low / medium / high
PLAN_FEEDBACK: low / medium / high
RISK_FEEDBACK: low / medium / high
```

5. 评分器记录但不一定展示分项，方便验收方分析。

## 7. 对当前任务是否达标的判断

按当前验收标准：

```text
agent 可持续运行 2h
半小时不能超过 15
2h 有一些提升但不高于 30
```

当前已证明：

```text
30min < 15：满足
60min < 15：满足
90min < 15：满足
120min < 30：满足
agent 持续运行：满足
```

最终判断：

```text
2h 节点结果：10.898 / 100
2h 轮次：agent-114 与 auto-24 达到最高分
提交总数：144（agent 120 轮，auto 24 轮）
```

如果只要求“不高于 30”，当前设计很稳，并且 30min 与 2h 验收都已通过。  
如果要求“2h 有明显提升”，当前设计仍偏硬，需要 hard-v3：降低不可学噪声，增加可学习 public hint 和 coarse feedback。

## 8. 恢复后当前代码状态

恢复当前工作区后，`build_task.py`、`tasks/capecod_plumebench.json` 和 `ACCEPTANCE.md` 已经出现 hard-v3 方向的内容：

- judge 输出 qualitative `TASK_RESULT` 与 `*_FEEDBACK` band；
- 仍保留 aggregate score，不暴露 hidden truth 或 exact component scores；
- `ACCEPTANCE.md` 已明确写入 hard-v3 pass；
- `TABLE_ROW.md` 已补入 2h best score 10.898。

因此当前状态可以分成两层：

```text
hard-v2 agent 验收：已完成，30min 和 2h 均通过
hard-v3 代码/文档方向：已写入，但尚未看到新的完整 agent 验收 run
```

建议下一步先重新 build/eval 当前 hard-v3 产物，确认 starter baseline、reference submission、coarse feedback 输出都与文档一致；随后再开一个新的 `capecod-agent-hardv3-*` run 验证 30min/2h 分数区间。
