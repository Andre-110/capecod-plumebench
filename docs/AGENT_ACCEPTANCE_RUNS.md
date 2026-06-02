# CapeCod-PlumeBench Agent 验收运行记录

## hard-v2: capecod-agent-hardv2-001

运行目录：

```text
/root/SE-bench-main/logs/runs/capecod-agent-hardv2-001/capecod_plumebench
```

启动时间：

```text
2026-05-27 22:25:09 CST
```

最终统计：

```text
提交总数：144
agent 提交：120
auto-eval 提交：24
最高分：10.898 / 100
最高分轮次：agent-114；auto-24 同分
```

关键时间点：

```text
30min best：10.013 / 100，agent-16
60min best：10.553 / 100，agent-54
90min best：10.872 / 100，agent-85
120min best：10.898 / 100，agent-114 / auto-24
```

代表性轨迹：

```text
agent-1    6.499
auto-1     6.499
agent-2    8.828
auto-2     7.120
agent-16  10.013
agent-54  10.553
agent-85  10.872
agent-114 10.898
auto-24   10.898
```

验收判断：

```text
starter baseline < 10：通过
30min < 15：通过
2h 有提升：通过，但提升较弱
2h < 30：通过
```

结论：

```text
hard-v2 对短时间冲分压制有效，2h 后仍明显低于 30。
但学习曲线在 10-11 分附近平台化，说明如果要求 2h 达到 15-25 的中间能力层，需要 hard-v3 调整。
```

## 下一轮建议

当前工作区已经包含 hard-v3 方向的 coarse feedback 和 acceptance 文档。下一轮建议使用新的 run id：

```text
capecod-agent-hardv3-001
```

需要重新记录：

```text
starter baseline
reference submission
30min best
60min best
90min best
120min best
是否仍低于 30
是否进入 15-25 中间区间
```
