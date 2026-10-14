# 用語集

本編の言葉と、コードに現れる名前を結び付けるための索引です。
最初から暗記せず、必要なときに戻ってきてください。

| 用語 | このプロジェクトでの意味 | 関連するコード・資料 |
|---|---|---|
| AUTOSAR CP | Classic Platform。車載ソフトウェアの共通基盤を定める枠組み。OS はその一部 | [出典と対象版](https://github.com/4ge32/lean-cp-os/blob/main/docs/SOURCES.md) |
| OSEK OS | 現在の基本タスク制御の動作基準。固定版は 2.2.3 | 同上 |
| Basic Task / 基本タスク | 起動し、実行し、終了するタスク。イベントを待つ `WAITING` 状態を持たない | `TaskConfig` |
| Extended Task / 拡張タスク | イベントを待って再開できるタスク。現在は未実装 | [対象範囲](https://github.com/4ge32/lean-cp-os/blob/main/docs/DESIGN.md) |
| 起動要求 / activation | タスクの仕事を 1 回実行してほしいという依頼。タスクの定義とは別物 | `Frame`、`activeCount` |
| SUSPENDED / 休止 | 未完了の起動要求がない | `taskState` の値 `1` |
| READY / 実行可能 | 起動済みで、CPU に選択されるのを待っている | `taskState` の値 `2` |
| RUNNING / 実行中 | 現在 CPU に選ばれているタスク | `taskState` の値 `3` |
| WAITING / 待ち | 拡張タスクがイベントを待つ状態。`READY` と異なり、現在のモデルにない | [基本タスクの説明](https://github.com/4ge32/lean-cp-os/blob/main/docs/TASK_CONTROL.md) |
| 優先度 | 数値が大きいほど先に選ぶ設定 | `TaskConfig.priority` |
| FIFO | 同じ優先度では先に届いた要求を先に選ぶ順序 | `choose`、`choose_fifo_head` |
| プリエンプション / 中断 | 高優先度のタスクへ CPU を渡し、元の仕事の続きを保存すること | `mayPreempt` |
| 継続 / continuation | 中断した仕事を続けるための情報。モデルの `pc` と実機の保存文脈は異なる表現 | `Frame.pc`、`context.S` |
| discard | 成功した終了・連鎖の後で、呼び出し元の続きを破棄する指示 | `Result.discard` |
| 不変条件 / invariant | 初期状態で成立し、操作しても保たれる性質 | `Valid`、`reachable_valid` |
| 定理 / theorem | 前提から結論を導くことを Lean が検査する宣言 | `Task/Proofs.lean` |
| オラクル | 比較の期待結果を計算する独立実装。ここでは Python | `tests/test_task_control.py` |
| ABI | 関数呼び出しや値の表現を、言語やバイナリーの境界で共有する取り決め | [API 一覧](api.md) |
| 精密化 / refinement | 抽象モデルと具体実装の振る舞いの対応を示すこと。現在の機械実装への対応はテストで確認 | [検証の読み方](../09-evidence.md) |
| トレーサビリティ | 要求から根拠資料、実装、証明、テストをたどれる対応関係 | `trace/`、`trace.json` |
| 証拠 / evidence | 対象ソース、ツール、実行結果、ログ、ハッシュを記録した成果物 | `evidence/` |
| ISR | 割り込み処理。モデルには入退場と深さがあるが、実ハードウェア割り込みは未実装 | `enterISR`、`exitISR` |
| WCET | 最悪実行時間。現在は上限を証明していない | [実行系の境界](https://github.com/4ge32/lean-cp-os/blob/main/docs/RUNTIME.md) |

一般モデルの定義は [Task/Model.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Model.lean)、
証明は [Task/Proofs.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Proofs.lean)で確認できます。
