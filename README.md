# Gordon Hunt 风格 LoRA · 项目入口

把「离散光斑 + 白色焦散细线 + 冷底暖点 + 平面化剪影」这套海景视觉语言，做成可控、可评估的风格 LoRA。

> 📄 **核心文档**：`docs/Gordon_Hunt_style_research_and_LoRA_plan.md`
> 包含风格解构六维表、数据集配比、caption 规范、超参基线、评估量表、合规边界与迭代路线。

## 三条先读结论

1. **不是水彩，是丙烯**（box canvas）。别在数据/提示里写 `watercolor`。
2. **左下角签名必须裁掉**，同一作品的多个限量版尺寸必须去重。
3. **画家在世、作品在版权期内**。商用需授权；默认按「非商业研究」或「要素抽象重绘」组织。

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
│   ├── manifest.csv                            逐图溯源台账（必填）
│   ├── 10_full/  3_dabs/  3_filaments/         训练分组（数字=repeats）
│   └── val/                                    验证集，不参与训练
├── tools/
│   ├── caption_vocab.md                        标注词表与示例
│   └── audit_dataset.py                        数据集质检脚本
├── eval/scorecard.csv                          结构化评分表
├── output/                                     权重与日志
└── samples/                                    采样输出
```

## 快速开始（5 步）

| # | 动作 | 命令 / 文件 |
|---|---|---|
| 1 | 确定授权路径（A 授权 / B 非商业研究 / C 抽象重绘），采集并清洗图片 | `dataset/README.md` |
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
