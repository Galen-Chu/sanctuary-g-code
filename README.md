# 🌿 Sanctuary G-Code

> **"Every seed deserves a world to live in."** · 「給每顆種子一個可棲身的世界。」

---

## 🧭 這是什麼？ · What It Is

Sanctuary 是一個**決定論的程序化世界產生器**：輸入一顆種子與一個預設，輸出一個完整、可重現的模擬環境——今天就輸出 [Unbodysoma](https://github.com/Galen-Chu/Unbodysoma) 可直接執行的情境檔。

G-Code 生態系的角色分工：**Unbodysoma 給身體與心智，Sanctuary 給世界**。生物體不該永遠住在一張手工擺好的地圖上；同一套規則、不同種子，就該長出佈局不同但統計性質相似的世界。

Sanctuary is a **deterministic procedural world generator**: seed + preset in, a
complete reproducible environment out — today as a runnable Unbodysoma scenario
file. In this ecosystem, Unbodysoma builds the body and mind; Sanctuary builds
the world it lives in.

```
seed ──► per-system RNG streams (mulberry32)
              │
    ┌─────────┼──────────────┬──────────────┐
    ▼         ▼              ▼              ▼
 fertility  wetness       barren ground   daily schedule
 (fbm 值雜訊)  (fbm 值雜訊)    (fbm 值雜訊)     (巡邏掠食者)
    │         │              │              │
    ▼         ▼              ▼              ▼
 食物斑塊    水源           常駐危險區        定時危險區
    └─────────┴──────┬───────┴──────────────┘
                    ▼
        植放規則（最小間距、淨空、庇護所旁）
                    ▼
              World（純資料）
                    ▼
        轉接器：Unbodysoma TOML ·（未來：JSON、WebGPU 預覽）
```

## 🔒 設計原則 · Design Principles

| 原則 | 意義 |
|------|------|
| **Deterministic by default** | 同一顆種子 → 逐位元相同的輸出，跨平台、跨 Python 版本（golden test 把關） |
| **Streams, not globals** | 每個生成系統一條獨立亂數流：改食物的邏輯，水與危險區的數字一個都不動 |
| **Adapters, not frameworks** | 核心輸出純資料的 `World`；TOML／JSON／預覽都是轉接器，契約見 `docs/DESIGN.md` |
| **Zero-dependency core** | 核心只用 Python 標準函式庫 |
| **Rational grounding** | 每個常數與規則在 `docs/DESIGN.md` 有出處或理由 |

**血統 Lineage**：程序化管線（雜訊、拒絕採樣、per-system 亂數流、淨空規則）移植自
[Noniv/abyssal-garden](https://github.com/Noniv/abyssal-garden)（MIT）——單檔 WebGPU
程序化海底世界。管線分析見 Unbodysoma 的
[WORLDGEN.md](https://github.com/Galen-Chu/Unbodysoma/blob/main/docs/WORLDGEN.md)。

## 🚀 Quick Start · 快速開始

```bash
git clone https://github.com/Galen-Chu/sanctuary-g-code.git
cd sanctuary-g-code
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

sanctuary --list-presets
sanctuary --seed 1 --preset meadow --out world.toml
python -m pytest                                     # 22 tests, 含 golden 決定論測試
```

不裝也行：`PYTHONPATH=src python -m sanctuary …`（PowerShell：`$env:PYTHONPATH="src"`）。

餵給 Unbodysoma：

```bash
cd ../Unbodysoma && pip install -e ".[dev]"
python -m unbodysoma run <path-to>/world.toml --out runs/world_s1
```

## 📦 Module Map · 模組地圖

| Module | Focus |
|--------|-------|
| `sanctuary/rng.py` | mulberry32 與 per-system 串流（移植自 abyssal-garden 的 `rnd`/`rseed`） |
| `sanctuary/noise.py` | 值雜訊、fbm、smoothstep（同源移植） |
| `sanctuary/world.py` | `World` 與實體 dataclass——Unbodysoma `world/grid.py` 的鏡像 |
| `sanctuary/presets.py` | 預設集：meadow / kelp-basin / dryland |
| `sanctuary/generate.py` | 生成本體：密度場＋拒絕採樣＋植放規則 |
| `sanctuary/toml_out.py` | Unbodysoma 情境檔轉接器（相容契約） |
| `sanctuary/__main__.py` | CLI |

測試分三層：決定論與獨立性（`test_rng`）、生成不變量（`test_generate`：數量、邊界、
間距、庇護所安全）、契約（`test_toml`：tomllib 往返＋golden 逐位元比對）。

## 🔄 Related Projects · 關聯專案

| Repository | Relationship · 關係 |
|-----------|-------------------|
| [Unbodysoma](https://github.com/Galen-Chu/Unbodysoma) | **消費者**：`world.toml` 的執行引擎；其 `docs/WORLDGEN.md` 是本專案的設計緣起 |
| [panopticon-g-code](https://github.com/Galen-Chu/panopticon-g-code) | 兄弟專案：它觀察生態，本專案建造棲地 |
| [Noniv/abyssal-garden](https://github.com/Noniv/abyssal-garden) | 管線血統來源（MIT），演算法移植出處 |

## 🗺️ Roadmap

- [x] **Phase 1（本骨架）**：決定論 2D 世界生成、Unbodysoma TOML 轉接器、golden 測試、CI
- [ ] **Phase 2**：統計不變量（跨種子的分布層級驗收）；族群模式（一次生成 N 個世界）；掠食者行程的策略庫
- [ ] **Phase 3**：地形場（可通行性影響植放）；資源季節動態；更豐富的 preset
- [ ] **Phase 4**：3D 密度場（高度場輸出）＋ WebGPU 預覽頁（abyssal-garden 血統的歸宿）
- [ ] **Phase 5**：品質分層與基準（比照來源專案的自適應策略）

細節與開放問題見 [docs/DESIGN.md](docs/DESIGN.md)。

## 🌐 Global Constraints

繼承自 G-Code 生態系：

- **Bilingual Imperative**：輸出雙語（English + 繁體中文）
- **CLI-First**：headless、終端可跑、cron 相容
- **Rational Grounding**：技術語言，不神祕主義
- **Reproducibility Required**：任何輸出都能由（種子, 預設）重建

## 📄 License

MIT — see [LICENSE](LICENSE)。
