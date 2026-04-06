# 植物成长模拟能力包

这个文档记录了当前已经编入 Ecology Harness 的植物、作物与微生物成长模拟能力层。

## 已安装 Skills

- `plant-growth-model-selection`
  - 用途：在真正建模前先选对模型家族
- `crop-growth-simulation-workflow`
  - 用途：作物物候、生物量、产量、灌溉与农业系统情景分析
- `crop-water-and-irrigation-simulation`
  - 用途：水分平衡、蒸散、灌溉与干旱胁迫建模
- `functional-structural-plant-modeling`
  - 用途：根系、枝条、器官发育与功能结构植物模型
- `root-and-rhizosphere-architecture-modeling`
  - 用途：根系结构、根际几何和根系参数化工作流
- `woody-plant-and-forest-simulation`
  - 用途：森林、灌丛、木本植物和林分干旱响应建模
- `microbial-growth-and-community-simulation`
  - 用途：微生物增长、群落代谢与反应器动力学
- `microbial-community-metabolism-simulation`
  - 用途：微生物群落代谢、资源竞争与交叉喂养建模
- `microbial-biofilm-and-reactor-simulation`
  - 用途：生物膜、扩散梯度、反应器与多过程微生物模拟
- `microbiome-timeseries-and-benchmark-simulation`
  - 用途：纵向微生物组推断与 benchmark 数据生成
- `plant-soil-microbe-coupled-simulation`
  - 用途：植物、土壤、养分与微生物耦合建模
- `growth-model-calibration-and-validation`
  - 用途：参数估计、敏感性、不确定性与验证设计

## 已编目的外部 Toolkits

- `APSIM Next Generation`
  - 仓库：https://github.com/APSIMInitiative/ApsimX
  - 选择原因：很强的农业系统框架，适合管理、轮作和系统级情景分析
- `PCSE / WOFOST`
  - 仓库：https://github.com/ajwdewit/pcse
  - 选择原因：Python 原生、很适合作物生长与产量模拟
- `AquaCrop-OSPy`
  - 仓库：https://github.com/aquacropos/aquacrop
  - 选择原因：特别适合灌溉、干旱和水分受限生长问题
- `BioCro`
  - 仓库：https://github.com/biocro/biocro
  - 选择原因：适合显式冠层光合、生理过程和机理性作物生长问题
- `pyfao56`
  - 仓库：https://github.com/kthorp/pyfao56
  - 选择原因：很适合 FAO-56 风格的蒸散、灌溉和土壤水分平衡分析
- `CPlantBox`
  - 仓库：https://github.com/Plant-Root-Soil-Interactions-Modelling/CPlantBox
  - 选择原因：很适合 3D 根-茎结构和植物-土壤互作
- `OpenAlea L-Py`
  - 仓库：https://github.com/openalea/lpy
  - 选择原因：成熟的 L-system 植物结构建模环境
- `r3PG`
  - 仓库：https://github.com/trotsiuk/r3PG
  - 选择原因：适合森林、木本和人工林生产力与林分生长问题
- `medfate`
  - 仓库：https://github.com/emf-creaf/medfate
  - 选择原因：适合木本植被水分平衡、植物水力和干旱响应研究
- `pyrealm`
  - 仓库：https://github.com/ImperialCollegeLondon/pyrealm
  - 选择原因：适合把环境因子、生产力和生态生理过程串起来
- `COBRApy`
  - 仓库：https://github.com/opencobra/cobrapy
  - 选择原因：微生物代谢增长模拟的基础框架
- `MICOM`
  - 仓库：https://github.com/micom-dev/micom
  - 选择原因：适合微生物群落代谢和 cross-feeding
- `COMETS`
  - 仓库：https://github.com/segrelab/comets
  - 选择原因：适合带扩散和代谢交换的微生物群落模拟
- `BacArena`
  - 仓库：https://github.com/euba/BacArena
  - 选择原因：适合把微生物个体和代谢交换同时显式表示出来
- `Community Simulator`
  - 仓库：https://github.com/Emergent-Behaviors-in-Biology/community-simulator
  - 选择原因：适合资源竞争和群落组装导向的微生物生态问题
- `Tellurium`
  - 仓库：https://github.com/sys-bio/tellurium
  - 选择原因：很适合 SBML/ODE 风格的机理增长模型
- `COPASI`
  - 仓库：https://github.com/copasi/COPASI
  - 选择原因：成熟的动态系统与参数拟合平台
- `PySCeS`
  - 仓库：https://github.com/PySCeS/pysces
  - 选择原因：Python 原生的动力学建模方案
- `NUFEB`
  - 仓库：https://github.com/nufeb/NUFEB
  - 选择原因：适合三维空间、生物膜和颗粒系统中的微生物模拟
- `Vivarium Core`
  - 仓库：https://github.com/vivarium-collective/vivarium-core
  - 选择原因：适合多过程组合、自定义微生物生理和混合模拟
- `MDSINE2`
  - 仓库：https://github.com/gerberlab/MDSINE2
  - 选择原因：适合有时间序列的微生物群落动态问题
- `miaSim`
  - 仓库：https://github.com/microbiome/miaSim
  - 选择原因：适合生成微生物组 benchmark 数据和扰动情景
- `pyPESTO`
  - 仓库：https://github.com/ICB-DCM/pyPESTO
  - 选择原因：很强的参数估计、不确定性和敏感性分析工具

## 按植物类型划分

- 一年生与大田作物
  - 推荐：`AquaCrop-OSPy`、`PCSE / WOFOST`、`BioCro`、`APSIM Next Generation`、`DSSAT Cropping System Model`
  - 适用：物候、产量、冠层生理、灌溉和管理情景

- 灌溉与水分平衡
  - 推荐：`pyfao56`、`AquaCrop-OSPy`
  - 适用：蒸散、灌溉制度、亏缺胁迫和土壤水分核算

- 根系、根际与结构植物模型
  - 推荐：`CPlantBox`、`OpenAlea L-Py`
  - 适用：显式根系结构、分枝、三维几何和根际过程

- 木本、林分、森林和灌丛
  - 推荐：`r3PG`、`medfate`、`ED2`、`LPJ-GUESS`、`LANDIS-II`
  - 适用：树木生长、林分动态、木本干旱响应、长期森林变化

## 微生物模拟家族

- 群落代谢与交叉喂养
  - 推荐：`MICOM`、`COMETS`、`BacArena`、`COBRApy`

- 资源竞争与群落组装
  - 推荐：`Community Simulator`

- 生物膜、反应器和空间梯度
  - 推荐：`NUFEB`、`Tellurium`、`COPASI`、`PySCeS`、`Vivarium Core`

- 时间序列微生物组与 benchmark
  - 推荐：`MDSINE2`、`miaSim`、`pyPESTO`

## MCP 使用策略

目前没有找到同等成熟、又明显适合直接默认接入的“植物成长模拟专用 MCP
server”。这一层更稳的做法是继续复用现有科研 MCP 作为执行骨架：

- `jupyter-mcp`：执行 notebook、画图、跑模拟脚本
- `labarchives`：保存实验记录、假设和结果出处
- `unit-converter`：统一输入参数和观测数据单位
- `weather-open-meteo`、`nasa`：补天气、气候和 forcing 数据

## 示例 Prompt

```text
/plant-growth-model-selection 玉米干旱加灌溉处理的成长模拟
/crop-growth-simulation-workflow 水稻在高温和晚播情景下的产量变化
/crop-water-and-irrigation-simulation 玉米亏缺灌溉和蒸散核算
/functional-structural-plant-modeling 磷限制下的根系结构模拟
/root-and-rhizosphere-architecture-modeling 土柱实验中的根系分枝与根际结构
/woody-plant-and-forest-simulation 人工林生产力和干旱死亡风险
/microbial-growth-and-community-simulation 根际菌群在碳脉冲条件下的互作模拟
/microbial-community-metabolism-simulation 扩散受限条件下菌群交叉喂养
/microbial-biofilm-and-reactor-simulation 脉冲营养输入下的生物膜发育
/microbiome-timeseries-and-benchmark-simulation 纵向微生物组扰动 benchmark 数据
/plant-soil-microbe-coupled-simulation 盆栽系统中作物根系、土壤水分和硝化菌耦合
/growth-model-calibration-and-validation 用多季观测数据拟合作物增长与产量参数
```
