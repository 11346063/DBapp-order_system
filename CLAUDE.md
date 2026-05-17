# Agentic Harness: Initialization Protocol (🟥 MANDATORY 🟥)

> **作為高階 Orchestrator Agent (Sisyphus)，請在任何 Session 開始時，嚴格遵守以下程序：**

## 1. 狀態同步與立即回報 (State Sync & Immediate Response)
1. **第一動作**：呼叫 Read Tool 讀取 `docs/progress.md` 與本檔案下方的專案概述。
2. **強制中斷點**：讀取完畢後，**必須立即發送一則文字訊息給使用者**，嚴禁在第一則訊息中直接開始寫 Code 或完成整個任務！
3. **模型路由 (Model Routing) 策略**：
   - **高階架構/複雜 Bug**：優先呼叫 `Oracle` 模型進行戰略規劃。
   - **程式碼實作/重構**：使用預設 Agent 執行。
   - **文檔/簡單修復**：使用 `quick` 模式。
4. **首則訊息格式**：
   > **當前進度摘要**：[簡短描述讀到的狀態]
   > **線束檢查**：[執行 `python scripts/harness_orchestrator.py` 的結果]
   > **行動計畫**：[基於模型路由的開發路徑]
5. **Karpathy 四原則**：動手前先想清楚、夠用就好、外科手術式修改、目標驅動執行（細節見 rules.md §15，或呼叫 `/karpathy-guidelines`）

## 2. Harness CLI 操作規範

**在執行任何 `scripts/harness/` 下的指令之前，你 MUST 先讀取：**

```
.opencode/references/cli-reference.md
```

此文件包含所有 harness action（audit / compact / clean / sandbox / validate）的完整參數表、輸入輸出格式、以及常見錯誤。**不讀此文件就執行指令 = 參數錯誤。NEVER 憑記憶或猜測下參數。**

常用指令速查（完整參數見 cli-reference.md）：

| 用途 | 指令 |
|------|------|
| 健康檢查 | `python scripts/harness/harness_orchestrator.py --action audit` |
| 清理過期檔案 | `python scripts/harness/harness_orchestrator.py --action clean --execute` |
| 壓縮上下文 | `python scripts/harness/harness_orchestrator.py --action compact --input <file>` |
| 安全執行指令 | `python scripts/harness/harness_orchestrator.py --action sandbox --command "..." --execute` |
| 驗證程式碼語法 | `python scripts/harness/harness_orchestrator.py --action validate --code "..." --language python` |

## 3. 物理約束與護欄
- **[CONTEXT SAFETY PROTOCOL]**: 
  - **Observation Masking**: 超過 2000 tokens 的工具輸出嚴禁直接顯示。必須導向 `.opencode/observations/` 並在對話中提供摘要。
  - **Scratch Pad Usage**: 中間過程、大型 log 或臨時知識請寫入 `.opencode/scratch/`。
  - **Dynamic Loading**: 優先使用「指引索引 (Skill Pointers)」動態加載規範，避免 Context Window 內塞入過多靜態規則。
- **原子化提交 (Atomic Commits)**：每完成一個邏輯單元，請立即進行 `git commit`。
- **物理檢查**：所有變更必須通過專案測試。
- **品質門哨 (Quality Gate)**：當功能開發完成，準備結案前，**👉 必須載入 `.opencode/skills/dark-factory-review.md`** 執行對抗審查與自癒循環。
- **結尾手續**：結束前必須執行 `harness_orchestrator.py --action audit` 確保無紅字。


---

# DBapp-menu - Agent Knowledge Base

## 專案概述
[在此填寫專案目標、技術棧與核心架構]

## 核心規範與指引 (Skills Index)

> ⚠️ **請優先載入對應的 Skill 以獲取最新規範與踩坑紀錄 (Agentic Harness: Progressive Disclosure)**。

### 開發流程
- **Git 提交規範**：👉 載入 `.opencode/skills/git-conventions.md`

### 系統架構與模組細節
- 基礎架構與資料庫規範：👉 載入 `.opencode/skills/architecture.md` (範例)
- 業務模組 A：👉 載入 `.opencode/skills/module-a.md` (範例)
- **DRF + JWT API 開發**：👉 載入 `.claude/skills/django-restful.md`

---
*此文件由 Sisyphus Harness 持續維護*
