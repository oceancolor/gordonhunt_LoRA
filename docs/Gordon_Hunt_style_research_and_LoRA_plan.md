# Gordon Hunt 艺术风格研究 × LoRA 训练方案

> 版本 v1.0 ｜ 2026-11-05 ｜ 工作区：本仓库根目录
> 目标：把一位在世英国海景画家的视觉语言，拆解成**可采样、可标注、可评估**的训练目标，并给出一套能直接落地的风格 LoRA 工程方案。

---

## 0. 执行摘要（先看这五条）

1. **研究对象确认**：Gordon Hunt（戈登·亨特，1958– ），英国康沃尔郡 Fowey 工作室的当代海景画家，超过 45 年艺术与设计从业经验；2019、2020 年入选英国皇家海洋艺术家协会（RSMA）年展，2025 年 12 月与 PITAKA 在深圳 OCAT 举办「觉知伏流 / GLINTS OF AWARENESS」联展。
2. **材料纠偏**：中文网络常把他误标为「水彩画家」或「油画风景」。一手画廊资料与画面质感均指向 **丙烯（acrylic on box canvas / deep edge canvas）**，部分委托作品为布面油画，另有 Giclée 限量版画。**训练数据里不要写 `watercolor`，也不要写 `oil painting` 作为全量标签**——这会直接污染风格向量。
3. **风格本质**：不是「印象派海景」这个泛标签，而是 **深色底起笔 → 层层叠色向最亮处推进 → 用离散的圆点/椭圆光斑与白色焦散细线，在平面化冷色块上构建逆光闪烁**。平面设计背景带来强烈的色块分区与图形化秩序。这是本方案的核心可学习信号。
4. **两个最容易翻车的坑**（来自实际看图）：
   - 多张作品**左下角有艺术家签名**（`GORDON HUNT` 字标 / 橙褐色草写）。不裁掉，LoRA 会学会在左下角生成伪文字。
   - 同一作品有**多个限量版尺寸与 in-situ 陈设图**，会被误当多张样本，导致构图记忆化。必须做近重复去重。
5. **合规红线**：画家在世，作品仍在版权保护期内。2026 年英国**没有**商业文本与数据挖掘（TDM）例外，`CDPA 1988 s.29A` 仅覆盖「非商业研究 + 合法访问」；英国政府已放弃 opt-out 式商业 TDM 例外，上议院 2026 年报告进一步建议禁止未经授权的「in the style of」商业使用并强制训练数据透明。**商业用途必须先取得授权**。详见第 10 节。

---

## 1. 艺术家档案与来源可信度

| 项目 | 结论 | 主要来源 |
|---|---|---|
| 姓名 / 生年 | Gordon Hunt，1958 年生于英国 | 中文艺术媒体（今日头条、微博、DigFamily）一致，画廊资料未直接给出生年，**标注为中等置信度** |
| 工作室 | 英国康沃尔郡 Fowey（福伊） | Wychwood Art、Artienda、深圳新闻网 |
| 从业背景 | 超过 45 年艺术与设计经验；有平面设计背景 | 深圳新闻网 / 深圳Plus / PITAKA 联展报道；Agora Gallery 评论提及 graphic design 影响 |
| 材质 | 丙烯 + box canvas / deep edge canvas；部分委托作品布面油画；Giclée 限量版画（常见 Edition of 120） | Wychwood Art 作品页（高置信度，一手画廊） |
| 展览 | 2019 / 2020 RSMA 年展；纽约、中国香港展出；英国电视节目 *Landscape Artist*；2025-12-14 深圳 OCAT 联展 | Artienda、深圳新闻网 |
| 题材 | 帆船与港湾、野泳者（wild swim）、海滩人物、海岸线与浅滩、日出逆光海面 | 画廊作品标题列表 |

### 1.1 关键自述原文（一手画廊转录）

> "I paint the light effects of sunshine on water, with sparkling reflections and silhouettes, resulting in strong contrasting colours and dynamic shapes."
>
> "I have a real sense of 'painting the light' when creating these works, evoking the feeling of sunshine, holidays and well being, which I think is why they are so popular."
>
> "The camera is my sketchbook, I carry it at all times, ready to capture a moment, a ray of light, a sparkle of water. Back in the studio I sketch out the composition in my sketchbook, it has **brown paper pages**, so as well as the shapes drawn with a black pencil, I also use a **white pencil to indicate the white, bright areas** of the painting."
>
> "The quick drying properties of acrylic suits my style of painting, **building up layers of colour, working towards the brightest parts** of the painting. I also like the modern clean look of box canvas on the wall."

### 1.2 批评性描述（Agora Gallery, 2018）

> "polished meditation in light and color" ／ "almost **pointillist** technique" ／ "the luminosity of light reflected in water becomes the most salient theme" ／ "strong contrasting colors and dynamic shapes" ／ 对比色产生 "**visual energy and excitement**" ／ 受 **graphic design** 影响 ／ "sensation of symmetry" ／ "the poetic reciprocity between sea and sky"。

### 1.3 中文报道补充（2025 PITAKA 联展）

> 「独创性地以**深色画布为起点**，通过**层层叠加的色彩**来描绘光线本身，以强烈的色彩对比、动态的构图和独特的『**闪烁**』笔触，为静谧的海面注入生命力。」

这一句与英文自述「由深到亮层层叠加」互相印证，是本方案判断**明度结构**的依据。

> 来源清单与访问日期见附录 A。本报告区分「一手画廊 / 媒体报道 / 评论文字」三级可信度，生年一类仅有二手来源的信息已标注置信度。

---

## 2. 风格解构：六个维度

基于三张公开作品图（《Wild Swim》《Sailing the Sparkling Sea》《Anchored Up》）的逐张视觉核对，加上文字资料交叉验证。

| # | 维度 | 可观察特征 | 训练中如何表达 |
|---|---|---|---|
| D1 | **题材** | 帆船剪影（单艘/双艘）、野泳者俯视、海滩人物、沙滩与浅滩、日出/日落港湾；人物始终**很小**，是尺度参照物而非主体 | caption 中作为「变化项」写明；不写进触发词 |
| D2 | **光** | 强逆光；水平线附近一条近白的过曝反射带；光斑从反射带向下/向四周衰减；船体与远景压成**深蓝黑色剪影**；天空也会散布稀疏光点 | 靠数据学习；prompt 里可用 `backlit` / `low sun` 控制变化 |
| D3 | **色** | 冷色主导：**绿松石 / 青绿 / 湖蓝 / 深海军蓝 / 黄绿浅滩**；暖色为**点缀**：橙、金黄、粉白的极小光点；沙滩为米黄/浅棕；暗部为近黑的深蓝。冷暖对比是「visual energy」的实现方式 | 靠数据学习；主色作为 caption 变量，避免全量固定 |
| D4 | **笔触 / 肌理**（最关键） | **两套语言并存**：<br>① 离散的**圆点 / 短椭圆光斑**（dabs），尺度近似均匀，密集成片，水平方向略拉长；<br>② **细长卷曲的白色焦散线**（caustic filaments），像水下折射网，叠在扁平蓝绿色块上。<br>外加不规则深蓝**色块**作暗部、暖橙小点作对比闪烁 | 需要**局部特写 crop** 才能学到；整图训练容易只学到大色调 |
| D5 | **构图** | ① 极简水平线构图（水平线约上 1/3，单艘剪影居中偏侧，大面积留白式水面）；② **俯视无水平线**（水面铺满全幅，主体小而偏下/偏左）；③ 斜切式海岸线（沙滩从下方斜切入，深色礁石压角）。平面化色块分区，边界用斑点过渡，图形设计感强 | 靠数据分布 + prompt 控制；不要把「俯视」写成全量常量 |
| D6 | **材质与制作** | 丙烯平涂 + 叠色；无可见厚涂笔触堆积、无水彩晕染/纸纹；box canvas 无框；画面**不追求写实细节**，是装饰性平面构成 | 视觉结果可学；「作画顺序」不可学，见第 3 节 |

### 2.1 反特征（Negative Anchors）——「他不是什么」

写进推理端 negative prompt，也用于人工筛图时剔除不合格样本：

- 不是**水彩**：无湿画晕染、无水痕、无纸纹、无透明罩染的薄透感。
- 不是**厚涂油画 / 印象派笔触堆叠**：无方向性扫笔、无颜料起伏；笔触是「点」与「线」而非「扫」。
- 不是**写实海景 / 摄影**：无真实波浪解剖、无细节人脸、无镜头景深与光晕（lens flare / bokeh）。
- 不是**柔和渐变**：色块之间是硬边或斑点过渡，不是平滑过渡。
- 不是**低饱和 / 灰调**：整体高饱和、高明度对比。
- 不是**复杂叙事**：画面元素极少，留白/留水面积大。

---

## 3. 风格要素 → 学习载体映射（避免不切实际的目标）

这一节是方案的关键：**不是所有风格描述都该塞进 caption**。LoRA 学的是像素统计，学不到艺术家的作画流程与意图。

| 风格要素 | 由谁负责 | 具体做法 |
|---|---|---|
| 圆点光斑 / 焦散细线 / 色块边缘 | **数据集**（主） | 整图 + 局部特写双通道采样，见 4.2 |
| 冷底 + 暖点的调色板、深色暗部 | **数据集**（主） | 覆盖不同时段/主色的样本 |
| 剪影、俯视、极简水平线、斜切海岸 | **数据集** + caption 变量 | caption 写 `view` / `horizon` 维度，让风格与构图解绑 |
| 触发词与风格绑定 | **caption 策略** | 稀有中性 token + `keep_tokens=1`，见第 5 节 |
| 由深到亮叠色、丙烯快干、棕色纸速写本 | **不可学习** | 仅用于**人工评估描述**，**禁止**写入 caption（会引入模型无法对应的语义噪声） |
| 「阳光、假期、幸福感」情绪 | **不可直接学习** | 通过题材与配色间接体现；不要写 `happy` `holiday feeling` |
| 留白比例、光斑密度、闪烁强度 | **推理端** | LoRA 权重 0.6–0.9 + prompt 修饰 + 负面提示，见第 9 节 |
| 严格构图复刻 | **ControlNet / IP-Adapter** | 可选扩展，不塞进本 LoRA，见第 11 节 |

---

## 4. 数据集方案

### 4.1 来源与授权路径（先解决，再采集）

| 路径 | 适用场景 | 要求 |
|---|---|---|
| **A. 授权许可**（商业唯一稳妥路径） | 商用、发布权重、对外服务 | 与艺术家 / 代理画廊取得书面授权，明确「用于生成模型微调」、地域、期限、是否可分发权重；逐图留存凭证 |
| **B. 非商业个人研究** | 本地实验、不分发 | 对应英国 `CDPA s.29A`：合法访问 + **纯非商业研究** + 充分标注来源。不公开权重、不公开数据集、不商用输出、不做带品牌名的产品 |
| **C. 要素抽象重绘**（最干净） | 想要可商用、可发布的模型 | 不复制原作：按第 2 节的**抽象维度**（离散光斑、冷暖对比、平面化色块、剪影、俯视）用自有/授权摄影素材重绘或程序化合成训练图。**视觉效果可借鉴，具体作品不进数据集** |

> 本方案默认按 **B（研究）** 或 **C（可商用）** 组织工程；若要走 A，把授权凭证路径填进 `dataset/manifest.csv`。
> 本报告为技术文档，**不构成法律意见**；落地商用前请咨询专业人士。

### 4.2 规模与分层配比（建议 80 张）

| 分组 | 目录 | 张数 | repeats | 作用 |
|---|---|---|---|---|
| 整画 · 极简水平线/帆船剪影 | `dataset/10_full/` | 22 | 10 | 学构图、留白、逆光结构 |
| 整画 · 俯视野泳/水面铺满 | `dataset/10_full/` | 18 | 10 | 学俯视视角与焦散细线 |
| 整画 · 海岸线/沙滩/人物 | `dataset/10_full/` | 16 | 10 | 学斜切色块分区、题材泛化 |
| **局部特写 · 圆点光斑** | `dataset/3_dabs/` | 12 | 3 | 强化点状笔触纹理 |
| **局部特写 · 焦散细线** | `dataset/3_filaments/` | 12 | 3 | 强化白色卷曲线纹理 |
| 合计 | | **80** | | |

**为什么特写要给低 repeats**：局部 crop 没有构图信息，若与整图等权重，模型会把「风格」学成一层无差别纹理贴膜，出现过拟合的典型症状——任何 prompt 都吐同一片糊状色斑。整图:特写 ≈ 3:1 的曝光比是保守起点，可在 v2 用 4:1 / 2:1 做消融。

`dataset/10_full` 的 `10` 即 Kohya 目录名约定的 repeat 数；实际总步数按 `repeats × 图片数 × epochs ÷ batch` 计算，以训练器打印的 step 估算为准。

### 4.3 图像规格

| 项 | 规格 |
|---|---|
| 分辨率 | 短边 ≥ 1024 px；SDXL / Flux 训练分辨率 1024；不要把 600 px 原图硬拉到 1024 |
| 长宽比 | 开启 bucketing（`enable_bucket`）；至少覆盖 1024×1024、1152×896、896×1152、1216×832（原作常见 70×113 cm 横幅） |
| 格式 | PNG 或高质量 JPEG（q≥95）；统一 sRGB |
| 色彩 | 不做自动对比度/饱和度增强——本风格的高饱和与高对比本身就是目标，增强会过冲 |
| 放大 | 需放大时用 Real-ESRGAN 类保守倍数 + 轻锐化；拒绝产生假笔触的超分模型 |

### 4.4 清洗规则（逐条执行，这是成败关键）

1. **裁签名**：三张核对样本均在**左下角**带签名（白色印刷体 `GORDON HUNT` 或橙褐草写）。统一裁掉左下角约 8–12% 区域，或做内容感知修复。**训练集里绝不能留下可读文字**。
2. **剔除 in-situ 陈设图**：画廊常提供「挂在客厅里」的场景图，含画框、家具、白墙、阴影 → 全部剔除。
3. **剔除版画纸边 / 白边 / 画框 / 水印 / 价格标签 / 网站角标**。
4. **同作品多版次去重**：如 `Turquoise bay` / `Turquoise bay - small` / 不同 Edition 尺寸，属同一画面，只保留最高分辨率的一张。用 pHash（汉明距离 ≤ 8）+ CLIP embedding 余弦相似度 ≥ 0.95 双重判定。
5. **剔除低质样本**：JPEG 块、摩尔纹、模糊、过曝丢细节、明显偏色的翻拍。
6. **题材去偏**：不要 70% 都是帆船；按 4.2 配比强制均衡，否则模型会把风格绑死在帆船上。
7. **留出验证集**：从整画中留 6–8 张完全不参与训练，用于检测「学到了风格」还是「背下了构图」。
8. **溯源**：逐图在 `dataset/manifest.csv` 记录 `file, source_url, license, permission_ref, sha256, width, height, group, caption_file`，见 `tools/audit_dataset.py` 的字段定义。

### 4.5 目录结构

```
dataset/
├── README.md                 # 授权与目录规范
├── manifest.csv              # 溯源台账（必填）
├── 10_full/                  # 56 张整画 + 同名 .txt
├── 3_dabs/                   # 12 张局部特写 + 同名 .txt
├── 3_filaments/              # 12 张局部特写 + 同名 .txt
└── val/                      # 6-8 张验证图（不参与训练）
```

---

## 5. Caption 规范

### 5.1 触发词

**不要用在世艺术家的真名做触发词**：既会把模型锚到基础模型里可能已有的姓名先验，也会在模型命名/发布时制造「官方关联」的合规风险。

| 候选 | 说明 |
|---|---|
| `glntwtr` （推荐） | 无语义稀有 token，CLIP 无先验，绑定最干净 |
| `cnwllight` | 有弱语义（Cornish light），泛化稍好但易与「风景摄影」串味 |
| `vxlumen` | 完全造词，备选 |

全数据集统一一个 token，置于 caption **首位**，配合 `--keep_tokens=1` 锁住。

### 5.2 标注原则

- **写变化，不写常量**：描述「主体 / 视角 / 光源 / 主色 / 构图」，**不写** `painting` `acrylic` `pointillist` `sparkling` `by Gordon Hunt`。若每张都写同一个风格词，模型会依赖那个词而架空触发词，LoRA 表现为「很弱」。
- **不写不可学习项**：作画顺序、快干丙烯、棕色速写本、情绪词，见第 3 节。
- 长度 **8–16 个英文词**，Flux 用短语句、SDXL 用自然短句。
- 开启 `--shuffle_caption`、`--caption_dropout_rate=0.05`（caption 必须有差异，dropout 才有意义）、`--keep_tokens=1`。

### 5.3 变量词表 → `tools/caption_vocab.md`

| 维度 | 可选值（示例） |
|---|---|
| subject | `a single sailboat` / `two yachts` / `two swimmers` / `beach figures` / `a moored boat` / `an empty shoreline` |
| view | `high horizon line` / `overhead view, no horizon` / `low oblique coastline` / `eye-level sea level` |
| light | `backlit low sun` / `midday glare` / `sunrise reflection band` / `warm evening glints` |
| palette | `turquoise and deep navy` / `teal with lime shallows` / `blue with gold glints` / `cool blue with orange accents` / `sand beige and dark blue` |
| composition | `vast negative space` / `small subject off-center left` / `diagonal sand wedge` / `dark reef in lower corner` |
| texture-state | `dense dotted glints` / `sparse filament highlights` （仅用于局部特写组，帮助区分两套笔触） |

### 5.4 示例 caption（10 条）

```
glntwtr, a single dark sailboat, high horizon line, backlit low sun, blue with gold glints, vast negative space
glntwtr, two swimmers seen from above, overhead view no horizon, turquoise and deep navy, small subjects lower left
glntwtr, two yachts at anchor, overhead view no horizon, teal with lime shallows, diagonal sand wedge
glntwtr, an empty shoreline, low oblique coastline, sunrise reflection band, sand beige and dark blue
glntwtr, beach figures wading, low oblique coastline, midday glare, cool blue with orange accents
glntwtr, a moored boat, high horizon line, warm evening glints, dark reef in lower corner
glntwtr, a single sailboat off-center right, high horizon line, backlit low sun, blue with gold glints
glntwtr, swimmers in open water, overhead view no horizon, turquoise and deep navy, dense filament highlights
glntwtr, dense dotted glints on sunlit water, turquoise and deep navy, warm orange accents
glntwtr, white caustic filaments over teal water, lime shallows, sparse filament highlights
```

> 最后两条是局部特写组；其余为整画组。完整词表与批量生成脚本接口见 `tools/caption_vocab.md`。

---

## 6. 训练配置

### 6.1 底模与训练器选型

| 路线 | 训练器 | 显存 | 适用 | 判断 |
|---|---|---|---|---|
| **SDXL 1.0 Base**（主路线，Phase A） | Kohya `sd-scripts` / GUI | 12 GB 可跑 768，16–24 GB 跑 1024 | 风格 LoRA 生态最成熟、参数可复现、迭代便宜 | **先在这条路上验证「风格向量是否成立」** |
| FLUX.1-dev（Phase B） | Kohya `flux_train_network.py` / FluxGym / AI-Toolkit | 24 GB+ | 提示跟随更强、质感更细 | 学习率敏感，风格易过拟合到纹理 |
| FLUX.2 / Qwen-Image / Z-Image（可选） | AI-Toolkit (ostris) | FLUX.2 建议 48 GB | 成品级输出、更强语义 | 成本高，等 Phase A 结论稳定后再上 |

**关键纪律**：训练、评估、推理**始终用同一个底模 checkpoint**。SDXL / SD1.5 / Flux 的 LoRA 互不通用；中途换底模再做对比等于同时改了两个变量。记录底模名称、来源 URL、文件哈希、架构到实验日志。

### 6.2 SDXL 基线超参（`configs/dataset_sdxl.toml` + `configs/train_sdxl.sh`）

| 参数 | 基线 | 可调范围 | 说明 |
|---|---|---|---|
| `network_dim` | 32 | 16–64 | 风格细节多用 32；80 张图上到 64 更容易记忆化 |
| `network_alpha` | 16 | 8–32 | 常取 dim 的一半 |
| `learning_rate` (UNet) | `1e-4` | `5e-5`–`2e-4` | 与优化器成对，别把 AdamW 的 LR 直接搬到 Prodigy |
| `text_encoder_lr` | `5e-5` | `1e-5`–`5e-5` | 绑定触发词；过高会破坏正常提示跟随 |
| optimizer | `AdamW8bit` | Prodigy / Adafactor | 8bit 显著省显存且质量损失可忽略 |
| lr_scheduler | `cosine_with_restarts` | `constant_with_warmup` | warmup 约 5% 步数 |
| resolution | 1024 | 768–1024 | 低于 768 会丢掉定义性的点状纹理 |
| bucketing | on | — | `min_bucket_reso=640`, `max_bucket_reso=1280` |
| `train_batch_size` | 1 | 1–2 | 便于跨实验比较步数 |
| `max_train_steps` | ~1800 | 1200–2400 | 目标每图 60–100 次曝光；以训练器估算为准 |
| precision / 省显存 | `bf16`, `gradient_checkpointing`, `cache_latents` | — | 12 GB 时降 768 或用 fp8 基础 |
| `noise_offset` | 0.035 | 0–0.05 | 对「深色底 + 极高光」的明度结构有帮助，建议 A/B 测 |
| `min_snr_gamma` | 5 | 关闭 / 5 | 稳定训练，可选 |
| 随机水平翻转 | **先关闭** | v2 再开 | 海景本身可翻，但若签名没裁干净会镜像到右下角；先排除变量 |
| `save_every_n_steps` | 200 | 150–250 | 早停靠 checkpoint，不靠 loss |
| `sample_every_n_steps` | 200 | — | 固定 seed，用 `prompts/eval_grid.txt` 的短网格 |

> 若改用 FLUX.1：`network_dim` 16–32、`learning_rate` 在 `5e-5 → 2e-4` 扫描、steps 1000–2500；配置模板见 `configs/train_flux_ai-toolkit.yaml`。

---

## 7. 执行流程

| 步骤 | 动作 | 通过判据 |
|---|---|---|
| 1 | 走完 4.1 授权路径，填 `dataset/manifest.csv` | 每张图有来源与许可字段 |
| 2 | 采集 → 裁签名 → 去重 → 分桶 → 分词标注 | `python tools/audit_dataset.py --root dataset` 全绿 |
| 3 | **Smoke test**：`max_train_steps=40`，小分辨率 | 模型加载、caption 命中、latent 缓存、出样本、ckpt 可打开，**控制台确认 caption 数量与图片数一致**（静默跳过 caption 是最常见的假成功） |
| 4 | 正式训练，每 200 步存 ckpt + 固定 seed 采样 | 样本不空白、不崩坏、与题材相关 |
| 5 | 用第 8 节网格评估每个 ckpt（权重 0.6 / 0.8 / 1.0） | 找到「风格到位 + 还能响应新 prompt」的最早 ckpt |
| 6 | 早停并锁定 `output/` 中的最终权重 | 后期 ckpt 只是更像训练图、却更不听话 → 停止 |
| 7 | 记录实验日志（底模哈希、超参、步数、选中 ckpt、评分） | 可复现 |

**过训练信号**：背景重复、构图锁死、任何 prompt 都出同一片色斑、纹理变硬变糊、颜色漂移、新题材拒绝响应、不带触发词时底模也被改变（泄漏）。若所有 ckpt 都弱，**先查** caption 是否加载、触发词是否一致、底模是否匹配、LR 与图片清晰度，**不要直接加倍步数**。

---

## 8. 评估体系

### 8.1 固定测试网格（`prompts/eval_grid.txt`）

四类 × 每个 ckpt × 三种 LoRA 权重（0.6 / 0.8 / 1.0）× 固定 seed：

| 类型 | 目的 | 示例方向 |
|---|---|---|
| T1 直接触发 | 风格是否出现 | 最简 prompt + 触发词，海面 + 单帆船 |
| T2 泛化 | 风格能否迁移到训练集中没有的题材 | 山间湖、城市水岸、夜景水面、内陆泳池（**训练集里没有**） |
| T3 提示跟随 | 触发词能否与其他要求共存 | 指定视角、数量、时段、主色、留白比例 |
| T4 泄漏 | 不带触发词时是否污染底模 | 完全不含触发词的普通风景 prompt |

### 8.2 结构化评分量表（`eval/scorecard.csv`）

每维度 0–5 分，加权总分 **/ 100**。

| 维度 | 权重 | 0 分 | 5 分 |
|---|---|---|---|
| S1 光斑笔触（圆点 + 焦散细线） | 25 | 平滑渐变/无笔触 | 两套笔触清晰可辨，密度自然 |
| S2 调色板（冷底暖点 + 深色暗部） | 20 | 灰调/偏色 | 青绿—深蓝基底配橙金小点，对比准确 |
| S3 平面化色块与剪影 | 15 | 写实立体、柔和过渡 | 硬边色块分区、斑点过渡、纯剪影 |
| S4 构图与留白 | 10 | 元素堆满、构图锁死 | 极简留白/俯视/斜切可随 prompt 变化 |
| S5 题材泛化（T2） | 15 | 只会画帆船 | 新题材仍保持风格语言 |
| S6 提示跟随与无泄漏（T3/T4） | 15 | 不听提示 / 不带触发词也变 | 精确跟随且底模保持中性 |

| 总分 | 判定 |
|---|---|
| ≥ 80 | 可进入 Phase B（迁移更强底模） |
| 65–79 | 留在 Phase A，做单项消融 |
| < 65 | 回查数据集与 caption，不调步数 |

### 8.3 量化辅助指标（可选自动化）

- **色彩直方图 JS 散度**：对照验证集水面区域的 HSV 色相分布，检验冷底暖点是否还原。
- **局部高频能量 / 局部方差**：衡量点状纹理密度，防止「学成糊状色斑」。
- **CLIP image-image 相似度**：生成图 vs 最近训练图，过高 = 记忆化。
- **pHash 近重复**：检测 ckpt 是否反复吐同一构图。

> Loss 只能说明拟合，**不能**说明风格、泛化与提示跟随。以样本网格证据为准。

---

## 9. 推理配方

**正向模板**

```
glntwtr, <subject>, <view>, <light>, <palette>, <composition>, masterful light on water
```

**负面提示**（对应 2.1 反特征）

```
photorealistic, photo, lens flare, bokeh, watercolor wash, wet paper texture, visible brush sweeping, thick impasto, smooth gradient, soft blending, muddy colors, desaturated, detailed faces, cluttered composition, text, signature, watermark, frame, border
```

| 项 | 建议 |
|---|---|
| LoRA 权重 | 0.65–0.90 起跳；> 1.0 容易出现纹理硬化与构图锁死 |
| CFG / steps（SDXL） | CFG 5–7，DPM++ 2M Karras，28–35 steps |
| 高分辨率修复 | denoise ≈ 0.45；放大能强化点状光斑，过大会把点糊成一片 |
| 光斑密度调节 | prompt 加 `dense dotted glints` / `sparse highlights`，或调权重，二者不要同时大幅改 |
| 构图强控 | 交给 ControlNet，别塞进本 LoRA（见第 11 节） |
| 输出标注 | 对外展示时标明 AI 生成、非官方、与艺术家无关联 |

---

## 10. 风险与合规

| 风险 | 事实 | 应对 |
|---|---|---|
| **版权** | 画家 1958 年生、在世；英国 `CDPA 1988` 艺术作品保护期为作者终生 + 70 年；中国《著作权法》为终生 + 50 年，中英同为《伯尔尼公约》成员国相互保护。作品**仍在保护期内** | 按 4.1 的 A / B / C 三路径选一，不默认「网上能看就能训」 |
| **训练数据合法性** | 2026 年英国政府已放弃 opt-out 式商业 TDM 例外；`s.29A` 仅限**非商业研究 + 合法访问 + 充分署名**，且「sole purpose」门槛高；商业微调、部署、批量评估均无例外可用 | 商用一律走书面授权；保留授权凭证与逐图溯源 |
| **「in the style of」** | 英国上议院 2026 年《AI、版权与创意产业》报告建议新增保护，禁止未经授权的商业风格模仿与数字复刻，并把训练数据透明列为法定义务 | 不用真名做触发词 / 模型名 / 营销语；用中性描述词；输出加 AI 标注 |
| **品牌与虚假关联** | 画家 2025 年与 PITAKA 有商业联名 | 不暗示官方合作、不使用联名视觉资产、不用于同类商品宣传 |
| **数据噪声** | 签名、版画纸边、in-situ 陈设图、同作品多版次 | 4.4 清洗规则 + `tools/audit_dataset.py` 质检 |
| **技术** | 风格过拟合到纹理、构图锁死、题材偏置 | 4.2 分层配比、低 repeats 特写、第 8 节早停判据 |

> 以上为技术风险管理提示，**不构成法律意见**；涉及商用、发布权重或跨境服务前请咨询专业律师。

---

## 11. 迭代路线与扩展接口

方案刻意留出以下接口，便于后续增添而不推翻现有结构：

| 优先级 | 扩展 | 接入点 |
|---|---|---|
| P1 | **风格解耦**：拆成「光斑纹理 LoRA」（特写组为主）与「构图/色块 LoRA」（整图组为主），推理时可分别调权 | `dataset/` 分组 + 两套 `configs/` |
| P1 | **分题材子 LoRA**：wild swim / sailing / shoreline 三个专家，避免单一 LoRA 在题材上互相稀释 | `dataset/` 增加 `group` 字段 |
| P2 | **底模迁移**：Phase A 的 SDXL 结论稳定后，迁移 FLUX.1 → FLUX.2 / Qwen-Image | `configs/train_flux_ai-toolkit.yaml` |
| P2 | **消融实验**：`noise_offset`、特写 repeats 比、`network_dim` 16/32/48、caption dropout 0/0.05/0.1 | `eval/scorecard.csv` 每次一行 |
| P3 | **适配器升级**：DoRA / LoHa / LyCORIS 对比标准 LoRA 的风格容量 | 仅换 `network_module` |
| P3 | **组合控制**：ControlNet 锁构图、IP-Adapter 参考色调，与风格 LoRA 叠加 | 推理端，不污染权重 |
| P3 | **自动化**：`audit_dataset.py` → 采集管线；评分脚本 → 基于 ckpt 的自动早停 | `tools/` 增加脚本，字段兼容 `manifest.csv` |

---

## 附录 A：来源清单

| # | 来源 | 类型 | 用于 | 访问 |
|---|---|---|---|---|
| 1 | Wychwood Art — *Glorious sunrise sailing, River Fowey Harbour* 作品页 | 一手画廊 | 材质、创作流程、自述引语、box canvas | 2026-11-05 |
| 2 | Wychwood Art — *Turquoise bay - small* / *Sail on by* 作品页 | 一手画廊 | 丙烯、Giclée 版次、印象派式描述 | 2026-11-05 |
| 3 | Artienda — *Gordon Hunt \| Seascape Paintings* | 一手画廊 | 题材分类、wild swim / turquoise、RSMA 展览、作品图 | 2026-11-05 |
| 4 | Agora Gallery — *Discovery: Contemporary Art Perspectives from England* (2018) | 评论文字 | 点彩、光与色、平面设计影响、对称与海天关系 | 2026-11-05 |
| 5 | 深圳新闻网 / 深圳Plus / 搜狐 — PITAKA × Gordon Hunt「觉知伏流」联展报道 (2025-12) | 媒体报道 | 45 年从业、深色画布起笔、层层叠色、闪烁笔触 | 2026-11-05 |
| 6 | 今日头条 / 微博 / DigFamily 艺术介绍 | 二手媒体 | 1958 生年、康沃尔灵感（**中等置信度**） | 2026-11-05 |
| 7 | UK Parliament — House of Lords AI & Copyright 报告新闻稿 (2026-03)；Chambers *AI & IP 2026* (UK)；Keystone Law 解读 | 法律/政策 | 商业 TDM 例外、`s.29A`、「in the style of」、透明度 | 2026-11-05 |
| 8 | Kohya sd-scripts 训练指南、AI-Toolkit / FluxGym 生态资料、2026 LoRA 训练实践汇编 | 技术资料 | 超参基线、VRAM 分档、caption 与评估策略 | 2026-11-05 |

**视觉核对样本**（仅用于本地观察，未纳入任何数据集，不随本方案分发）：《Wild Swim》《Sailing the Sparkling Sea》《Anchored Up》三张公开作品图，来自附录 A #3 页面。

## 附录 B：文件索引

| 路径 | 作用 |
|---|---|
| `README.md` | 项目入口、快速开始 |
| `docs/Gordon_Hunt_style_research_and_LoRA_plan.md` | **本文档**：风格研究 + 完整训练方案 |
| `configs/dataset_sdxl.toml` | Kohya 数据集配置（分组 / repeats / buckets） |
| `configs/train_sdxl.sh` | SDXL 训练启动脚本（基线超参） |
| `configs/train_flux_ai-toolkit.yaml` | FLUX 备选配置模板 |
| `prompts/eval_grid.txt` | 四类评估网格 + 推理模板 + negative |
| `tools/caption_vocab.md` | 标注词表、示例、批量生成接口 |
| `tools/audit_dataset.py` | 数据集质检（分辨率 / 去重 / 签名区 / caption / 溯源） |
| `eval/scorecard.csv` | 评分表模板 |
| `dataset/README.md` | 授权与目录规范 |
| `dataset/manifest.csv` | 溯源台账（自行填写） |
| `output/` `samples/` | 权重与采样输出 |
