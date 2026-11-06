# Gordon Hunt 风格 LoRA · 项目入口

把「离散光斑 + 白色焦散细线 + 冷底暖点 + 平面化剪影」这套海景视觉语言，做成可控、可评估的风格 LoRA。

> 📄 **核心文档**：`docs/Gordon_Hunt_style_research_and_LoRA_plan.md`
> 包含风格解构六维表、数据集配比、caption 规范、超参基线、评估量表、合规边界与迭代路线。

## 三条先读结论

1. **不是水彩，是丙烯**（box canvas）。别在数据/提示里写 `watercolor`。
2. **左下角签名必须裁掉**，同一作品的多个限量版尺寸必须去重。
3. **画家在世、作品在版权期内**。**P0 已锁定为路径 B（非商业个人研究）**，见下节；商用或发布权重须另走授权。

## 当前决策：P0 = B（非商业个人研究）

> 2026-11-06 锁定。依据主方案第 4.1 / 第 10 节（英国 `CDPA 1988 s.29A`：合法访问 + 纯非商业研究 + 充分署名）。操作规范见 `docs/P1_collection_spec.md`。

| ✅ 允许 | ❌ 禁止 |
|---|---|
| 本机或**自己控制的云实例**上做私人实验 | 商用、出售、接单、广告、带品牌名的产品 |
| 从允许访问的公开页面逐张保存并登记来源 | 公开数据集、上传公共数据集平台、打包分发 |
| 生成仅供自己评估的样本 | 发布 LoRA 权重、生成样图，或在公开仓库里放作品图 |
| 仓库内保留文档、代码与**空台账模板** | 绕过付费墙、绕过 robots 或站点禁止抓取声明批量扒图 |

**因此这个公开仓库只放文档与代码**：`.gitignore` 已排除 `dataset/` 图片与 caption、`output/` 权重、`samples/` 样图；填入真实来源链接的台账写进 `dataset/manifest.local.csv`（已忽略），不要覆盖并提交 `dataset/manifest.csv` 模板。

云 GPU 说明：把数据上传到自己控制的计算实例用于训练，不等于向公众分发，但须选可信平台、训练完删除实例内数据、不用公开共享镜像承载数据集。**路径 C「在线训练服务」仍需把受版权作品交给第三方且控制粒度低，继续不推荐**。若日后要商用或发布权重，必须重新走 **A 书面授权**或改用 **C 抽象重绘**，不要沿用 B 下训练出的权重。

> 以上为工程风险管理提示，不构成法律意见。

## 目录

```
LoRA/
├── README.md                                   ← 你在这里
├── docs/Gordon_Hunt_style_research_and_LoRA_plan.md   ← 主方案
├── configs/
│   ├── dataset_sdxl.toml                       Kohya 数据集配置
│   ├── train_sdxl.sh                           SDXL 训练启动脚本
│   └── train_flux_ai-toolkit.yaml              FLUX 备选模板
├── prompts/
│   ├── eval_grid.txt                           四类评估网格 + 推理/负面模板
│   └── sample_prompts.txt                      训练期固定采样提示
├── dataset/
│   ├── README.md                               授权与目录规范
│   ├── collection_plan.template.csv            采集清单模板（复制后填，不提交）
│   ├── manifest.csv                            台账模板（真实台账写 manifest.local.csv）
│   ├── _inbox/                                 原始下载图（gitignored）
│   ├── 10_full/  3_dabs/  3_filaments/         训练分组（数字=repeats）
│   └── val/                                    验证集，不参与训练
├── tools/
│   ├── clean_dataset.py                        P1 批量清洗（默认 dry-run）
│   ├── caption_vocab.md                        标注词表与示例
│   └── audit_dataset.py                        数据集质检脚本
├── eval/scorecard.csv                          结构化评分表
├── output/                                     权重与日志
└── samples/                                    采样输出
```

## 快速开始（5 步）

| # | 动作 | 命令 / 文件 |
|---|---|---|
| 1 | ~~确定授权路径~~ **已定 B**：逐张另存到 `dataset/_inbox/`、填采集清单，再跑批量清洗 | `docs/P1_collection_spec.md` 第 3.1 节；`tools/clean_dataset.py`（默认 dry-run，`--apply` 才写入） |
| 2 | 按分组放图 + 同名 `.txt` caption，填溯源台账 | `tools/caption_vocab.md`、`dataset/manifest.csv` |
| 3 | 质检必须全绿 | `python tools/audit_dataset.py --root dataset` |
| 4 | 先跑 40 步 smoke test，再跑正式训练 | `configs/train_sdxl.sh`（改 `--max_train_steps=40`） |
| 5 | 用评估网格给每个 checkpoint 打分，选最早「风格到位且仍听话」的权重 | `prompts/eval_grid.txt`、`eval/scorecard.csv` |

## 依赖与环境

- Python 3.10+；质检脚本的**图像级检查**需要 `Pillow`（`pip install Pillow`），缺失时脚本仍会完成结构与 caption 检查并提示。
- 训练：Kohya `sd-scripts`（SDXL / FLUX.1）或 `AI-Toolkit`（FLUX.2 / Qwen-Image）。
- 显存：SDXL 1024 建议 16–24 GB；12 GB 可降到 768；FLUX.2 建议 48 GB。
- Windows 用户：`configs/train_sdxl.sh` 在 Git Bash 下运行；路径已用正斜杠写法。
- 路径配置：仓库内不含任何本机绝对路径。`SD_SCRIPTS` / `BASE_MODEL` 用环境变量或编辑脚本设置；配置模板里的 `@PROJECT_ROOT@` 由 `train_sdxl.sh` 自动替换成本地路径并生成 gitignored 的 `configs/dataset_sdxl.local.toml`。

## 扩展接口

方案已预留：拆分「纹理 LoRA / 构图 LoRA」、分题材子 LoRA、迁移 FLUX.2、DoRA/LoHa 消融、ControlNet 组合、自动早停。详见主方案第 11 节。

> 本仓库文档为技术研究资料，不构成法律意见；商用、发布权重或对外服务前请确认授权。
