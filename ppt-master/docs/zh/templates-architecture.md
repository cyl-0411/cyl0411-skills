# 模板架构

本文描述当前 `ppt-master` 安装包采用的三分类模板模型。它与包含 `styles/` 的新版四分类实现不兼容；维护本安装包时，应以这里的 `brand`、`layout`、`deck` 三类以及 `scripts/register_template.py` 为准。

## 三类模板

| `kind` | 目录 | 职责 | 不应主导的内容 |
| --- | --- | --- | --- |
| `brand` | `templates/brands/<id>/` | 品牌身份：颜色、字体、Logo、语气、图标风格 | 页面结构与 SVG 页面清单 |
| `layout` | `templates/layouts/<id>/` | 页面结构：画布、版式、页面类型、SVG 页面清单 | 品牌身份 |
| `deck` | `templates/decks/<id>/` | 完整演示文稿参考：身份、结构和模板概述 | 无；它是完整基线 |

每个模板目录必须包含 `design_spec.md`，并在 YAML frontmatter 中声明唯一的 `kind`。资源文件与规范放在同一模板目录中，保证模板复制后仍然自包含。

## 段所有权

`design_spec.md` 分成三个逻辑段。融合模板时以整段替换为默认规则，不进行隐式字段级混合。

| 段 | 典型内容 | 融合时的所有者 |
| --- | --- | --- |
| Identity | Color Scheme、Typography、Logo、Voice & Tone、Icon Style | `brand` |
| Structure | Canvas、Page Structure、Page Types、SVG Roster | `layout` |
| Middle | Template Overview、用途与设计意图 | `deck` |

单个 `deck` 同时提供三个段；显式提供 `brand` 或 `layout` 时，它们分别覆盖 `deck` 的 Identity 或 Structure 段。

## 最小 frontmatter

### Brand

```yaml
---
kind: brand
name: example-brand
summary: Short identity description
primary_color: "#0057B8"
---
```

正文应给出颜色、字体、Logo、语气和图标风格。不要加入页面清单。

### Layout

```yaml
---
kind: layout
name: example-layout
summary: Short structure description
canvas_format: ppt169
page_count: 8
page_types:
  - cover
  - section
  - content
  - closing
---
```

正文应描述画布、页面结构、页面类型和 SVG roster；对应 SVG 文件保存在同一模板目录。

### Deck

```yaml
---
kind: deck
name: example-deck
summary: Short full-deck description
canvas_format: ppt169
page_count: 12
primary_color: "#0057B8"
---
```

正文同时包含 Identity、Structure 和 Template Overview，资源与完整 SVG roster 随目录一起保存。

## 索引字段

`scripts/register_template.py` 是索引结构的机器真值。重建索引时写入以下字段：

| 索引 | 条目字段 |
| --- | --- |
| `templates/brands/brands_index.json` | `summary`, `primary_color` |
| `templates/layouts/layouts_index.json` | `summary`, `canvas_format`, `page_count`, `page_types[]` |
| `templates/decks/decks_index.json` | `summary`, `canvas_format`, `page_count`, `primary_color` |

不要向索引手工加入 registrar 不生成的字段。

## 触发规则

模板流程仅由用户明确提供的模板目录路径触发。裸模板名、品牌名或风格描述不会自动解析为目录，也不会触发模糊匹配。用户询问可用模板时，可以读取索引并列出名称和路径；只有用户随后提供具体路径才进入模板流程。

## 多模板融合

| 组合 | Identity | Structure | Middle |
| --- | --- | --- | --- |
| brand | brand | 自由设计 | 无 |
| layout | 自由设计 | layout | 无 |
| deck | deck | deck | deck |
| brand + layout | brand | layout | 无 |
| brand + deck | brand | deck | deck |
| layout + deck | deck | layout | deck |
| brand + layout + deck | brand | layout | deck |

如果用户给出两个同类模板，先列出段级差异并让用户选择一个来源，或逐段解决冲突。不要用路径顺序隐式决定胜者。最多支持两个同类来源。

融合后的 `design_spec.md` 应在标题后记录来源和冲突解决结果：

```markdown
> **Fused from:**
> - deck: `templates/decks/example/` (base)
> - brand: `templates/brands/example/` (identity override)
> - layout: `templates/layouts/example/` (structure override)
> - conflicts resolved: Color Scheme from brand (user choice)
```

单路径模板不需要 provenance 块。

## 验证

修改模板后，分别执行只读索引检查：

```bash
python scripts/register_template.py --rebuild-all --kind brand --dry-run
python scripts/register_template.py --rebuild-all --kind layout --dry-run
python scripts/register_template.py --rebuild-all --kind deck --dry-run
```

同时确认 `design_spec.md` 的 `kind` 与物理目录一致，所有引用的 SVG、Logo 和资源均位于模板目录内。
