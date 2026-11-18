# 開發優化盤點 Backlog

> 2026-11-16 盤點（Phase 1 後首次歸檔）。本文件是**跨階段**的開發與優化清單：README 的 Roadmap 是階段骨架，這裡收集具體工作項、生態整合與工程債。每次盤點時更新；完成的項目移入 Roadmap 對應階段的勾選紀錄。設計層的未決問題仍留在 [DESIGN.md](DESIGN.md) §6——本清單是「要做什麼」，那裡是「怎麼設計」。
> 2026-11-18 方向修訂：M1 降位為拉動即用的消費者整合；四層架構定案（核心／可組合系統／圖書館／轉接器，DESIGN §1）；Phase 2 重排為「統計驗收 → 架構核心 → 內容系統」。

## 1. 生成品質、統計與架構（Phase 2 核心）

- **統計驗收**（DESIGN 開放問題 1）：✅ v1 完成（2026-11-18）——`stats.py` 四項指標＋可執行理論中心（泊松參考、獨立圓盤覆蓋）×文件化因子帶；`--fingerprint` CLI；實測比值與觀察記錄入 DESIGN §5。遺留：帶寬隨理論收緊、圖論可達性量測、指紋入標本索引（架構核心）。
- **架構核心：系統模組化＋世界原型**：✅ v1 完成（2026-11-18）——`systems.py` 五註冊系統（`Generation`／`System` 介面＝DESIGN 開放問題 4 的答案，重組不改位元組：150 世界逐位元驗證）；`Preset.systems` 組合宣告（kelp-basin 收縮轉架構級）；`library.py`：`--index` 原型庫 JSON＋`--fingerprint --json` 標本卡（(seed, archetype@version, 指紋)——只存索引卡、按需重生成）；`toml_out.TOML_SYSTEMS` 能力宣告＋超出即報錯。遺留：完整世界 JSON（隨 WebGPU 預覽）、標本累積工具／specimen-g-code 攝入、第一個以註冊系統形式落地的新內容（掠食者策略庫）。
- **世界群模式（population mode）**：✅ 完成（2026-11-18）——`--count N`＋`population.toml` manifest（群級 provenance、逐檔 SHA-256），派生規則 `master + i` 已入 DESIGN §2 第 6 點。**M1 的世界側半邊就位**。
- **掠食者行程策略庫**（以註冊系統形式落地——模組化之後的第一個新內容）：目前只有固定時段 {11, 14, 17, 20}＋抖動一種；候選——隨機掃描（不可預測）、晝夜規律（可學習）、區域集中（迫使遷移）。每種策略應表現為行為可區分的統計特徵（給 Unbodysoma Phase 3 學習實驗當題目）。
- **archetype 的參數面**：preset 目前是常數組合；族群層的「世界維度變異」（面積、貧瘠度、危險密度連續抽樣）可作為原型之上的分布層。

## 2. 生態整合（跨專案）

- **M1「N 個體 × M 世界」的組裝（已降位，2026-11-18）**：從開發里程碑改為**拉動即用的消費者整合**——Unbodysoma `run_population` × 本專案 population mode 兩側基礎設施已就緒（世界側載體 `population.toml` 已定案，剩對方讀取 manifest 的協定），需要行為層回饋時再組裝。**世界詞彙的擴張不等待它。**
- **世界 provenance 進執行紀錄**：Unbodysoma 側要把外部世界的（產生器、preset@版本、種子、SHA-256）寫進 `meta.json`（其 BACKLOG §4）；本專案側確保 TOML 檔頭資訊完整即可（已滿足，追蹤對方進度）。
- **世界群標本**：統計驗收的輸出（跨種子分布數據＝原型指紋）餵標本索引（§1 架構核心）→ specimen-g-code 的世界標本（其 Phase 4 適配器）。

## 3. 幾何與地形（Phase 3）

- **地形場＋可達性**：高度場（值雜訊即可）影響植放規則與移動成本——abyssal-garden `CLEARS`（淨空保證）的對應物，也是其最值得抄的工程模式（DESIGN 開放問題 2）。
- **資源季節動態**：regrow 速率、水源水量隨季節參數變化（現在是常數）；以註冊系統形式先落核心＋JSON 轉接器，TOML 鍵集（Unbodysoma 端 `FoodPatch` 語意擴充，ADR-0010）跟上即接——過渡期由轉接器能力宣告（DESIGN §4）處理降級，不再擋路。
- **2D → 2.5D**：坡度場先於完整高度場（風險較小、對植放規則已足夠）。

## 4. 3D 與前端（Phase 4，abyssal 血統的歸宿）

- **高度場輸出**：3D 密度場的柵格化版本，作為 Phase 3 地形的自然延伸。
- **WebGPU 預覽頁**：輸出 JSON（座標＋場參數），前端以**同源雜訊常數**重算場來鋪渲染——`scripts/verify_lineage.*` 已證明種子跨語言逐位元共享，預覽頁是這個投資的兌現（DESIGN 開放問題 3）。
- **品質分層**：比照來源專案的自適應策略（動態解析度、繪製距離）——只在預覽頁存在後才有意義（Phase 5）。

## 5. 工程與基礎設施

- **`py.typed` 標記**：✅ 完成（2026-11-18）——標記已入 `src/sanctuary/`，wheel 打包內容驗證通過；CI 同日補強跨平台矩陣（ubuntu/windows/macos × Python 3.11–3.14）與 ruff/mypy 釘版。
- **v0.2.0 release tag**：版本化契約已定案、preset 全部 `@1`。population mode 落地時版本已升至 0.2.0（manifest 需要如實的生成器版本；golden 隨檔頭版本戳記重生成）——統計驗收完成後打 tag 最乾淨。
- **CI 的 Node 作業（選配）**：把 `verify_lineage.mjs` 的跨語言比對納入 CI（需要 node runner；目前是文件化的手動步驟）。風險低但非必要——血統已由 Python 側的 golden 常數（`test_js_lineage`）單向釘死。
- **GitHub repo 的 description／topics**：定案（2026-11-18，本機無 gh 指令待套用）——
  description："Deterministic procedural world generator: seed + preset in, a complete reproducible world out — the habitat half of the Unbodysoma ecosystem."
  topics：`procedural-generation, worldgen, deterministic, simulation, python`。

## 6. 已回答的設計問題（歸檔）

| 舊問題 | 答案 |
|---|---|
| preset 版本化：世界要帶版本資訊嗎？ | 已定案（2026-11-16）：`preset@version` provenance 契約——`Preset.version` bump 制、輸出檔頭標注、DESIGN §2 第 5 點 |
| 世界產生器放哪個專案？（Uniconsign vs Unbodysoma vs 獨立） | 已定案：獨立專案（本專案），邊界見 Unbodysoma ADR-0010 |
| 模板與 Unbodysoma 的程式相依？ | 已定案：零相依——耦合只存在於 TOML 鍵集契約（雙邊測試把關） |
| M1 是開發里程碑嗎？ | 已定案（2026-11-18）：降位為拉動即用的消費者整合；開發節奏以世界詞彙為核心，需要行為回饋時才組裝 |
| 世界架構如何擴張／收縮？ | 已定案（2026-11-18）：四層架構（核心／可組合系統／圖書館／轉接器）；archetype＝系統組合＋參數，重組不改位元組——詳 DESIGN §1、§3、§4 |
