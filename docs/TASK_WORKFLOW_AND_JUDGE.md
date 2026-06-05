# CapeCod-PlumeBench 任务工作流与评测机制说明

## 1. 任务定位

`CapeCod-PlumeBench` 是一个面向科研建模 Agent 的地下水污染羽重建与监测决策任务。任务背景来自 USGS Cape Cod treated-wastewater groundwater plume 长期监测场景，但为了满足 SE-Bench 的离线可复现、hidden judge 和稳定评分要求，实际数据是基于真实场景构造的确定性物理启发派生数据。

任务不是普通表格预测题。Agent 需要扮演地下水修复建模工程师，在只看到公开观测数据的条件下，建立污染羽时空模型，预测隐藏井和未来年份的污染物浓度，估计污染羽尺度指标，并设计下一阶段监测井方案。

本任务公开数据的实际规模如下：

| 数据文件 | 规模 | 关键字段 / 说明 |
|---|---:|---|
| `public_wells.csv` | 60 口公开井 | `well_id`, `x_m`, `y_m`, `screen_depth_m`, `aquifer_zone` |
| `public_observations.csv` | 4183 条公开历史观测 | 年份 1978-2018，4 类 analyte，含检测限记录 |
| `prediction_requests.csv` | 864 个预测目标 | 36 口目标井，6 个未来年份，4 类 analyte |
| `plume_metric_requests.csv` | 8 个污染羽指标请求 | nitrate 和 chloride，各 4 个年份 |
| `candidate_monitoring_wells.csv` | 40 口候选新井 | 预算优化对象，分为 source/core/front 区域 |

公开观测覆盖的 analyte 和阈值来自 `public_site_config.json`：

| analyte | unit | background | threshold | peak | decay | retardation |
|---|---|---:|---:|---:|---:|---:|
| `nitrate_n_mg_l` | mg/L as N | 0.12 | 10.0 | 24.0 | 0.022 | 0.92 |
| `ammonium_n_mg_l` | mg/L as N | 0.04 | 1.5 | 6.0 | 0.045 | 1.18 |
| `chloride_mg_l` | mg/L | 18.0 | 120.0 | 230.0 | 0.012 | 0.72 |
| `specific_conductance_us_cm` | uS/cm | 95.0 | 600.0 | 900.0 | 0.010 | 0.68 |

## 2. 真实的人类工作流

真实工程师处理这类问题时，一般不会直接训练一个黑盒模型，而是会经过完整的场地理解、数据清洗、物理假设、交叉验证和监测设计流程。

### 2.1 理解场地背景

工程师首先需要理解场地物理过程：

- 污染源历史：处理后污水长期入渗，源强随时间变化。
- 地下水流向：本任务中 `x_m` 近似代表 downgradient 方向。
- 含水层类型：砂砾含水层，污染羽会随地下水迁移、弥散、衰减。
- 污染物类型：nitrate、ammonium、chloride、specific conductance。
- 不同污染物迁移差异：不同 analyte 有不同背景值、阈值、衰减速度和滞后行为。

在本任务数据里，公开井的空间范围是：

- `x_m`：325.03 到 5398.22，代表从源区附近到 downgradient 前缘方向。
- `y_m`：-845.23 到 494.92，代表横向偏移和 plume margin。
- `screen_depth_m`：8.15 到 37.03，代表不同筛管深度。
- `aquifer_zone`：33 口 `margin` 井，27 口 `core` 井。

例如前 5 口公开井为：

```text
well_id,x_m,y_m,screen_depth_m,aquifer_zone
W001,873.51,-693.56,14.09,margin
W002,3988.59,-56.0,29.03,core
W003,3651.15,21.65,24.04,core
W005,1326.66,-246.27,16.22,margin
W006,2070.97,-12.88,18.91,core
```

这组数据直接影响建模假设。例如 `W001` 横向偏移较大、属于 `margin`，不能简单用作 plume centerline；`W002` 和 `W003` 位于较大 `x_m` 且属于 `core`，更可能对 downgradient plume 趋势有信息量。

### 2.2 读取和清洗公开数据

Agent 能看到的数据包括：

- `data/public_wells.csv`：公开监测井位置、筛管深度、含水层分区。
- `data/public_observations.csv`：公开历史观测浓度。
- `data/prediction_requests.csv`：需要预测的隐藏井、年份和 analyte 请求。
- `data/plume_metric_requests.csv`：需要估计的污染羽尺度指标请求。
- `data/candidate_monitoring_wells.csv`：候选新监测井。
- `data/public_site_config.json`：阈值、单位、预算、最大井数等配置。
- `schemas/output_schema.json`：输出结构要求。

清洗重点包括：

- `less_than_detection` 的检测限数据如何处理。
- 缺失年份和缺失 analyte 如何补偿。
- 井位、深度、年份、analyte 单位是否一致。
- 公开井和 prediction request 中出现的井是否可以合并利用空间信息。
- 对低浓度背景值、异常峰值和未来外推风险进行稳健处理。

本任务公开观测的具体情况是：

- 总观测行数：4183。
- 年份范围：1978-2018。
- `remark=measured`：3920 行。
- `remark=less_than_detection`：263 行。
- 各 analyte 行数：
  - `ammonium_n_mg_l`：1049 行。
  - `chloride_mg_l`：1049 行。
  - `specific_conductance_us_cm`：1049 行。
  - `nitrate_n_mg_l`：1036 行。

示例观测行：

```text
well_id,year,analyte,value,unit,remark
W001,1978,nitrate_n_mg_l,0.42637,mg/L as N,measured
W001,1978,ammonium_n_mg_l,0.18631,mg/L as N,measured
W001,1978,chloride_mg_l,11.1829,mg/L,less_than_detection
W001,1978,specific_conductance_us_cm,173.71869,uS/cm,measured
W001,1980,nitrate_n_mg_l,0.74808,mg/L as N,measured
W001,1980,specific_conductance_us_cm,82.93591,uS/cm,less_than_detection
```

因此清洗步骤不能简单丢弃 `less_than_detection`。例如 `W001,1978,chloride_mg_l=11.1829` 是低于检测限记录，若直接当作正常精确浓度使用，会低估边缘井或背景区域的浓度；若直接删除，又会丢失背景浓度约束。一个合理处理方式是把这类值向 analyte background 收缩，或者按低浓度 censored observation 处理。

近期公开观测较少但很关键，2008 年后的公开观测分布如下：

| year | rows |
|---:|---:|
| 2010 | 101 |
| 2012 | 116 |
| 2014 | 118 |
| 2016 | 107 |
| 2018 | 105 |

这些 2010-2018 年观测对未来 2020-2040 的外推特别重要，因为它们比 1978-2008 的早期数据更接近 prediction requests。

### 2.3 探索性分析

真实工程师会先做 EDA，而不是直接预测：

- 按 analyte 分组查看浓度分布。
- 按年份看污染羽是否前移。
- 按 `x_m` 看 plume front 位置。
- 按 `y_m` 看 lateral spreading 和 plume bending。
- 按 `screen_depth_m` 看垂向深度效应。
- 比较 nitrate、chloride、ammonium 的迁移速度和衰减差异。
- 识别公开数据中是否存在 source shutdown、rebound、tailing、future acceleration 的迹象。

本任务中，EDA 可以直接围绕以下具体问题展开：

1. **沿 x 方向的 plume front。**  
   `public_wells.csv` 中公开井最大 `x_m=5398.22`，prediction requests 中目标井也覆盖远 downgradient 区域。工程师会按 analyte 和年份找出超过阈值的最大 `x_m`，估计前缘速度。

2. **横向 plume margin。**  
   公开井 `y_m` 范围从 -845.23 到 494.92。像 `W001,y=-693.56` 是明显 margin 井，而 `W002,y=-56.0` 更接近 core。模型需要区分 core 和 margin，不能只按 `x_m` 单变量外推。

3. **垂向深度。**  
   公开井筛管深度为 8.15-37.03m。候选井也有 `screen_depth_m` 字段，例如 `C001` 深度 32.93m，`C008` 深度 23.33m。深度错配会影响浓度预测。

4. **analyte-specific 行为。**  
   nitrate 阈值是 10.0 mg/L as N，chloride 阈值是 120.0 mg/L，specific conductance 阈值是 600.0 uS/cm。它们的 background 和 retardation 不同，不能共用一个全局衰减曲线。

5. **公开未来弱信号。**  
   虽然主要公开数据到 2008 年，但 2010-2018 年仍有少量观测。真实工程师会把这些记录作为 rolling validation 或 future extrapolation anchor，而不是只用全历史均值。

### 2.4 建立时空污染羽模型

强解法通常不是单纯均值或最近邻，而是混合模型：

- 历史同井趋势模型：如果某个井有 2010-2018 附近观测，可以用作未来外推基础。
- 空间核平滑：利用相近 `x/y/z/year/analyte` 的观测。
- advection-dispersion 特征：考虑污染羽沿 x 方向推进，横向和纵向弥散。
- analyte-specific 参数：不同 analyte 的 retardation、attenuation、background 不同。
- future scenario 调整：题面暗示 hidden 有 plume acceleration、lateral drift、rebound 和 hidden scenario shift。
- 风险阈值校准：不仅要预测浓度，还要预测是否超过阈值。

`prediction_requests.csv` 的具体目标规模是：

- 总预测行数：864。
- 目标井数：36。
- 目标年份：2020、2024、2028、2032、2036、2040。
- analyte 数量：4，每类 216 个预测目标。
- 其中 12 口目标井也属于公开井集合，对应 288 行。
- 其中 24 口目标井不在公开井集合，对应 576 行。

示例预测请求：

```text
target_id,well_id,x_m,y_m,screen_depth_m,year,analyte,unit,threshold
T0001,W004,2979.64,-344.89,23.68,2020,nitrate_n_mg_l,mg/L as N,10.0
T0002,W004,2979.64,-344.89,23.68,2020,ammonium_n_mg_l,mg/L as N,1.5
T0003,W004,2979.64,-344.89,23.68,2020,chloride_mg_l,mg/L,120.0
T0004,W004,2979.64,-344.89,23.68,2020,specific_conductance_us_cm,uS/cm,600.0
T0005,W004,2979.64,-344.89,23.68,2024,nitrate_n_mg_l,mg/L as N,10.0
T0006,W004,2979.64,-344.89,23.68,2024,ammonium_n_mg_l,mg/L as N,1.5
T0007,W004,2979.64,-344.89,23.68,2024,chloride_mg_l,mg/L,120.0
T0008,W004,2979.64,-344.89,23.68,2024,specific_conductance_us_cm,uS/cm,600.0
```

这个例子说明同一口目标井 `W004` 在同一年要预测 4 个 analyte，并且同一井位还要外推到多个未来年份。因此模型应复用同一井位的空间、深度、年份信息，而不是把 864 行当作彼此独立的表格样本。

一个更接近工程逻辑的模型会把每个请求转换为特征，例如：

```text
target = (well_id, x_m, y_m, screen_depth_m, year, analyte, threshold)
features = (
  downgradient coordinate x_m,
  lateral offset y_m,
  screen depth mismatch,
  year - source year,
  analyte-specific background/threshold/retardation/decay,
  same-well recent observations if available,
  nearby public observations in retarded travel-time coordinates
)
```

这样可以同时处理 `W004` 这类隐藏目标井和公开目标井的未来外推。

### 2.5 估计污染羽尺度指标

对于 `plume_metrics.json`，人类工作流通常会构造一个空间网格：

- 在多个 `x_m` 和 `y_m` 上预测浓度。
- 找出超过阈值的最远 `x_m`，作为 `plume_front_x_m`。
- 对超过阈值区域按浓度超额加权，估计 `centerline_y_m`。
- 对浓度超过背景值的部分积分或求和，得到 `mass_proxy`。

本任务的 plume metric 请求只有 8 个，但分值高达 26 分，因此非常关键：

```text
request_id,year,analyte,threshold
M001,2024,nitrate_n_mg_l,10.0
M002,2028,nitrate_n_mg_l,10.0
M003,2032,nitrate_n_mg_l,10.0
M004,2040,nitrate_n_mg_l,10.0
M005,2024,chloride_mg_l,120.0
M006,2028,chloride_mg_l,120.0
M007,2032,chloride_mg_l,120.0
M008,2040,chloride_mg_l,120.0
```

这意味着模型不能只输出 864 个点预测，还必须能在 2024、2028、2032、2040 年构造 nitrate 和 chloride 的空间污染羽。一个常见实现是：

1. 在 `x_m=100..5600`、`y_m=-750..750` 的规则网格上生成虚拟请求点。
2. 用与点预测相同的模型预测网格浓度。
3. 对超过 threshold 的网格点求最大 x，得到 front。
4. 对超过 threshold 的网格点按 `value - threshold` 加权求 y 坐标，得到 centerline。
5. 对 `value - background` 的正值部分求和，得到 mass proxy。

如果只用占位公式，例如 `front = 1850 + 25 * (year - 2010)`，通常只能拿到很低的 metrics 分，因为它无法响应 analyte、future acceleration 和 lateral drift。

### 2.6 设计监测井方案

真实监测设计不是选最高浓度点这么简单。需要兼顾：

- 预算上限。
- 最多 8 口井。
- 污染羽前缘覆盖。
- lateral margin 覆盖。
- 深度覆盖。
- 不确定性高的区域。
- 阈值附近区域，因为这些点最能改善风险分类。
- 空间多样性，避免多口井太近。

输出是 `monitoring_plan.json`，包含 `selected_wells`、`total_cost_usd` 和 `method`。

本任务候选监测井共有 40 口：

- `core`：19 口。
- `front`：13 口。
- `source`：8 口。
- `x_m` 范围：564.06 到 5097.45。
- 单井总成本，即 `install_cost_usd + annual_sampling_cost_usd`，范围约 6394.91 到 15043.38 美元。
- 预算：72000 美元。
- 最多新井数：8。

示例候选井：

```text
candidate_id,x_m,y_m,screen_depth_m,install_cost_usd,annual_sampling_cost_usd,zone
C001,2997.42,-46.23,32.93,5284.44,1110.47,core
C002,4170.0,181.5,25.51,5969.98,1826.52,front
C003,4171.85,-411.93,28.76,8891.82,923.91,front
C004,801.97,95.17,23.88,13281.92,1087.3,source
C005,2899.85,274.39,18.77,13694.48,1348.9,core
C006,4115.04,-182.15,31.56,8082.24,839.04,front
C007,2897.92,105.06,17.78,9313.86,1207.58,core
C008,1424.76,416.34,23.33,13189.28,1450.52,core
```

人类工程师看到这些候选井时，会做类似下面的判断：

- `C002`、`C003`、`C006` 位于 front zone，适合约束 downgradient plume front。
- `C003,y=-411.93` 和 `C002,y=181.5` 横向位置差异大，可以覆盖 plume margin 两侧。
- `C004` 位于 source zone，可能对 rebound 或 source-area residual 有价值，但成本较高。
- `C001` 是低成本 core 井，总成本约 6394.91 美元，可能作为 cost-efficient core control。
- 如果 8 口井都选 front zone，可能前缘覆盖强，但 source/core 趋势和 lateral diversity 不足。

因此 monitoring plan 的工程目标不是简单最大化预测浓度，而是在预算内最大化信息量。

### 2.7 生成报告

`report.md` 和 `answer.json` 用于解释模型，不是主要分数来源，但用于检查提交是否具有合理工程说明。报告应包含：

- 数据处理方式。
- 模型假设。
- advection、dispersion、attenuation、rebound 的处理。
- 公开数据验证方式。
- 监测井选择逻辑。
- 不确定性和局限性。

## 3. 评分规则

任务总分为 100 分。内部评分由多个部分组成：

| 模块 | 分值 | 说明 |
|---|---:|---|
| 格式与约束 | 2 | 检查 required outputs、CSV/JSON 结构、非负有限值、预算约束等 |
| hidden 浓度预测 | 45 | 比较 `predictions.csv` 和 hidden truth |
| 阈值风险分类 | 20 | 判断预测值是否超过 analyte threshold |
| plume metrics | 26 | 比较污染羽前缘、中心线、质量 proxy |
| monitoring plan | 6 | 用 hidden candidate utility 评价监测井方案 |
| report / answer | 1 | 检查报告关键词、长度、answer 结构 |

### 3.1 格式分

提交必须生成：

- `predictions.csv`
- `plume_metrics.json`
- `monitoring_plan.json`
- `answer.json`
- `report.md`

并且预测值必须是有限、非负数。监测井方案不得超过预算和最大井数。

例如 starter baseline 虽然模型很弱，但会生成完整文件，因此能拿到格式相关分数。修复后的 smoke test 中，空 baseline 的结果为：

```text
TOTAL_SCORE 6.499
pass_rate 6.50%
```

这说明它不是 runtime failure，也不是格式非法，而是核心预测、risk 和 metrics 分数较低。

### 3.2 浓度预测分

Judge 读取 hidden truth：

```text
/opt/capecod_hidden/hidden_targets.csv
```

然后与 `predictions.csv` 按 `target_id` 合并，计算 log-RMSE：

```text
log_rmse = sqrt(mean((log1p(pred) - log1p(truth))^2))
```

预测分公式近似为：

```text
prediction_score = 45 * max(0, 1 - log_rmse / 0.34)^2
```

这意味着分数曲线比较陡。预测如果只是大致趋势正确，但 hidden future shift、rebound、局部异常没有处理好，分数仍然不会很高。

本任务中 `prediction_requests.csv` 有 864 行，因此一个预测文件必须包含 864 个 `target_id` 的非负预测值。典型输出结构如下：

```text
target_id,predicted_value
T0001,12.34
T0002,0.56
...
```

如果某些 `target_id` 缺失，或 `predicted_value` 出现 NaN、inf、负数，格式分和预测分都会受影响。因为评分使用 `log1p`，低浓度背景区域和高浓度 plume core 区域都会影响 RMSE；把所有点预测成全局均值通常会同时损失 plume core、front 和 margin 信息。

### 3.3 风险分类分

每个 prediction request 有 analyte threshold。Judge 判断：

```text
truth_value >= threshold
predicted_value >= threshold
```

然后计算 precision、recall、F1：

```text
risk_score = 20 * max(0, (f1 - 0.55) / 0.45)^1.4
```

所以如果模型过度平滑，导致高风险点被预测成低风险，risk score 会很差。

具体到本任务，请求行自带阈值。例如：

```text
T0001,W004,...,2020,nitrate_n_mg_l,...,threshold=10.0
T0002,W004,...,2020,ammonium_n_mg_l,...,threshold=1.5
T0003,W004,...,2020,chloride_mg_l,...,threshold=120.0
T0004,W004,...,2020,specific_conductance_us_cm,...,threshold=600.0
```

因此同一个井位、同一年份会产生 4 个不同风险判断。一个模型如果对 nitrate 预测偏低，会漏报 `nitrate_n_mg_l >= 10.0` 的风险；如果对 chloride 或 conductance 使用同一尺度，又会造成大量误报或漏报。

### 3.4 plume metrics 分

Judge 读取：

```text
/opt/capecod_hidden/hidden_metrics.json
```

对比 agent 提交的 `plume_metrics.json`。

误差包括：

- `plume_front_x_m` 误差，按约 260m 缩放。
- `centerline_y_m` 误差，按约 130m 缩放。
- `mass_proxy` 误差，按 log1p 后约 0.45 缩放。

最终：

```text
metric_score = 26 * exp(-2.2 * metric_error)
```

所以 plume metrics 需要整体污染羽结构正确，不只是点预测局部正确。

这部分的 8 个请求虽然数量少，但每个请求都是空间整体量。举例：

- `M001` 要求 2024 年 nitrate 的 plume front、centerline 和 mass proxy。
- `M004` 要求 2040 年 nitrate，外推跨度最长。
- `M005` 到 `M008` 是 chloride，阈值和迁移参数不同，不能直接复用 nitrate 的前缘。

如果点预测模型只在 36 口目标井上表现尚可，但不能生成合理网格污染羽，metrics 分仍然会低。

### 3.5 monitoring plan 分

Judge 读取 hidden candidate utilities：

```text
/opt/capecod_hidden/hidden_candidate_utilities.csv
```

然后比较 agent 选择的候选井与 reference candidate set 的 hidden utility 总和。

约束包括：

- 候选井 ID 必须存在。
- 不能重复。
- 最多 8 口井。
- 总成本不能超过预算。
- 空间过近会有 penalty。

最高 6 分。这个模块分值不大，但可以反映工程决策能力。

以预算 72000 美元、最多 8 口井为例，若选择 8 口平均成本约 9000 美元的井，基本会贴近预算；若选择多个成本超过 14000 美元的井，则很容易只能选 5-6 口。Scorer 会按 hidden utility 评价所选井的信息价值，因此一个只按最低成本排序的方案通常能合法提交，但不会有高 monitoring utility。

### 3.6 report 分

报告分只有 1 分，主要检查：

- 是否包含 `plume`
- `groundwater`
- `monitoring`
- `uncertainty`
- `advection`
- `dispersion`
- 报告长度是否足够
- `answer.json` 是否包含 `model_summary`

这不是核心分，但能避免纯输出文件没有解释。

例如报告如果只有一句 “baseline model”，即使预测文件有效，也很难拿满 1 分；而包含 `plume`、`groundwater`、`monitoring`、`uncertainty`、`advection`、`dispersion` 等关键词，并解释数据处理和监测设计逻辑，通常能拿到报告部分的大部分分数。

## 4. Work 和 Judge 的交互机制

SE-Bench 使用三层结构：

```text
Host
  └── Judge Server

Work Container
  └── Agent 工作环境

Judge Container
  └── Hidden truth + scorer
```

### 4.1 Work Container

Work container 是 agent 实际工作的地方，路径为：

```text
/home/workspace/capecod_plumebench
```

Agent 能看到：

- 公开数据。
- README。
- schema。
- starter code。
- `sebench-submit`。

Agent 看不到：

- hidden targets。
- hidden metrics。
- hidden candidate utilities。
- scorer 源文件。

### 4.2 Judge Server

Judge server 跑在 host 上，监听：

```text
0.0.0.0:8080
```

它负责：

- 注册 run session。
- 接收 work container 提交。
- 为每次提交启动临时 judge container。
- 收集评分结果。
- 维护 run history。
- 返回 aggregate score 和 coarse feedback。

### 4.3 Judge Container

每次提交都会创建一个临时 judge container。它包含：

```text
/opt/capecod_hidden/hidden_targets.csv
/opt/capecod_hidden/hidden_metrics.json
/opt/capecod_hidden/hidden_candidate_utilities.csv
/opt/capecod_scoring/evaluate.py
```

隐藏目录是 root-only。提交代码运行时使用受限 `runner` 用户，不能读取 hidden 文件。

## 5. 一次提交的完整流程

1. Agent 修改代码和输出文件。
2. Agent 执行：

```bash
sebench-submit
```

或者 auto-eval daemon 每 300 秒自动执行：

```bash
sebench-submit --auto-eval
```

3. `sebench-submit` 打包允许提交的文件：

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

4. 通过 HTTP POST 发送给 Judge Server。
5. Judge Server 创建临时 Judge Container。
6. Judge Container 解包提交文件，运行：

```bash
python /opt/capecod_scoring/evaluate.py
```

7. Scorer 执行提交代码，通常会运行：

```bash
python baseline_solver.py
```

8. 提交代码生成：

```text
predictions.csv
plume_metrics.json
monitoring_plan.json
answer.json
report.md
```

9. Scorer 用 root 权限读取 hidden truth，计算分数。
10. Judge Server 返回结果给 work container。

## 6. Judge 返回给 Agent 的信息

Judge 返回的是 coarse feedback，不是完整评分细节。

典型输出：

```text
CASE aggregate OK score=20.700 aggregate score only
TASK_RESULT model_prediction low
TASK_RESULT risk_classification low
TASK_RESULT plume_metrics medium
TASK_RESULT monitoring_design medium
TASK_RESULT report high
MODEL_FEEDBACK ...
RISK_FEEDBACK ...
METRIC_FEEDBACK ...
PLAN_FEEDBACK ...
TOTAL_SCORE 20.700
CASES_OK 1
CASES_TOTAL 1
```

Agent 能看到：

- 总分：`TOTAL_SCORE`。
- aggregate case score。
- 每个大模块的粗等级：`low / medium / high`。
- 每个模块的方向性文字反馈。

Agent 看不到：

- hidden truth value。
- 每个 target 的误差。
- prediction/risk/metrics/plan 的具体子分。
- hidden candidate utility。
- reference candidate set。

一个真实返回示例来自修复后的 2 小时 run：

```text
round: agent-102
TOTAL_SCORE: 22.045
pass_rate: 22.045%
```

另一个空 baseline smoke test 示例：

```text
round: manual-1
TOTAL_SCORE: 6.499
pass_rate: 6.499%
```

这两个例子说明，修复后 `pass_rate` 不再表示“离散测试是否通过”，而是连续总分的归一化进度。`6.499` 不会再被展示成 100% pass。

### 6.1 粗等级规则

内部有一个 `quality_label` 逻辑，大致是：

```text
>= 72% of component max: high
>= 35% of component max: medium
otherwise: low
```

例如 prediction component 满分 45：

- 预测分达到约 32.4 以上才是 high。
- 达到约 15.75 以上是 medium。
- 低于这个就是 low。

这就是为什么 agent 经常看到 `prediction low`，即使总分已有 20 左右。

### 6.2 为什么只返回粗反馈

这个设计是为了平衡两件事。

一是可学习性。Agent 至少能知道哪个方向弱：

- prediction 低：继续改污染羽点预测。
- risk 低：阈值分类和高风险点需要校准。
- metrics 低：污染羽前缘、中心线、质量 proxy 不准。
- plan 低：监测井方案 hidden utility 不高。

二是防泄露。如果返回每个 target 的误差、hidden 真值、精确 component score，agent 很容易通过黑盒 hill-climb 或反推 hidden 数据。因此当前只给总分和粗方向。

## 7. 当前修复后的运行口径

原来 `score_sum` 只要 `CASE aggregate OK` 就会显示 `pass_rate=100%`，导致 `6.499/100` 也看起来像“全部通过”。这会误导 agent 和 harness。

当前已修复为：

```text
pass_rate = TOTAL_SCORE / 100
```

例如：

```text
score = 20.700
pass_rate = 20.70%
```

这样 agent 和 harness 不会再误判低分提交已经完成。

另外，原来 Codex stop hook 不可靠，agent 进程退出后 run 会停止。当前 `run_agent` 外层增加了重启机制：

- agent 退出但 timeout 未耗尽时，harness 会继续启动下一轮。
- workspace 保留。
- judge history 保留。
- continuation prompt 会告诉 agent 不要从头开始，而是继续优化当前解。

因此 `capecod-agent-fixed-001` 能跑满 2 小时，`capecod-agent-long-001` 能在 24 小时上限下继续运行。

## 8. 当前长跑状态记录

当前长跑：

```text
run_id: capecod-agent-long-001
timeout: 86400s
```

最近一次检查时：

- 已运行约 2.5 小时。
- 当前进入 iteration 2。
- 24h 最终 best score：`31.093 / 100`。
- 上一轮 2 小时 run 的 best 是 `22.045 / 100`。
- 长跑已完成，运行时长约 86400 秒。

作为对照，修复前后有代表性的运行分数如下：

| run_id | runtime | best score | 说明 |
|---|---:|---:|---|
| `capecod-empty-baseline` / smoke | 秒级 | 6.499 | starter baseline，格式有效但模型弱 |
| `capecod-agent-hardv2-001` | 2h | 10.898 | 早期 hard-v2，aggregate feedback 下提升有限 |
| `capecod-agent-hardv3-005` | 约 65min | 11.813 | hard-v3 一次中等表现 |
| `capecod-agent-fixed-001` | 2h | 22.045 | 修复 pass_rate 和外层持续运行后达到中间区间 |
| `capecod-agent-long-001` | 24h | 31.093 | 24h 上限长跑完成，2745 次提交，最终 best round `agent-2457` |
