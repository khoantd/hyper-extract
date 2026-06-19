# he analyze

对图结构知识图谱中的关键节点与高度连接节点进行排序分析。

---

## 用法

```bash
he analyze KA_PATH [OPTIONS]
```

## 参数

| 参数 | 说明 |
|------|------|
| `KA_PATH` | 知识抽象目录路径 |

## 选项

| 选项 | 说明 |
|------|------|
| `--top-k`, `-n` | 显示排名前 N 的节点（默认 10） |
| `--metric`, `-m` | `degree`、`betweenness` 或 `composite`（默认） |
| `--tier` | 仅显示指定层级（如 `critical`） |
| `--json` | 输出 JSON 格式 |

---

## 说明

通过图拓扑分析识别 **枢纽节点**（连接最多）与 **结构关键节点**（割点、高介数中心性，需安装 `networkx`）。

默认综合得分：

`importance = 0.6 × 归一化度 + 0.4 × 归一化介数`

适用于 `AutoGraph`、时空图变体及 `AutoHypergraph`。

---

## 示例

```bash
he analyze ./tesla_kb/
he analyze ./tesla_kb/ -n 5 --metric degree
he analyze ./tesla_kb/ --json
he show ./tesla_kb/
```

---

## 相关命令

- [`he show`](show.md) — 可视化（含关键节点侧栏）
- [`he info`](info.md) — 知识抽象统计信息
