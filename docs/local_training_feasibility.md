# 本机 LoRA 训练可行性与工作量评估

> 评估时间：2026-11-06 14:43 ｜ 方法：本机实测（nvidia-smi、WMI/CIM、Python 包探测、网络连通性、目录扫描）+ 对照 `Gordon_Hunt_style_research_and_LoRA_plan.md` 的训练基线
> 性质：只读评估，未安装、未修改任何环境，未启动训练。

---

## 0. 一句话结论

**本机不能按现有方案训练，退到 SD 1.5 也不可行。** 唯一显卡是 GTX 1060 **3GB**，而方案基线要求 SDXL 1024 ≥ 12 GB、FLUX ≥ 24 GB；即使降到 SD 1.5 / 512，业界最低也要 4–6 GB。这是硬件硬门槛，**不是调参、换优化器或降分辨率能补上的**。

推荐分工：**本机负责数据准备、标注、质检、评估打分与文档；训练放云 GPU（24 GB 卡，约 ¥1–2/时）**。本机无法承担训练与权重验证。

---

## 1. 实测环境

| 项 | 实测值 | 判断 |
|---|---|---|
| GPU | NVIDIA GeForce **GTX 1060 3GB**（Pascal GP106, sm_61） | 无 Tensor Core、不支持 bf16 |
| 显存 | 3072 MiB 总量，**当前已用 2736 MiB**（约 330 MiB 空闲） | 桌面程序占满，GPU 利用率 95%、温度 81°C |
| 驱动 / CUDA | 560.94 / CUDA 12.6 | 驱动够新，但显存与架构不够 |
| CPU | Intel i7-7700 @3.60GHz，4 核 8 线程 | 够做数据处理，不够做训练 |
| 内存 | 15.93 GB 总量，**当前空闲仅 3.54 GB** | 连 latent 缓存都吃紧 |
| 磁盘 | C: 23.6 GB 可用；D: 135.3 / E: 192.8 / F: 143.7 GB 可用 | C 盘偏紧，大模型应放 D/E/F |
| 系统 | Windows 10 专业版 19045 | — |
| 主 Python | 3.13.14（pip 26.1.2） | **torch / accelerate / diffusers / transformers / xformers / bitsandbytes / Pillow / numpy / safetensors 全部缺失** |
| 其它 Python | `py -0p` 可见 3.13 / 3.12 / 3.11 / 3.7 / 3.6；`uv 0.11.19` 可用 | 3.11 适合 Kohya，建独立 venv 很方便 |
| CUDA Toolkit | 无 `nvcc` | 训练不需要编译即可跑（wheel 自带 runtime），但 xformers/triton 需预编译包 |
| **已有可用环境** | `/d/ComfyUI/.venv` → **torch 2.6.0+cu126，`cuda available = True`** | 可复用 CUDA 栈，省去装 PyTorch |
| **已有底模** | `/d/ComfyUI/models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors`（2.0 GB，SD 1.5 fp16） | 无 SDXL、无 FLUX 底模 |
| 训练器 | Kohya sd-scripts / AI-Toolkit 均未安装 | 需补 |
| 数据集 | `dataset/` 下只有 `.gitkeep`、README、manifest 模板，**0 张训练图** | 最大瓶颈，与硬件无关 |
| 网络 | huggingface.co ❌、civitai.com ❌；**hf-mirror.com ✅、github.com ✅、pypi.org ✅** | 底模/数据集需走镜像或国内源 |
| WSL | **被安全策略禁止启动**（程序黑名单） | 不能作为 Linux 训练栈备选；按提示，如需使用须由用户在安全中心自行移除黑名单 |

> 显存占用来自浏览器（Edge / Chrome）、QQ、微信、CodeBuddy、WorkBuddy、Epic/Steam 客户端与一个正在运行的游戏；即便全部关闭，物理上限仍是 3 GB。

---

## 2. 可行性评分量表

| 维度 | 权重 | 得分 | 依据 |
|---|---|---|---|
| 显存充足度 | 30 | **0** | 3 GB < SDXL 12 GB / SD1.5 4–6 GB / FLUX 24 GB |
| GPU 架构与算力 | 15 | **1** | Pascal sm_61，无 Tensor Core、无 bf16，仅能低效 fp16 |
| 内存与磁盘 | 10 | **5** | 16 GB RAM 但仅 3.5 GB 空闲；C 盘紧、D/E/F 充足 |
| 软件栈就绪度 | 15 | **6** | 有 torch cu126、uv、Python 3.11 可复用；训练栈全缺 |
| 底模与资源获取 | 10 | **5** | 本地有 SD1.5；HF/Civitai 不通但镜像与 PyPI 可达 |
| 训练数据就绪度 | 20 | **0** | 0 / 80 张，且授权路径未定 |
| **合计** | **100** | **17** | **不可行** |

| 总分区间 | 判定 |
|---|---|
| ≥ 75 | 可在本机直接启动训练 |
| 50–74 | 补齐环境 / 降级分辨率后可行 |
| **< 50** | **必须外置算力**（本机落在 17） |

> 注意：即使显存问题被解决，数据就绪度仍是 0 分。硬件与数据是两条独立瓶颈，先解决哪条都不影响另一条。

---

## 3. 为什么是硬门槛

| 训练配置 | 最低显存（业界常见基线） | 本机 |
|---|---|---|
| SDXL LoRA 1024（本方案 Phase A） | **≥ 12 GB**（16–24 GB 更稳） | 3 GB ❌ |
| FLUX.1-dev / FLUX.2 LoRA（Phase B） | **≥ 24 GB**（FLUX.2 建议 48 GB） | 3 GB ❌ |
| SD 1.5 LoRA 512（极限降级） | **4–6 GB**，且需 fp16 + gradient checkpointing + 8bit 优化器 + batch 1 | 3 GB ❌ |

额外三点：
- **当前实际可用显存约 330 MiB**，连加载 SD 1.5 UNet 都不够，更谈不上反向传播。
- **架构限制**：GTX 1060 无 Tensor Core，fp16 训练吞吐极低，bf16 完全不可用；`bitsandbytes` 8bit 优化器在 sm_61 上支持有限，而它正是低显存方案的关键组件。
- **内存连锁**：空闲 RAM 仅 3.54 GB，`cache_latents`、数据加载与系统盘交换都会互相挤占，OOM 风险从 GPU 蔓延到主机。

结论：**A 方案（本机硬上）不建议尝试**，投入产出比极差——即便勉强跑通，也只能得到分辨率 512、dim 8、风格细节严重损失的次品，且需要用户关闭全部日常程序数小时。

---

## 4. 工作量分解

| 阶段 | 任务 | 人工耗时 | 机时 | 本机可做 | 阻塞项 |
|---|---|---|---|---|---|
| P0 | 确定授权路径（A 授权 / B 研究 / C 抽象重绘） | 0.5–2 h（授权等待另计，可能数天） | — | ✅ | 版权合规 |
| P1 | 采集 80 张、裁左下角签名、去陈设图、多版次去重、分辨率筛选 | **6–10 h** | — | ✅ | 素材来源 |
| P2 | 80 条 caption 编写 + 逐条复核（含局部特写组 texture-state） | **3–5 h** | — | ✅ | 人工判断 |
| P3 | 跑 `audit_dataset.py`、装 Pillow、整理 manifest 与验证集 | 1 h | — | ✅ | Pillow 未装 |
| P4 | 云端建环境：Kohya sd-scripts + 依赖 + 底模（SDXL ~6.9 GB） | 1–2 h | 0.5 h | ⚠️ 脚本可本机写好 | 云端账号 |
| P5 | 40 步 smoke test → 正式训练 ~1800 步 | 0.5 h | **1.5–4 h** | ❌ | 外置算力 |
| P6 | 评估网格（3 权重 × 14 prompt × 多 ckpt）+ 六维打分 | **2–4 h** | 0.5–1 h | ✅ 打分；❌ 出图 | 外置算力 |
| P7 | 依据评分做 v2 消融（另计） | — | — | — | — |
| **合计** | | **约 14–24 h 人工** | **约 4–8 h 机时** | | |

**成本量级**（2026-10/11 公开报价，以平台控制台实时价为准）：

| 平台 / 卡型 | 参考价 | 4–8 机时 |
|---|---|---|
| 国内 RTX 3090 24GB | ¥0.72–1.56 / 时（AutoDL 官网 ¥1.32） | **约 ¥3–13** |
| 国内 RTX 4090 24GB | ¥1.24–1.98 / 时（AutoDL 官网 ¥1.98） | **约 ¥5–16** |
| RunPod RTX 3090 / 4090 | $0.50 / $0.69 每小时（2026-08 官方价） | 约 $2–6 |

> 相比买卡，租卡成本可忽略；**真正的工作量在 P0–P2（数据与授权，约 10–17 小时人工），不在算力**。

---

## 5. 路径对比

| 路径 | 可行性 | 成本 | 主要代价 | 建议 |
|---|---|---|---|---|
| **A 本机硬上**（SD1.5 / 512 / 极限省显存） | ❌ 不可行 | ¥0 | 需关闭全部桌面程序，仍大概率 OOM；训练数十小时且风格细节丢失 | 放弃 |
| **B 云 GPU**（推荐） | ✅ | ¥5–20 / 轮 | 需上传数据集、云端搭一次环境 | **首选**：AutoDL / 恒源云 / 算家云 的 3090 或 4090（24GB），生态镜像多、按量计费 |
| **C 在线训练服务**（Shakker / MimicPC / Civitai） | ⚠️ 技术可行 | 约 $1.19/次起 | **需把受版权保护的作品上传到第三方**，控制粒度低、数据不可控 | 不推荐（合规风险） |
| **D 升级本机硬件** | ✅ | 一次性数千元 | 需 ≥12GB 显存（SDXL 768 可跑）/ 24GB 更稳；还需 PSU 与散热余量 | 仅当长期高频训练才划算 |

> B 路径里，本机仍承担 P0–P3 与 P6 的人工环节；云端只承担训练与出图。

---

## 6. 本机能 / 不能承担的工作

| ✅ 本机可做 | ❌ 本机不可做 |
|---|---|
| 授权决策、素材整理、裁签名、去重（P0–P1） | SDXL / FLUX LoRA 训练 |
| 80 条 caption 编写与复核（P2） | 加载 SDXL / FLUX 权重做推理验证 |
| `audit_dataset.py` 质检、manifest 溯源（P3） | 训练期采样、checkpoint 对比 |
| 评估量表打分、文档与版本管理（P6–P7） | 任何需要 bf16 / Tensor Core 的环节 |
| SD 1.5 512 出图（ComfyUI，可用于参考） | — |

> 现有 `configs/train_sdxl.sh` 与 `dataset_sdxl.toml` 可直接搬到云端 Linux 实例（路径用 `@PROJECT_ROOT@` 占位，无本机绑定），只需把 `SD_SCRIPTS` / `BASE_MODEL` 指向云端路径。

---

## 7. 推荐执行顺序

1. **先定授权路径**（否则后面所有工作都可能白做）。建议 C「要素抽象重绘」或 B「非商业研究」，商用一律走 A。
2. **本机完成 P1–P3**：采图清洗 → 标注 → 装 Pillow → `python tools/audit_dataset.py --root dataset` 全绿。
3. **开一台 24GB 云实例**（优先带 Kohya / PyTorch 预置镜像），把 `dataset/` 与 `configs/` 上传；底模走平台镜像或 hf-mirror，避免直连 huggingface.co。
4. **先跑 `STEPS=40` smoke test**，确认 caption 命中数 == 图片数、样本正常、ckpt 能打开。
5. **正式训练**，每 200 步存 ckpt，用 `prompts/eval_grid.txt` 固定种子采样。
6. **下载权重与样本到本机**，按 `eval/scorecard.csv` 人工打分，选最早「风格到位且仍听话」的 ckpt。
7. **把实验记录与结论提交回仓库**，再按第 11 节做 v2 消融。

---

## 8. 风险与注意事项

- **版权**：画家在世、作品在保护期内。路径 C 会把数据上传到第三方平台，合规风险最高，不建议。详见主方案第 10 节。
- **网络**：huggingface.co 与 civitai.com 实测不通；底模与依赖请走 `hf-mirror.com`、`pypi.org` 或云平台预置镜像。
- **磁盘**：C 盘只剩 23.6 GB。若坚持在本机下载 SDXL 底模做验证，务必放到 D/E/F 盘。
- **WSL**：被安全策略列入程序黑名单，本次评估未重试、未绕行；若日后需要 Linux 训练栈，需由用户在安全中心自行处理。
- **数据才是主瓶颈**：即使明天换上 4090，`dataset/` 仍是 0 张，P0–P2 的 10–17 小时人工一分都省不掉。
- **温度**：评估时 GPU 81°C / 风扇 75%，长时间高负载前建议检查散热；这也侧面说明本机不适合再叠加训练负载。

---

## 附录：实测依据

| 检查项 | 命令 / 来源 |
|---|---|
| GPU、显存占用、驱动、CUDA | `nvidia-smi`（2026-11-06 14:43） |
| GPU 型号、内存、CPU、磁盘 | `Get-CimInstance Win32_VideoController / Win32_ComputerSystem / Win32_Processor / Win32_LogicalDisk` |
| Python 包与 torch/cuda | `python -c importlib...`；`/d/ComfyUI/.venv/Scripts/python.exe -c "import torch..."` |
| Python 版本清单 | `py -0p`、`uv --version` |
| 网络 | `curl -m 12 -o /dev/null -w "%{http_code}"` 对 5 个站点 |
| 训练基线 | 主方案第 6 节；2026 Kohya / AI-Toolkit 训练实践公开资料 |
| 云 GPU 报价 | AutoDL 官网、rentgpu.link 2026-10 抓取数据、RunPod 2026-08 官方价（均需以实时报价为准） |
