# Usage Guide

本文档说明 Universe Evolution Lab 的所有命令。所有示例默认在项目根目录执行。

如果系统中 `python` 指向 Python 3，可以把示例中的 `.venv/bin/python` 替换为 `python`。

## create

用途：创建一个新的宇宙实验，并保存到 `data/runs/<name>.json`。

示例：

```bash
.venv/bin/python -m universe_lab.main create --mode life_burst --name test_life
.venv/bin/python -m universe_lab.main create --mode civilization_seeds --name test_civ
.venv/bin/python -m universe_lab.main create --mode minimal_observer --name test_observer
```

说明：

- `--mode` 必须是 `life_burst`、`civilization_seeds`、`minimal_observer` 之一。
- `--name` 会作为宇宙名称，也会用于默认存档路径。
- 可选 `--seed` 用于创建可复现实验。
- 可选 `--output` 用于指定存档路径。

## step

用途：推进指定宇宙若干步，并覆盖保存到原存档。

示例：

```bash
.venv/bin/python -m universe_lab.main step --run data/runs/test_life.json --steps 10
```

说明：

- `--run` 指向已有 JSON 存档。
- `--steps` 必须大于 0。
- 每一步都会推进 age，并生成至少一条事件。

## show

用途：查看一个宇宙当前状态、生命状态、文明状态和最近事件。

示例：

```bash
.venv/bin/python -m universe_lab.main show --run data/runs/test_life.json
.venv/bin/python -m universe_lab.main show --run data/runs/test_life.json --events 20
```

说明：

- 默认展示最近 10 条事件。
- 如果没有文明，会显示 `none`，不会报错。
- 可选 `--json` 输出简要 JSON 摘要。

## stats

用途：输出当前宇宙统计数据。

示例：

```bash
.venv/bin/python -m universe_lab.main stats --run data/runs/test_life.json
```

说明：

- 包括物种总数、活跃物种、灭绝物种、种群、平均智能、平均合作、平均适应力。
- 包括文明总数、活跃文明、崩溃文明、文明人口、平均知识、组织度、稳定性。
- 包括事件总数和按类型计数。

## timeline

用途：按年份查看事件历史。

示例：

```bash
.venv/bin/python -m universe_lab.main timeline --run data/runs/test_life.json
.venv/bin/python -m universe_lab.main timeline --run data/runs/test_life.json --limit 20
```

说明：

- 默认展示全部事件。
- `--limit` 会选择最近 N 条事件，并按 year 升序展示。
- 没有事件时会友好提示。

## branch

用途：从某个存档复制一个平行宇宙分支。

示例：

```bash
.venv/bin/python -m universe_lab.main branch --run data/runs/test_life.json --name test_life_branch
```

说明：

- 分支会保留原宇宙的历史状态和事件。
- 分支会生成新的 universe id，并记录 `branch_created` 事件。
- 这是 minimal observer 模式下的主要对照实验方式。

## export

用途：导出便于分析的 JSON 文件。

示例：

```bash
.venv/bin/python -m universe_lab.main export --run data/runs/test_life.json --out data/runs/test_life_export.json
```

说明：

- 导出内容包括宇宙基本信息、物种摘要、文明摘要、事件摘要、简化物种列表、简化文明列表和完整时间线。
- 平均值保留 2 位小数。
- `--out` 的父目录不存在时会自动创建。

## report

用途：生成 Markdown 实验报告。

示例：

```bash
.venv/bin/python -m universe_lab.main report --run data/runs/test_life.json --out docs/test_life_report.md
```

说明：

- 报告包括 Basic Info、Species Summary、Civilization Summary、Event Summary、Species Overview、Civilization Overview 和 Recent Timeline。
- Recent Timeline 默认使用最近 20 条事件。
- 没有文明时会写明 `none`。

## compare

用途：对比两个宇宙或两个分支的统计差异。

示例：

```bash
.venv/bin/python -m universe_lab.main compare --run-a data/runs/test_life.json --run-b data/runs/test_life_branch.json
```

说明：

- 输出两个宇宙的 name、mode、age。
- 对比活跃物种、灭绝物种、物种总人口、活跃文明、崩溃文明、文明总人口和事件总数。
- 输出事件类型计数差异和简短 conclusion。

## batch

用途：一次创建并推进多个宇宙实验。

示例：

```bash
.venv/bin/python -m universe_lab.main batch --mode life_burst --count 10 --steps 50 --prefix batch_life
.venv/bin/python -m universe_lab.main batch --mode civilization_seeds --count 5 --steps 30 --prefix batch_civ
.venv/bin/python -m universe_lab.main batch --mode minimal_observer --count 5 --steps 30 --prefix batch_observer
```

说明：

- 自动创建 `<prefix>_001`、`<prefix>_002` 等存档。
- 存档默认写入 `data/runs`。
- `count` 必须大于 0。
- `steps` 可以为 0。
- 每个 run 会输出 name、mode、age、active species、active civilizations 和 events total。

## summary

用途：读取一批同 prefix 的 JSON 存档，并生成批量汇总。

示例：

```bash
.venv/bin/python -m universe_lab.main summary --runs data/runs --prefix batch_life
.venv/bin/python -m universe_lab.main summary --runs data/runs --prefix batch_life --out docs/batch_life_summary.md
```

说明：

- `--runs` 指定存档目录。
- `--prefix` 用于匹配文件名开头。
- 输出平均 age、平均活跃物种、灭绝物种总数、平均物种人口、活跃文明相关统计、平均事件数和事件类型计数。
- Interesting runs 会列出活跃物种最多、活跃文明最多、物种人口最高、事件最多和灭绝事件最多的 run。
- 提供 `--out` 时会生成 Markdown 汇总报告。
