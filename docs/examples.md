# Examples

本文档给出 3 个完整实验流程。所有示例默认在项目根目录执行。

## 示例 1：单个 life_burst 宇宙实验

目标：创建一个生命大爆炸宇宙，推进 30 步，查看状态、统计和事件时间线。

```bash
.venv/bin/python -m universe_lab.main create --mode life_burst --name example_life
.venv/bin/python -m universe_lab.main step --run data/runs/example_life.json --steps 30
.venv/bin/python -m universe_lab.main show --run data/runs/example_life.json
.venv/bin/python -m universe_lab.main stats --run data/runs/example_life.json
.venv/bin/python -m universe_lab.main timeline --run data/runs/example_life.json --limit 15
```

导出分析 JSON 和 Markdown 报告：

```bash
.venv/bin/python -m universe_lab.main export --run data/runs/example_life.json --out data/runs/example_life_export.json
.venv/bin/python -m universe_lab.main report --run data/runs/example_life.json --out docs/example_life_report.md
```

可以观察：

- 哪些物种处于 growing、stable、declining 或 extinct。
- 是否出现了 proto civilization。
- 哪些事件类型出现频率最高。

## 示例 2：civilization_seeds 文明种子实验

目标：创建一个包含 3 个早期文明的宇宙，推进后复制分支并对比。

```bash
.venv/bin/python -m universe_lab.main create --mode civilization_seeds --name example_civ
.venv/bin/python -m universe_lab.main step --run data/runs/example_civ.json --steps 25
.venv/bin/python -m universe_lab.main show --run data/runs/example_civ.json
```

复制分支并继续推进分支：

```bash
.venv/bin/python -m universe_lab.main branch --run data/runs/example_civ.json --name example_civ_branch
.venv/bin/python -m universe_lab.main step --run data/runs/example_civ_branch.json --steps 15
```

对比原宇宙和分支：

```bash
.venv/bin/python -m universe_lab.main compare --run-a data/runs/example_civ.json --run-b data/runs/example_civ_branch.json
```

可以观察：

- 分支是否产生更多活跃文明。
- 哪个分支事件更多。
- 文明是否进入 declining 或 collapsed 状态。

## 示例 3：batch 批量实验与 summary 汇总

目标：一次运行多个 `life_burst` 宇宙，并生成批量汇总。

```bash
.venv/bin/python -m universe_lab.main batch --mode life_burst --count 5 --steps 20 --prefix example_batch_life
```

终端汇总：

```bash
.venv/bin/python -m universe_lab.main summary --runs data/runs --prefix example_batch_life
```

生成 Markdown 汇总：

```bash
.venv/bin/python -m universe_lab.main summary --runs data/runs --prefix example_batch_life --out docs/example_batch_life_summary.md
```

可以观察：

- 平均活跃物种数量。
- 总灭绝物种数量。
- 哪个 run 的物种人口最高。
- 哪个 run 的事件最多。
- 是否有 run 出现活跃文明。
