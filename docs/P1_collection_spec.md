# P1 采集与清洗操作规范

> **决策前提**：P0 = **B 非商业个人研究**（2026-11-06 锁定）。依据 `Gordon_Hunt_style_research_and_LoRA_plan.md` 第 4.1 / 4.4 / 第 10 节。
> **范围**：P1 = 采图 → 清洗 → 分组 → 台账。不含 caption 编写（P2）与质检执行（P3）。
> **指定来源**（2026-11-06）：Pinterest、微信公众号、小红书、Instagram、公开作品网页。分级与用法见第 2 节。
> **性质**：工程操作规范，不构成法律意见。商用或发布权重需改走路径 A 或 C。

---

## 0. B 路径的六条硬约束（先读，违反即前功尽弃）

| # | 约束 | 落地做法 |
|---|---|---|
| 1 | **合法访问** | 只从允许访问的公开页面或自有/已购素材取得；不绕过付费墙、DRM、`robots.txt` 或站点「禁止抓取」声明。**逐张人工另存，不写批量爬虫**。 |
| 2 | **纯非商业研究** | 全程不得用于接单、售卖、广告、带品牌名的产品或任何对外服务。 |
| 3 | **不分发** | 不公开数据集、不打包上传公共数据集平台、不提交作品图到本公开仓库。 |
| 4 | **充分标注来源** | 每张记录原始作品页 URL、作品标题、访问日期；台账只留本机。 |
| 5 | **不发布权重与样图** | `output/`、`samples/` 已被忽略；README / Issues / PR 里也不要贴复刻明显的生成图。 |
| 6 | **不制造官方关联** | 不用画家真名做触发词、模型名、仓库描述或营销语；不使用 2025 PITAKA 联名的视觉资产。 |

**公开仓库边界**：本仓库是公开 GitHub 仓库，只放文档、代码与空模板。真实台账写 `dataset/manifest.local.csv`（gitignored），不要覆盖 `manifest.csv` 模板后提交。

**云 GPU 边界**：上传到**自己控制的实例**做计算 ≠ 向公众分发，可行；但需选可信平台、训练完删除实例内数据、不用公开共享镜像承载数据集。路径 C 那种「在线训练服务」把作品交给第三方且控制粒度低，继续不推荐。

---

## 1. 数量口径（最容易算错的一处）

| 项 | 张数 | 说明 |
|---|---|---|
| `10_full/` 整画（训练） | **56** | 按 22 / 18 / 16 配比（见下） |
| `3_dabs/` 圆点光斑特写 | **12** | 从训练整画里裁，不是另找 12 张新作品 |
| `3_filaments/` 焦散细线特写 | **12** | 同上 |
| **训练图合计** | **80** | 与 `tools/audit_dataset.py` 的 `GROUPS` 期望值一致 |
| `val/` 验证图 | **6–8** | **另算**，完全不参与训练，需是独立作品 |
| **需采集的不同整画作品** | **62–64** | 56 训练 + 6–8 验证 |

> ⚠️ 特写只能从**训练组整画**裁切。**严禁从 `val/` 图裁特写**——同一画面的纹理进了训练集会让验证集失效，等于自己给自己放水。

**整画题材配比（56 张）**

| 题材 | 张数 | 学什么 |
|---|---|---|
| 极简水平线 / 帆船剪影 | 22 | 构图、留白、逆光结构 |
| 俯视野泳 / 水面铺满 | 18 | 俯视视角、焦散细线 |
| 海岸线 / 沙滩 / 人物 | 16 | 斜切色块分区、题材泛化 |

别让 70% 都是帆船，否则风格会被绑死在「帆船」这个主体上。

---

## 2. 采图来源（指定的 5 类）

**核心原则：社交 / 聚合平台当「发现渠道」，不是「训练图最终来源」。** 它们用于找作品标题、扩充题材覆盖、定位原始作品页；训练图优先回溯到画廊 / 艺术家官网的**最高分辨率正面图**。这样既满足 B 路径的「合法访问 + 充分署名」，也避免把二次压缩、贴纸与平台水印学进风格向量。

| 来源 | 角色 | 本机可达性（2026-11-06 实测） | 典型噪声 / 必须处理 |
|---|---|---|---|
| **公开作品网页**（艺术家官网、代理画廊作品页） | ✅ **训练图最终来源** | `wychwoodart.com` 200、`artienda.co.uk` 200 | 同一作品多版次、in-situ 陈设图、左下角签名 |
| **Pinterest** | 🔍 发现渠道 / 题材线索 | 200 | 低分辨率二次压缩、拼图、随意裁剪、常无原始出处；**主要用来反查作品标题** |
| **微信公众号文章**（`mp.weixin.qq.com`） | 🔍 发现渠道 / 中文线索 | 200 | 排版截图、正文文字叠加、二维码、作者二次调色；**截图一律不进训练集** |
| **小红书** | 🔍 发现渠道 / 题材线索 | 200 | 九宫格拼图、贴纸、滤镜、水印、强压缩 |
| **Instagram** | 🔍 发现渠道 | **本机不可达**（`curl` 返回 `000`） | 方形裁切、滤镜、水印；处理方式见下方说明 |

**逐平台操作规则**

1. 在平台上找到作品 → 记下**作品标题 / 发布者 / 平台链接 / 访问日期**。
2. 用标题反查公开作品页 → 从该页另存最高分辨率正面图，`source_url` 填**原始作品页**，平台链接记入 `discovery_url`，平台名记入 `source_platform`。
3. 反查不到原始页，但平台允许保存、且图像达标（短边 ≥1024、无文字水印）→ 可入训练集，台账标 `source_status = unverified`。**建议不超过总量的 20%（≤16 张），且一律不进 `val/`**（验证集必须来源清晰）。
4. 任何带文字、二维码、贴纸、拼图边框、明显滤镜偏色的图 → 直接剔除，不靠裁切挽救。
5. **逐张人工另存、不写爬虫**；遵守平台服务条款，不绕过登录、付费墙或地区限制。

> ⚠️ **Instagram 本机不可达**：不要为采图去搭建绕过手段——B 路径的「合法访问」是硬要件，绕过访问限制会让整条路径失效。建议在其余四类可达平台完成发现，或由你在合规网络环境下人工另存后，把文件与来源信息带回本机处理。

**已指定入口（2026-11-06）**

| 入口 | 实测 | 用法 |
|---|---|---|
| `https://www.gordon-hunt.co.uk/`（艺术家官网） | 200 ✅ | **优先回溯源**：从作品页取最高分辨率正面图，`source_url` 填这里，`source_status = original` |
| `https://www.instagram.com/foweyartist/`（Instagram 账号） | 本机不可达 | 仅作发现渠道：把作品标题与账号链接记入 `discovery_url`，再回官网 / 画廊页反查原图；需你在合规网络环境下人工另存 |

> 官网首页当前可抓取的正文极少（仅 "Welcome: Gordon Hunt Artist" 与 Fowey / Cornwall 工作室信息），疑似 JS 渲染或图片型站点；**作品页 URL 模式需在浏览器里人工确认后**再填入清单，不要在清单里只填首页地址。

**本机网络补充**：`huggingface.co` / `civitai.com` 不通；`github.com` / `pypi.org` / `hf-mirror.com` 通。采集走浏览器逐张保存，不依赖这些站点。

**来源回溯状态**（`manifest.local.csv` 可选列，不影响质检必需字段）：

| `source_status` | 含义 |
|---|---|
| `original` | 已从画廊 / 艺术家官网作品页取得原图 |
| `unverified` | 仅平台来源、未回溯到原始页（受 20% 上限约束） |
| `self-created` | 自有 / 已购素材扫描 |

**同一作品多版次**：画廊常给同一画面配多个限量版尺寸或 `- small` 变体，另附「挂在客厅」的 in-situ 陈设图。三者都要识别出来，只保留**分辨率最高的正面原图**一张。跨平台发现时尤其容易把同一张画收两遍，去重前先按标题归并。

---

## 3. 逐张清洗（按顺序执行）

| # | 操作 | 参数 / 判定 |
|---|---|---|
| 1 | 剔除 in-situ 陈设图、画框、家具、白墙、投影，**以及平台截图文字、贴纸、拼图边框、二维码、正文叠加** | 任何非画面内容一律不要；社交平台来源优先过这一关 |
| 2 | **裁签名** | 默认**裁掉底部全宽 8%**（签名在左下角），保持画面完整、不产生 L 形缺口；签名上移到 8% 以上时用内容感知修复局部。绝不能留下可读文字，否则模型学会生成伪文字 |
| 3 | 去版画纸边 / 白边 / 水印 / 价格标签 / 网站角标 / 平台账号水印 | 顺便检查四角与右下角 |
| 4 | 同作品去重 | 先按标题人工归并版次（含跨平台重复）；再跑 aHash 粗筛（脚本阈值 ≤20/256）+ pHash 汉明距离 ≤8；有条件再用 CLIP embedding 余弦 ≥0.95 精筛 |
| 5 | 分辨率筛选 | 短边 ≥1024 px（硬下限 768）；600 px 原图**不要硬拉到 1024**，换来源 |
| 6 | 色彩 | 统一 sRGB；**不做**自动对比度 / 饱和度增强——高饱和高对比本身就是目标；带明显滤镜偏色的平台图直接弃用，不试图「校回来」 |
| 7 | 格式与命名 | PNG 或 JPEG q≥95；`gh_001.jpg` … 纯 ASCII、无空格中文；图片与 caption 同名 |
| 8 | 分组 | 整画 → `10_full/`；特写 → `3_dabs/` 或 `3_filaments/`；验证图 → `val/` |
| 9 | 裁特写 | 从训练整画裁 **768–1024 px 纯纹理块**（硬下限 640，见 3.1）：不含船、人、地平线。`3_dabs` 只放圆点/短椭圆光斑，`3_filaments` 只放白色卷曲焦散细线，两套笔触不要混 |
| 10 | 隔离验证集 | 6–8 张独立作品、`source_status = original`，确认不出现在 `configs/dataset_sdxl.toml` 的任何 subset 里 |

> 目录名前缀 `10_` / `3_` 是 **Kohya 的 repeats 约定**，`dataset_sdxl.toml` 里不要再写 `num_repeats`，否则次数相乘。

### 3.1 批量清洗脚本 `tools/clean_dataset.py`

**输入**：`dataset/_inbox/` 放原始下载图（任意文件名，脚本只读不改）；`dataset/collection_plan.csv` 是逐图清单（从 `collection_plan.template.csv` 复制后填写，**该文件与 `_inbox/` 均已 gitignored**）。

```bash
PY=/d/ComfyUI/.venv/Scripts/python.exe   # 本机已有 Pillow 11.1.0；或先 pip install Pillow 后用 python
cp dataset/collection_plan.template.csv dataset/collection_plan.csv
# ① 填好清单，先预览（默认 dry-run，不写任何文件）
$PY tools/clean_dataset.py --root dataset
# ② 确认无误再真正写入
$PY tools/clean_dataset.py --root dataset --apply --report eval/clean_report.txt
```

> `/d/ComfyUI/.venv/Scripts/python.exe` 是本机现成环境的 Git Bash 路径示例；其他机器换成自己的 Python 即可（主 Python 执行 `pip install Pillow` 后同样能跑）。本机实测：主 Python 3.13 **无 Pillow**，ComfyUI venv 为 Python 3.12.9 + Pillow 11.1.0。

脚本**不删改 `_inbox/` 原图、不覆盖已有输出**（除非 `--overwrite`）、**不创建 caption**（P2 再做）。

| 清单列 | 必填 | 说明 |
|---|---|---|
| `source_file` / `group` / `source_url` / `source_status` | ✅ | `group` ∈ `10_full` / `3_dabs` / `3_filaments` / `val`；`source_status` ∈ `original` / `unverified` / `self-created` |
| `target_name` | | 输出名如 `gh_001.jpg`；留空按行号自动生成 |
| `title` / `source_platform` / `discovery_url` / `original_url` / `subject_tag` / `accessed_at` / `notes` | | 溯源与题材配比统计，一并写进台账 |
| `crop_x` / `crop_y` / `crop_w` / `crop_h` | | **四个都填**才启用特写模式：按原图像素坐标裁框，跳过白边与签名裁切 |

**处理链**：去近白白边（只裁「整条边缘都接近纯白」的边，浅色天空不会被误伤）→ 底部全宽裁 8% → 尺寸门槛 → aHash 近重复报告 → 写 `dataset/<group>/gh_NNN.jpg` → 生成 / 合并 `dataset/manifest.local.csv`（含 sha256、尺寸、`license=non-commercial-research`）。

**尺寸口径修正**：`configs/dataset_sdxl.toml` 的 `min_bucket_reso = 640`，所以特写块 **640 px 是硬下限、建议 768–1024 px**；原文「512–1024」的下半段会被训练器 bucket 排除。整画硬下限 768、建议 ≥1024。脚本按组分别判定。

常用开关：`--bottom-crop 0`（已手工裁过签名）、`--no-trim-border`、`--border-level 235`（画廊 JPEG 白边带压缩噪声时调低）、`--skip-duplicates`、`--overwrite`、`--dedup-threshold N`。

> 清单请用 Excel / 表格软件编辑，**别手工数逗号**——列错位会让 `crop_*` 被误填而触发特写模式。脚本对缺列、非法 group、占位 URL、越界裁框都会直接报 ERROR，dry-run 阶段就能发现。近重复只在「整画 / 验证」与「特写」各自类别内比对，因为特写本来就是从整画裁出来的。

---

## 4. 目录与台账

```
dataset/
├── manifest.csv              空模板（提交进仓库，勿填真实来源）
├── manifest.local.csv        真实台账（gitignored，仅本机）
├── 10_full/       gh_001.jpg + gh_001.txt …   56 张
├── 3_dabs/        gh_0xx.jpg + gh_0xx.txt …   12 张
├── 3_filaments/   gh_0xx.jpg + gh_0xx.txt …   12 张
└── val/           6–8 张（无 caption 也可，不参与训练）
```

`manifest.local.csv` 字段（与模板一致）：

| 字段 | B 路径填法 |
|---|---|
| `file` / `group` / `caption_file` | 与磁盘文件名严格一致 |
| `source_url` | **必填**；回溯成功填原始作品页，未回溯填该平台的作品帖链接，绝不填站点首页 |
| `license` | 统一 `non-commercial-research`；质检脚本会按当前路径 B 校验 |
| `permission_ref` | 留空（路径 A 才填授权凭证） |
| `sha256` / `width` / `height` | P3 由脚本计算回填，先留 `0` |
| 可选追加列 | `title` / `accessed_at` / `source_platform` / `discovery_url` / `original_url` / `source_status`（不影响质检必需字段；多平台来源建议至少记 `source_platform` 与 `source_status`） |

---

## 5. 分工：需要你拍板 vs 我能代劳

| 需要你本人 | 已由脚本 / 助手代劳 |
|---|---|
| 判断平台访问与保存方式是否符合「合法访问」、逐张另存到 `_inbox/` | ✅ `clean_dataset.py`：裁底部 8%、去白边、重命名、统一格式 |
| 用标题反查原始作品页、判定 `source_status`、填 `collection_plan.csv` | ✅ 按清单回填 `source_url` 等溯源字段 |
| 判断哪些是同一作品的不同版次 | ✅ aHash 近重复报告（`--skip-duplicates` 可自动跳过）；跨平台标题归并仍需人工确认 |
| 判断特写属于「圆点」还是「焦散线」、给出 crop 坐标 | ✅ 按坐标批量裁 768–1024 纯纹理块 |
| 挑选哪 6–8 张做验证集（须 `original`） | ✅ 自动生成 / 合并 `manifest.local.csv`，算 sha256 与尺寸 |
| 最终确认清洗后画面没有签名与平台文字残留 | ✅ 跑 `audit_dataset.py` 质检、修脚本 |

---

## 6. P1 → P2 的验收门槛

- [ ] `10_full` 56 / `3_dabs` 12 / `3_filaments` 12 / `val` 6–8，数目与配比都对
- [ ] 每张图短边 ≥1024 px（低于 768 的一张不留）
- [ ] 100% 无可读文字、无画框、无水印、无 in-situ 陈设图，**无平台截图文字 / 贴纸 / 拼图边框 / 二维码 / 滤镜偏色**
- [ ] 无同作品多版次重复（含跨平台重复）；`val/` 与训练组无画面重叠
- [ ] 每条台账都有 `source_url` 与 `non-commercial-research`，并标注了 `source_status`
- [ ] `unverified` 来源 ≤16 张且**全部不在 `val/`**
- [ ] `tools/clean_dataset.py --root dataset` dry-run 无 ERROR；`--apply` 后 `eval/clean_report.txt` 的 WARN 已逐条人工确认
- [ ] `git status` 里**看不到**任何图片、caption、`_inbox/` 原图、`collection_plan.csv` 或 `manifest.local.csv`

---

## 7. 下一步

P2：按 `tools/caption_vocab.md` 写 80 条 caption（触发词 `glntwtr` 置首位、禁用词为零），再由你逐条复核画面语义。之后 P3 跑 `python tools/audit_dataset.py --root dataset` 全绿，才进云 GPU 训练。

> 若中途想改为可商用 / 可发布，必须**停止**使用 B 下采集的数据，重新按路径 C 用自有素材重绘，或先取得路径 A 的书面授权。
