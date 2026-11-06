# dataset/ — 采集、授权与目录规范

> **先确定授权路径，再放第一张图。** 画家在世，作品仍在版权保护期内；详见主方案第 4.1 / 第 10 节。

## 1. 授权路径（三选一）

| 路径 | 适用 | 要求 |
|---|---|---|
| **A 书面授权** | 商用、发布权重、对外服务 | 艺术家 / 代理画廊书面许可，明确「用于生成模型微调」、地域、期限、是否可分发权重；凭证写入 `manifest.csv.permission_ref` |
| **B 非商业个人研究** | 本地实验、不分发 | 合法访问 + 纯非商业研究 + 充分标注来源；不公开权重、不公开数据集、不商用输出 |
| **C 要素抽象重绘** | 想要可商用、可发布的模型 | **不复制原作**：按「离散光斑 / 冷暖对比 / 平面化色块 / 剪影 / 俯视」等抽象维度，用自有或授权素材重绘或程序化合成 |

**当前已锁定路径 B（2026-11-06）**，详见 `docs/P1_collection_spec.md`。走 A 时把授权凭证路径填进台账。本说明不构成法律意见。

> **B 路径下的台账**：`manifest.csv` 是提交进公开仓库的**空模板**，请保持原样。真实台账写到 `dataset/manifest.local.csv`（已被 `.gitignore` 忽略），字段相同，`license` 统一填 `non-commercial-research`，`permission_ref` 留空，`source_url` 精确到作品页。`tools/audit_dataset.py` 会优先读取 local 台账并校验 license 与当前路径一致。多平台采集时可自行追加 `title / accessed_at / source_platform / discovery_url / original_url / source_status` 列（质检只校验必需字段，多余列忽略）；来源分级与回溯规则见 `docs/P1_collection_spec.md` 第 2 节。

## 2. 目录与命名

```
dataset/
├── manifest.csv       逐图溯源台账（必填）
├── 10_full/           56 张整画 + 同名 .txt        （前缀 10 = repeats）
├── 3_dabs/            12 张局部特写 + 同名 .txt    （前缀 3 = repeats）
├── 3_filaments/       12 张局部特写 + 同名 .txt
└── val/               6-8 张验证图，不参与训练
```

- 文件名：`gh_001.jpg`、`gh_002.png` … 无空格、无中文、纯 ASCII。
- 前缀数字是 **Kohya 目录名约定**，`configs/dataset_sdxl.toml` 里**不要**再写 `num_repeats`，否则重复相乘。
- `val/` 不出现在任何训练配置里。

## 3. 图像规格

| 项 | 要求 |
|---|---|
| 短边 | ≥ 1024 px（硬下限 768） |
| 长宽比 | 保留原始比例，交给 bucketing；覆盖 1024² / 1152×896 / 896×1152 / 1216×832 |
| 色彩 | sRGB；**不做**自动对比度 / 饱和度增强 |
| 格式 | PNG 或 JPEG q≥95 |
| 放大 | 需放大时保守倍数 + 轻锐化；拒绝会产生假笔触的超分模型 |

## 4. 清洗清单（逐条执行）

1. **裁掉左下角签名**（约 8–12% 区域）或内容感知修复。多张作品带 `GORDON HUNT` 字标或橙褐草写签名；残留会让模型学会生成伪文字。
2. **剔除 in-situ 陈设图**（含画框、家具、白墙、投影）。
3. **剔除版画纸边、白边、水印、价格标签、网站角标**。
4. **同作品多版次去重**：如 `Turquoise bay` 与 `Turquoise bay - small`、不同 Edition 尺寸，只保留最高分辨率一张；pHash 距离 ≤ 8 或 CLIP 余弦 ≥ 0.95 判为近重复。
5. **剔除低质图**：JPEG 块、摩尔纹、模糊、翻拍偏色、过曝丢细节。
6. **题材均衡**：按 22 / 18 / 16 / 12 / 12 配比，别让 70% 都是帆船。
7. **局部特写**：从整画中裁 512–1024 px 的纯纹理块，分别归入 `3_dabs`（圆点光斑）与 `3_filaments`（白色焦散细线）。
8. **留验证集**：从整画中留 6–8 张，完全不参与训练。

## 5. manifest.csv 字段

| 字段 | 说明 |
|---|---|
| `file` | 文件名，与磁盘一致 |
| `source_url` | 原始来源链接 |
| `license` | 授权类型 / 许可标识（如 `licensed-for-finetune` / `non-commercial-research` / `self-created`） |
| `permission_ref` | 授权凭证文件路径或编号（路径 A 必填） |
| `sha256` | 文件哈希 |
| `width` / `height` | 像素尺寸 |
| `group` | `10_full` / `3_dabs` / `3_filaments` / `val` |
| `caption_file` | 同名 `.txt` 文件名 |

> 示例行 `EXAMPLE_REMOVE_ME` 请在实际使用前删除。

## 6. 禁止事项

- 不要把本目录打包分发、上传到公共数据集平台（除非走路径 A 且许可允许）。
- 不要把画框、签名、水印、网页截图混进训练图。
- 不要在 caption 里写艺术家真名或任何风格常量词（见 `tools/caption_vocab.md`）。
- 不要在未跑 `python tools/audit_dataset.py --root dataset` 且全绿之前启动训练。
