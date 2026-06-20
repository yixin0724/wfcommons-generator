# wfcommons-generator

![Tests](https://github.com/yixin0724/wfcommons-generator/actions/workflows/tests.yml/badge.svg)

`wfcommons-generator` 是一个基于 [WfCommons](https://wfcommons.org/) 的工作流实例生成项目，用于生成可复现的 WfFormat JSON 工作流数据，方便后续接入调度器、仿真器或分析脚本。

## 功能特点

- 支持 `montage`、`epigenomics`、`seismology`、`genome`、`cycles`、`soykb`、`srasearch` 七类 WfCommons recipe。
- 支持按工作流类型、请求任务规模、每个规模实例数量批量生成 JSON。
- 支持 WfCommons 官方的 runtime、输入文件大小、输出文件大小缩放参数，以及基础图排除参数。
- 使用稳定随机种子，相同参数可以复现同一路径下的工作流实例。
- 核心生成逻辑放在 `wfcommons_generator/` 包中，命令行入口放在 `scripts/` 目录中。
- 默认将生成结果写入 `data/wfcommons/`，生成产物与源码分离。
- 提供 JSON 检查命令，用于快速查看任务数、边数、文件数和部分依赖边。

## 项目结构

```text
wfcommons_generator/
  __init__.py
  core.py                         核心生成逻辑，可被其他 Python 代码复用
scripts/
  generate_wfcommons_instances.py 生成工作流实例的命令行入口
  inspect_wfcommons_json.py       JSON 结构检查入口
tests/                            Pytest 测试
data/
  README.md                       生成实例目录说明
  wfcommons/                      默认生成输出目录，默认不提交到 Git
.github/workflows/tests.yml       GitHub Actions 测试流程
pyproject.toml                    Python 包配置
requirements.txt                  基础依赖
```

生成的 workflow JSON 文件可能比较大。本仓库默认版本管理源码、测试和文档；`data/wfcommons/` 被 `.gitignore` 忽略，建议需要时在本地重新生成。如果后续要公开数据集，更适合使用 GitHub Release artifact 或单独的数据仓库。

## 支持的工作流类型

```text
montage       天文图像拼接类工作流
epigenomics   生物信息/表观基因组类工作流
seismology    地震数据处理类工作流
genome        基因组处理类工作流
cycles        Cycles 工作流
soykb         SoyKB 生物信息类工作流
srasearch     SRA Search 工作流
```

WfCommons 不是只支持固定规模。`--sizes` 可以传入任意整数规模，但必须大于等于对应 recipe 的最低请求规模。常用建议规模可以使用：

```text
100
300
500
1000
```

其中 `100` 不适用于最低规模大于 100 的 recipe，例如 `seismology`。为了让默认命令对全部支持 recipe 都可用，本项目默认规模为：

```text
300
500
1000
```

默认每个工作流类型、每个规模生成 5 个实例，所以完整默认数据集为：

```text
7 workflow types * 3 sizes * 5 instances = 105 JSON files
```

注意：`--sizes` 表示请求任务数。WfCommons 可能因为 recipe 结构约束产生略有差异的实际任务数，命令行输出会同时显示 `requested_tasks` 和 `actual_tasks`。如果请求规模低于下表中的最低下限，程序会直接报错，不会自动放大规模生成。

下表中的最低请求规模来自当前项目依赖的 WfCommons 1.4 recipe 基础图限制；它不是可生成规模的固定枚举，只是每类 recipe 的请求下限。

| workflow type | 最低请求规模 |
|---|---:|
| `cycles` | 69 |
| `epigenomics` | 43 |
| `genome` | 54 |
| `montage` | 60 |
| `seismology` | 103 |
| `soykb` | 98 |
| `srasearch` | 24 |

## 输出结构

默认输出路径：

```text
data/wfcommons/{workflow_type}/{requested_size}/{workflow_type}_{requested_size}_{instance_id}.json
```

示例：

```text
data/wfcommons/montage/100/montage_100_000.json
data/wfcommons/genome/1000/genome_1000_004.json
```

JSON 内容是 WfCommons WfFormat，主要包含：

```text
workflow.specification.tasks      任务、父子依赖、输入输出文件
workflow.specification.files      文件及 sizeInBytes
workflow.execution.tasks          每个任务的 runtimeInSeconds
```

## 环境准备

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

开发模式安装：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

## 生成工作流实例

生成全部默认数据集：

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py
```

只生成一个 `montage` 的 100 规模实例：

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py --workflow-types montage --sizes 100 --instances-per-size 1
```

生成 `montage` 和 `genome`，规模为 100、500、1000：

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py --workflow-types montage genome --sizes 100 500 1000
```

生成新增的 `cycles`、`soykb`、`srasearch`：

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py --workflow-types cycles soykb srasearch --sizes 100 300 --instances-per-size 1
```

输出到自定义目录：

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py --output-dir data\wfcommons_custom
```

指定随机种子基准：

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py --seed-base 20260516
```

使用 WfCommons 官方缩放参数：

```powershell
.\.venv\Scripts\python.exe scripts\generate_wfcommons_instances.py --workflow-types montage --sizes 300 --runtime-factor 1.5 --input-file-size-factor 2.0 --output-file-size-factor 0.5
```

安装为可编辑包后，也可以直接使用命令名：

```powershell
.\.venv\Scripts\wfcommons-generate.exe --workflow-types montage --sizes 100 --instances-per-size 1
```

## 参数说明

```text
--output-dir
    输出根目录。默认 data/wfcommons。

--workflow-types
    要生成的工作流类型列表。可选 cycles epigenomics genome montage seismology soykb srasearch。
    默认生成全部类型。

--sizes
    请求任务规模列表。可传任意大于等于对应 recipe 最低下限的整数。
    默认 300 500 1000。

--instances-per-size
    每个 workflow type 和 size 组合生成几个实例。默认 5。

--seed-base
    随机种子基准。默认 20260516。

--exclude-graphs
    WfCommons 基础图排除列表。通常无需设置。

--runtime-factor
    WfCommons runtime 缩放因子，必须大于 0。默认 1.0。

--input-file-size-factor
    WfCommons 输入文件大小缩放因子，必须大于 0。默认 1.0。

--output-file-size-factor
    WfCommons 输出文件大小缩放因子，必须大于 0。默认 1.0。
```

这些参数对应 WfCommons 官方 `from_num_tasks` 接口中的 `exclude_graphs`、`runtime_factor`、`input_file_size_factor` 和 `output_file_size_factor`。

每个实例的实际 seed 计算方式：

```text
seed = seed_base + stable_offset(workflow_type) + requested_size * 1000 + instance_id
```

相同参数重复运行，会覆盖同路径文件，并生成可复现的实例。

## 检查生成结果

查看一个 JSON 的任务数、边数、文件数和部分任务/边：

```powershell
.\.venv\Scripts\python.exe scripts\inspect_wfcommons_json.py --workflow-json data\wfcommons\montage\100\montage_100_000.json
```

限制打印数量：

```powershell
.\.venv\Scripts\python.exe scripts\inspect_wfcommons_json.py --workflow-json data\wfcommons\montage\1000\montage_1000_000.json --limit 5
```

安装为可编辑包后，也可以直接使用命令名：

```powershell
.\.venv\Scripts\wfcommons-inspect.exe --workflow-json data\wfcommons\montage\100\montage_100_000.json --limit 5
```

## Python API

```python
from wfcommons_generator import generate_wfcommons_instances

for item in generate_wfcommons_instances(
    output_dir="data/wfcommons",
    workflow_types=["montage"],
    sizes=[100],
    instances_per_size=1,
    seed_base=20260516,
):
    print(item.path, item.actual_tasks)
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
```

GitHub Actions 会在 Python 3.10、3.11、3.12 上运行测试。
