# Goal49 运维案例：中文说明

这是一个经过脱敏的可靠性工程案例，不公开 Goal49 的选股模型、因子、阈值、股票、收益、真实数据源或消息渠道。

公开部分只讨论：

- 临时云端运行器如何保存最小状态；
- 如何用规范化 JSON 与 SHA-256 检查准备快照；
- 如何拒绝过期、目标错误、重复或覆盖不足的数据；
- 如何按顺序降级到备用数据源；
- 如何用“用户可见结果哈希＋回执”避免重复消息；
- 如何阻止同一目标出现相互冲突的第二次发送；
- 如何设置硬截止时间，逾期只发状态，不再生成业务决策；
- 如何分别监控“准备完成”和“最终送达”。

仓库中的 `ITEM-001`、时间、数据源和资格标记全部是合成数据。代码不联网，也没有第三方运行依赖。

快速运行：

```bash
python -m pip install -e .

goal49-ops-demo run-demo \
  --config examples/synthetic-config.json \
  --universe examples/synthetic-universe.json \
  --workdir .demo
```

公开证据边界、事故时间线和限制分别见：

- `docs/privacy-boundary.md`
- `docs/incident-timeline.md`
- `docs/evidence-register.md`
- `docs/reliability-controls.md`
