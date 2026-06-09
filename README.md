# Universe Evolution Lab

多宇宙文明演化实验室。

Universe Evolution Lab 是一个命令行 MVP，用于创建、运行、观察、分支、导出和批量比较虚拟宇宙、生命、文明演化实验。当前重点是小规模、可读、可扩展的本地模拟，不引入复杂依赖。

## 当前定位

- 命令行优先，所有功能通过 `python -m universe_lab.main` 使用。
- 标准库优先，模拟与报告生成不依赖第三方运行时库。
- 观察优先，用户可以创建、推进、查看、分支、导出、比较和批量汇总实验。
- 模拟规则保持轻量，当前只覆盖基础生命和文明演化。

## 支持模式

- `life_burst`：生命大爆炸模式，初始生成多个生命种子，观察生命种群自然演化。
- `civilization_seeds`：文明种子模式，初始生成 3 个原始文明，观察文明发展、衰退或崩溃。
- `minimal_observer`：最小干预观察模式，只允许创建、运行、查看、复制分支和导出观察结果，不提供直接修改生命或文明命运的命令。

## 安装

```bash
git clone <your-repo-url>
cd universe-evolution-lab
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

项目运行代码只使用 Python 标准库。`requirements.txt` 主要用于测试和代码检查。

## 快速开始

```bash
.venv/bin/python -m universe_lab.main create --mode life_burst --name demo_life
.venv/bin/python -m universe_lab.main step --run data/runs/demo_life.json --steps 20
.venv/bin/python -m universe_lab.main show --run data/runs/demo_life.json
.venv/bin/python -m universe_lab.main stats --run data/runs/demo_life.json
.venv/bin/python -m universe_lab.main timeline --run data/runs/demo_life.json --limit 10
```

如果你的系统中 `python` 指向 Python 3，也可以使用：

```bash
python -m universe_lab.main create --mode life_burst --name demo_life
```

## CLI 命令

创建宇宙：

```bash
.venv/bin/python -m universe_lab.main create --mode life_burst --name test_life
.venv/bin/python -m universe_lab.main create --mode civilization_seeds --name test_civ
.venv/bin/python -m universe_lab.main create --mode minimal_observer --name test_observer
```

推进回合：

```bash
.venv/bin/python -m universe_lab.main step --run data/runs/test_life.json --steps 10
```

查看当前状态：

```bash
.venv/bin/python -m universe_lab.main show --run data/runs/test_life.json
```

统计当前状态：

```bash
.venv/bin/python -m universe_lab.main stats --run data/runs/test_life.json
```

查看事件时间线：

```bash
.venv/bin/python -m universe_lab.main timeline --run data/runs/test_life.json
.venv/bin/python -m universe_lab.main timeline --run data/runs/test_life.json --limit 20
```

复制平行分支：

```bash
.venv/bin/python -m universe_lab.main branch --run data/runs/test_life.json --name test_life_branch
```

导出分析 JSON：

```bash
.venv/bin/python -m universe_lab.main export --run data/runs/test_life.json --out data/runs/test_life_export.json
```

生成 Markdown 报告：

```bash
.venv/bin/python -m universe_lab.main report --run data/runs/test_life.json --out docs/test_life_report.md
```

比较两个宇宙或分支：

```bash
.venv/bin/python -m universe_lab.main compare --run-a data/runs/test_life.json --run-b data/runs/test_life_branch.json
```

批量实验：

```bash
.venv/bin/python -m universe_lab.main batch --mode life_burst --count 5 --steps 20 --prefix batch_life
```

批量汇总：

```bash
.venv/bin/python -m universe_lab.main summary --runs data/runs --prefix batch_life
.venv/bin/python -m universe_lab.main summary --runs data/runs --prefix batch_life --out docs/batch_life_summary.md
```

更多说明见 [docs/usage.md](docs/usage.md)。

## 测试和检查

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests
```

## 当前不包含

当前版本不包含：

- VR 或 3D 体验
- 网页应用
- AI API 接入
- 造物主主线
- 外层真实世界设定
- 终极文明或预设文明终点

这些方向可能作为未来扩展讨论，但不属于当前 CLI MVP 的核心范围。
