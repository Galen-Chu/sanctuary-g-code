# 開發優化盤點 Backlog

> 2026-11-16 盤點（Phase 1 後首次歸檔）。本文件是**跨階段**的開發與優化清單：README 的 Roadmap 是階段骨架，這裡收集具體工作項、生態整合與工程債。每次盤點時更新；完成的項目移入 Roadmap 對應階段的勾選紀錄。設計層的未決問題仍留在 [DESIGN.md](DESIGN.md) §8——本清單是「要做什麼」，那裡是「怎麼設計」。

## 1. 生成品質與統計（Phase 2 核心）

- **統計驗收**（DESIGN 開放問題 1）：同一 preset 跨 ~100 顆種子的分布斷言——最近水源距離中位數、危險區覆蓋率、巡邏時段涵蓋、庇護所-資源可達性。界線必須由生成規則的理論值校準（例：泊松盤間距的期望），不是調到測試變綠為止。
- **世界群模式（population mode）**：`--count N` 從主種子派生 N 個世界種子，輸出 N 份 TOML＋一份世界群 manifest（群級 provenance：preset@版本、種子範圍、生成器版本）。**這是 M1 的世界側半邊**（見 §2）。
- **掠食者行程策略庫**：目前只有固定時段 {11, 14, 17, 20}＋抖動一種；候選——隨機掃描（不可預測）、晝夜規律（可學習）、區域集中（迫使遷移）。每種策略應表現為行為可區分的統計特徵（給 Unbodysoma Phase 3 學習實驗當題目）。
- **preset 的參數面**：preset 目前是常數組合；族群層的「世界維度變異」（面積、貧瘠度、危險密度連續抽樣）可作為 preset 之上的分布層。

## 2. 生態整合（跨專案）

- **M1「N 個體 × M 世界」的組裝**：Unbodysoma 的 `run_population`（已就位）× 本專案的 population mode（§1）——每個體配一個世界、種子成對派生，實驗 manifest 同時記錄兩側 provenance。兩側基礎設施齊備，缺的只是這層組裝協定。
- **世界 provenance 進執行紀錄**：Unbodysoma 側要把外部世界的（產生器、preset@版本、種子、SHA-256）寫進 `meta.json`（其 BACKLOG §4）；本專案側確保 TOML 檔頭資訊完整即可（已滿足，追蹤對方進度）。
- **世界群標本**：統計驗收的輸出（跨種子分布數據）→ specimen-g-code 的世界標本（其 Phase 4 適配器）。

## 3. 幾何與地形（Phase 3）

- **地形場＋可達性**：高度場（值雜訊即可）影響植放規則與移動成本——abyssal-garden `CLEARS`（淨空保證）的對應物，也是其最值得抄的工程模式（DESIGN 開放問題 2）。
- **資源季節動態**：regrow 速率、水源水量隨季節參數變化（現在是常數）；輸出進 TOML 的對應欄位需要 Unbodysoma 端 `FoodPatch` 語意擴充（鍵集契約變更——依 ADR-0010 需雙邊同步）。
- **2D → 2.5D**：坡度場先於完整高度場（風險較小、對植放規則已足夠）。

## 4. 3D 與前端（Phase 4，abyssal 血統的歸宿）

- **高度場輸出**：3D 密度場的柵格化版本，作為 Phase 3 地形的自然延伸。
- **WebGPU 預覽頁**：輸出 JSON（座標＋場參數），前端以**同源雜訊常數**重算場來鋪渲染——`scripts/verify_lineage.*` 已證明種子跨語言逐位元共享，預覽頁是這個投資的兌現（DESIGN 開放問題 3）。
- **品質分層**：比照來源專案的自適應策略（動態解析度、繪製距離）——只在預覽頁存在後才有意義（Phase 5）。

## 5. 工程與基礎設施

- **`py.typed` 標記**：✅ 完成（2026-11-18）——標記已入 `src/sanctuary/`，wheel 打包內容驗證通過；CI 同日補強跨平台矩陣（ubuntu/windows/macos × Python 3.11–3.14）與 ruff/mypy 釘版。
- **v0.1.0 release tag**：版本化契約已定案、preset 全部 `@1`——Phase 2（population mode＋統計驗收）落地後打 tag 最乾淨；若 Phase 2 前有外部消費者需求可提前。
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
