# 70篇插图英语阅读小册

70篇均已完成。每篇包含专属水彩插图、纯净英文原文、完整中文译文、22项核心词汇、其余文中词汇、4道回想练习和五点文章主线。

70份独立PDF共467页；按推荐顺序编为7册合订PDF，每册10篇，共474页（含7页可点击目录）。保留原篇号。PDF为176×250毫米B5，字体嵌入，文字可搜索复制。

## 下载与阅读

在[完整成果Release](https://github.com/alienalgorithm/postgraduate-vocabulary/releases/tag/reading-complete-2026.11.13-v1)下载全部材料或分类包。七册合订PDF也可单独下载。

- `production/01`至`production/70`：每篇正式PDF、同一PDF的逐页PNG预览及版面核验记录。
- `volumes/01`至`volumes/07`：合订PDF、目录实页预览及核验记录。
- `illustrations`：70张原始插图及生成、返工记录。第01篇沿用已确认的`01-preview.png`。
- `content/articles`：70篇完整双语文稿、词汇、题目及最新版简述。
- `sources`：与文稿对应的原文、重点词和最新简述。
- `reviews`与`progress`：逐篇交叉审校及最终本地完整性记录。
- `manifest.json`：所有正式PDF、插图和467张预览的SHA-256。
- `recommended-order.json`：推荐阅读顺序，只调整阅读顺序，保留原篇号。

预览PNG直接渲染自各自的正式PDF，均已核对；下载正式小册子使用PDF文件。

## 核验与复现

安装Python依赖后检查已交付文件，不会重新生成PDF：

```bash
python -m pip install -r requirements.txt
python verify_archive.py
```

仅检查70篇源文稿：`python verify_archive.py --sources-only`。

需要主动重新排版时，运行`python build_all70.py --force`；原交付PDF和其SHA-256是本版的正式依据。第01篇会从`output`复制已确认的冻结PDF。`python build_volumes.py`可按已审定顺序重新合订。字体文件及其许可附在`fonts`。

英文原文固定依据此前视频定稿提交`9374187e740fcefef39e42259a2f057ae504ebc9`。本次小册子的中文用语、史实澄清和简述修正记录见`booklet-terminology-corrections.json`；没有为归档重新编码视频或改动配音。
