# 生态过程模型能力包

这个文档记录了当前已经编入 Ecology Harness 的传统生态过程模型、主体模型、
流域模型和系统模拟能力层。

## 已安装 Skills

- `process-model-selection`
  - 用途：在真正建模前先选对过程模型家族
- `agent-based-ecology-modeling`
  - 用途：用 `NetLogo`、`Mesa`、`GAMA` 处理个体和主体生态模型
- `watershed-and-ecohydrology-modeling`
  - 用途：用 `SWAT+`、`RHESSys` 处理流域和生态水文问题
- `food-web-and-trophic-simulation`
  - 用途：用 `Ecopath with Ecosim` 处理食物网和营养级问题
- `forest-landscape-disturbance-modeling`
  - 用途：用 `LANDIS-II` 处理森林景观、火干扰和经营情景
- `terrestrial-biosphere-and-vegetation-modeling`
  - 用途：用 `LPJ-GUESS`、`ED2`、`Biome-BGC`、`CENTURY / DayCent` 处理陆地生态过程
- `model-calibration-and-sensitivity`
  - 用途：传统模拟器的校准、敏感性和不确定性分析
- `cross-model-scenario-comparison`
  - 用途：多模型情景比较和结果对齐

## 已编目的模型系统

- 第一批优先模型
  - `NetLogo`
  - `Mesa`
  - `GAMA Platform`
  - `DSSAT Cropping System Model`
  - `SWAT+`
  - `Ecopath with Ecosim`

- 第二梯队已可发现模型
  - `LPJ-GUESS`
  - `ED2`
  - `Biome-BGC`
  - `CENTURY / DayCent`
  - `RHESSys`
  - `LANDIS-II`
  - `Madingley Model`
  - `RangeShifter 2.0`

## 当前执行骨架

目前更稳的做法是：

- 把重型外部模型作为 cataloged toolkit 接入
- 用 `jupyter-mcp` 做输入整理、启动包装和后处理
- 用 `labarchives` 管实验记录和运行出处
- 用 `unit-converter` 统一单位后再做校准和比较
- 等本地安装更稳定后，再逐步补模型专用 runner tools

## 计划中的 Runner Surface

下一层最自然的工具接口包括：

- `RunNetLogoModel`
- `RunMesaScenario`
- `RunGamaScenario`
- `RunDSSATScenario`
- `RunSWATPlusProject`
- `RunEcopathScenario`
- `ParseModelOutputs`
- `CompareScenarioRuns`
- `BuildForcingDataset`

## 示例 Prompt

```text
/process-model-selection 恢复、放牧、火干扰和流域水文耦合问题
/agent-based-ecology-modeling 破碎化农田中传粉者移动和访花行为
/watershed-and-ecohydrology-modeling 施肥变化下的流域氮输出
/food-web-and-trophic-simulation 捕鱼压力变化下的沿海食物网响应
/forest-landscape-disturbance-modeling 温带森林火灾和采伐情景比较
/terrestrial-biosphere-and-vegetation-modeling 变暖下长期 NPP 和土壤碳响应
/model-calibration-and-sensitivity 用流量和硝酸盐观测校准流域模型
/cross-model-scenario-comparison 比较 DSSAT 和 APSIM 在热胁迫与灌溉情景下的输出
```
