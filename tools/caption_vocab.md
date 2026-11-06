# Caption 规范与词表

> 对应主方案第 5 节。核心原则：**写变化，不写常量；写画得出的，不写作画过程。**

## 1. 硬性规则

| 规则 | 说明 |
|---|---|
| 触发词 | `glntwtr`，**每条首位**，配合 `keep_tokens=1` |
| 长度 | 8–16 个英文词（质检脚本允许 6–22） |
| 编码 | UTF-8，与图片同名同目录，`xxx.jpg` → `xxx.txt` |
| 语言 | 英文短句（SDXL）/ 短标签式短语（Flux） |
| 结构 | `trigger, subject, view, light, palette, composition` |
| 差异 | 每条必须不同；启用 `shuffle_caption` + `caption_dropout_rate=0.05` |

**不要用在世艺术家真名做触发词**：既不干净（基础模型可能有姓名先验），也会在模型命名/发布时制造「官方关联」的合规风险。

## 2. 禁用词（质检脚本会直接报 ERROR）

```
gordon hunt / by gordon          <- 真名、署名关联
watercolor / watercolour         <- 材料误标（实为丙烯）
acrylic / oil painting / impasto<- 材质常量，且模型学不到「作画顺序」
pointillist / pointillism        <- 风格常量，写满每张会架空触发词
sparkling / painting / brushstroke
happy / holiday feeling          <- 情绪，不可学习
```

> 反复写同一个风格词，模型会依赖那个词而忽略触发词，最终表现为「LoRA 很弱」。
> **画风靠省略来学**：所有样本共有的东西，一条都不要写。

## 3. 变量词表（只写这些维度）

| 维度 | 取值 |
|---|---|
| `subject` | `a single sailboat` ／ `two yachts` ／ `two swimmers` ／ `a single swimmer` ／ `beach figures wading` ／ `a moored boat` ／ `an empty shoreline` ／ `a quiet beach with one figure` ／ `a still lake` ／ `a city waterfront` ／ `an indoor pool` |
| `view` | `high horizon line` ／ `overhead view, no horizon` ／ `low oblique coastline` ／ `eye-level sea level` |
| `light` | `backlit low sun` ／ `midday glare` ／ `sunrise reflection band` ／ `warm evening glints` ／ `dusk reflections` |
| `palette` | `turquoise and deep navy` ／ `teal with lime shallows` ／ `blue with gold glints` ／ `cool blue with orange accents` ／ `sand beige and dark blue` |
| `composition` | `vast negative space` ／ `small subject off-center left` ／ `small subject off-center right` ／ `diagonal sand wedge` ／ `dark reef in lower corner` ／ `minimal composition` |
| `texture-state`（**仅局部特写组**） | `dense dotted glints` ／ `sparse filament highlights` ／ `white caustic filaments` |

## 4. 示例（10 条）

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

最后两条属 `3_dabs` / `3_filaments` 局部特写组；其余属 `10_full` 整画组。

## 5. 批量生成接口（留扩展）

自动打标（WD14 Tagger v3 / Florence-2 / JoyCaption）只能当草稿，**必须人工逐条复核**。建议的接口形态：

```python
# tools/make_captions.py  (v2 扩展，当前未实现)
# 输入: dataset/manifest.csv 中的 group 字段 + 人工填的 subject/view/light/palette/composition
# 输出: 每张图同名 .txt，首位恒为 TRIGGER
from pathlib import Path
TRIGGER = "glntwtr"
def build(row):
    fields = [TRIGGER, row["subject"], row["view"], row["light"],
              row["palette"], row["composition"]]
    return ", ".join(f for f in fields if f)
# 约束: 不写入任何「禁用词」；同组 caption 不得重复；每组抽样 10 条人工复核
```

接入点：`dataset/manifest.csv` 增加 `subject / view / light / palette / composition` 五列即可，不影响现有质检字段。

## 6. 人工复核清单（每批 10 条抽看）

- [ ] 触发词在首位且拼写一致（`glntwtr`，无大小写/复数变体）
- [ ] 没有禁用词
- [ ] 描述与画面**实际内容**一致（别把「俯视」写成「水平线构图」）
- [ ] 主色描述与画面一致（绿松石 / 青绿 / 金橙 / 米黄）
- [ ] 两条 caption 之间确有差异
- [ ] 局部特写组额外标了 `texture-state`
