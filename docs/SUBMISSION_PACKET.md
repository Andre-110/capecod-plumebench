# CapeCod-PlumeBench 提交材料草案

## 1. 任务名称

CapeCod-PlumeBench：地下水污染羽时空重建、隐藏监测井/隐藏年份浓度预测与监测井布设优化。

## 2. 任务类型

- 领域：土木/环境工程/地下水污染修复
- 任务类型：科研建模 + 隐藏评测 + 策略优化
- SE-Bench parser：`score_sum`
- 是否需要联网：不需要。任务数据在镜像构建时离线生成，Agent 运行阶段不依赖外网。
- 资源需求：CPU 2 核以上，内存 4GB 以上；推荐 CPU 4 核、内存 8GB。无需 GPU。

## 3. 真实科研场景背景

任务锚定 USGS Cape Cod treated-wastewater groundwater plume 长期监测场景。官方数据 release 覆盖 1978-2018 年水质数据和采样点特征，用于研究处理后污水陆地处置对 Cape Cod 砂砾含水层地下水质量的影响。该场地曾近 60 年将处理后污水排入快速入渗床，1995 年 12 月后处置位置迁移；污染羽部分排入距入渗床约 1,600 英尺的冰川壶穴湖，并向 Vineyard Sound 一带延伸约 4.5 英里。

本任务没有在构建时在线下载 USGS 大数据，而是基于该真实场景构造一个离线、确定性、可隐藏评测的物理启发派生基准。这样做的原因是 SE-Bench 任务需要可复现、可离线构建、可稳定评分，并且 hidden 数据不能暴露给 Agent。

官方来源：

```text
USGS Data Release:
Chemical Data From 40 Years of Monitoring a Treated-Wastewater Groundwater Plume
in a Sand and Gravel Aquifer, Cape Cod, Massachusetts, 1978-2018
```

## 4. Agent 任务目标

Agent 扮演地下水修复建模工程师，需要基于公开监测井、水质观测和场地参数，完成以下工作：

1. 清洗公开监测井和水质数据，处理缺失值、检测限、单位和异常点。
2. 建立地下水污染羽时空预测模型。
3. 对 hidden wells / hidden years / hidden analytes 的浓度进行预测。
4. 判断浓度是否超过风险阈值。
5. 估计污染羽前缘、中心线、质量 proxy 等 plume-scale metrics。
6. 在预算和井数约束下设计下一阶段监测井布设方案。
7. 写出技术报告，解释模型、假设、验证方法和监测策略。

## 5. 输入数据

Work 容器公开给 Agent：

```text
data/public_wells.csv
data/public_observations.csv
data/prediction_requests.csv
data/plume_metric_requests.csv
data/candidate_monitoring_wells.csv
data/public_site_config.json
schemas/output_schema.json
README.md
model.py
predict.py
monitoring_plan.py
baseline_solver.py
```

Judge 容器隐藏数据：

```text
/opt/capecod_hidden/hidden_targets.csv
/opt/capecod_hidden/hidden_metrics.json
/opt/capecod_hidden/hidden_candidate_utilities.csv
/opt/capecod_scoring/evaluate.py
```

隐藏数据包含更远年份、更强的 plume acceleration、lateral drift、analyte-specific rebound 和 hidden scenario shift。公开数据只给出较早年份和部分观测，防止简单插值直接高分。

## 6. 输出格式

Agent 需要最终产出：

```text
model.py
predict.py
monitoring_plan.py
baseline_solver.py
predictions.csv
plume_metrics.json
monitoring_plan.json
answer.json
report.md
```

`predictions.csv`：

```text
target_id,predicted_value
```

`plume_metrics.json`：

```json
{
  "metrics": [
    {
      "request_id": "M001",
      "plume_front_x_m": 0.0,
      "centerline_y_m": 0.0,
      "mass_proxy": 0.0
    }
  ]
}
```

`monitoring_plan.json`：

```json
{
  "selected_wells": [
    {"candidate_id": "C001", "reason": "front uncertainty"}
  ],
  "total_cost_usd": 0.0,
  "method": "brief method"
}
```

约束：

- 最多选择 8 口候选井。
- 总成本不得超过 `public_site_config.json` 中的预算。
- 所有预测值必须有限、非负。

## 7. 评分方案

总分 100：

```text
格式与约束合规：2
隐藏浓度预测：45
超标风险分类：20
污染羽指标估计：26
监测井布设方案：6
报告和解释：1
```

评分输出：

```text
CASE aggregate OK score=...
TASK_RESULT model_prediction low|medium|high
TASK_RESULT risk_classification low|medium|high
TASK_RESULT plume_metrics low|medium|high
TASK_RESULT monitoring_design low|medium|high
MODEL_FEEDBACK ...
RISK_FEEDBACK ...
METRIC_FEEDBACK ...
PLAN_FEEDBACK ...
TOTAL_SCORE ...
CASES_OK ...
CASES_TOTAL 1
```

SE-Bench 使用 `score_sum` parser 解析连续分数。Agent 能看到 aggregate 总分和 coarse feedback，但看不到 prediction/risk/metrics/monitoring 的精确分项分数或 hidden 真值，兼顾学习性和防快速 hill-climb。

## 8. 防泄露与防作弊设计

1. Work 镜像不包含 `/opt/capecod_hidden`。
2. Hidden truth 和 hidden utility 只在 judge 镜像中生成。
3. Hidden 文件目录权限为 root-only。
4. 评分时提交代码先以 `runner` 非特权用户执行。
5. 已验证 `runner` 读取 `/opt/capecod_hidden/hidden_targets.csv` 会 permission denied。
6. 评分器不信任 stdout，而是读取提交生成的结构化文件。
7. 评分包含格式、数值有效性、预算约束、浓度预测、风险分类、plume metrics、监测井 utility 和报告质量。
8. Hidden scenario 与 public observations 存在未来年份、空间漂移和 rebound 差异，降低公开数据简单拟合风险。

## 9. 难度说明

空白 starter baseline 在加难后得分：

```text
6.499 / 100
```

参考解得分：

```text
100.000 / 100
```

这说明：

- 任务可解，不是不可完成题。
- starter 只能拿到 15 分以下，符合“半小时不能超过 15 分”的方向。
- 从 30 分提升到高分需要真正建模地下水污染羽时空演化、未来 extrapolation、阈值风险、plume metrics 和 monitoring design。

## 10. 人类 20 小时工作量拆解

预估人类完成高质量解法需要 20 小时以上：

```text
1. 理解场地背景、USGS plume 资料和数据字典：2.0h
2. 探索公开井位、年份、analyte、检测限和缺失模式：2.0h
3. 数据清洗、单位处理、censored value 处理：2.0h
4. 设计 advection-dispersion / hybrid interpolation 特征：3.0h
5. 拟合 analyte-specific attenuation、retardation、rebound 行为：3.0h
6. 交叉验证和 public holdout 调参：2.5h
7. plume front / centerline / mass proxy 网格估计：2.0h
8. monitoring plan 约束优化和不确定性分析：2.0h
9. 报告、answer.json、代码整理和 debug：2.0h
10. 多轮提交、日志分析、鲁棒性修复：2.0h
```

合计约 22.5 小时。

## 11. 环境空跑比例

当前验证中，评分运行时间为秒级到十几秒级。镜像构建主要是安装 `numpy/pandas` 和生成小型 CSV/JSON 数据。Agent 的主要时间会花在读取任务、建模、调参、运行本地验证和提交反馈上，而不是等待长时间仿真或外部下载。

估计环境空跑占比低于 10%，满足“环境空跑时间不能超过 50%”要求。

## 12. 交付物位置

```text
/root/SE-bench-main/tasks/capecod_plumebench.json
/root/SE-bench-main/task_blueprints/capecod_plumebench/build_task.py
/root/SE-bench-main/task_blueprints/capecod_plumebench/create_capecod_task.py
/root/SE-bench-main/task_blueprints/capecod_plumebench/ACCEPTANCE.md
/root/SE-bench-main/task_blueprints/capecod_plumebench/RESULTS.md
/root/SE-bench-main/task_blueprints/capecod_plumebench/SUBMISSION_PACKET.md
/root/SE-bench-main/task_blueprints/capecod_plumebench/empty_baseline.tar.gz
/root/SE-bench-main/task_blueprints/capecod_plumebench/reference_submission.tar.gz
```

已构建镜像：

```text
sebench.work.capecod_plumebench:latest
sebench.judge.capecod_plumebench:latest
```

## 13. 仍需人工补充的提交材料

若要正式提交到外部表格，还建议补充：

1. 数据收集表中的任务行。
2. 跑通截图或日志截图。
3. 如验收方严格要求“直接真实数据”，需要把 USGS 原始数据下载并纳入生成链，或在提交说明中明确当前是“真实场景锚定的物理派生隐藏基准”。
