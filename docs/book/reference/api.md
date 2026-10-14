# API 一覧

ここでは設定可能な基本タスクモデルの操作を整理します。
OSEK の標準ヘッダーや AUTOSAR のバイナリー互換を提供する API 一覧ではありません。
固定 3 タスクの入門モデル `LeanCpOs` と、一般モデル `LeanCpOs.TaskControl` は区別してください。

## 6 つのサービス

以下は `LeanCpOs.TaskControl` の関数です。
`cfg` は静的設定、`s` は状態、`target` は 0 始まりのタスク ID、`ctx` は呼び出し条件です。

| サービス | Lean の呼び出し | 成功時の効果 |
|---|---|---|
| ActivateTask | `activate cfg s target ctx` | 起動要求を 1 個追加し、条件に応じて高優先度へ切り替える |
| TerminateTask | `terminate cfg s ctx` | 現在の起動要求を終了し、次を選ぶ。`discard = true` |
| ChainTask | `chain cfg s target ctx` | 現在の要求を終了し、対象の新しい要求を追加する。`discard = true` |
| Schedule | `schedule cfg s ctx` | 明示的に高優先度の実行可能タスクへ譲る。同順位へは譲らない |
| GetTaskID | `getTaskID s ctx` | 状態を変えず、実行中 ID に 1 を加えた値を返す。なしは `0` |
| GetTaskState | `getTaskState cfg s target ctx` | 状態を変えず、対象の状態値を返す |

`GetTaskState` の結果は `1 = SUSPENDED`、`2 = READY`、`3 = RUNNING` です。
追加の起動要求が待っていても、そのタスクが現在実行中なら `RUNNING` です。
`ChainTask` で自分自身を指定すると、現在の要求を終了して新しく起動します。
起動上限に達していても、現在の一件を置き換える自己連鎖は受け付けます。

## 結果とエラー

`Result` は `state`、`status`、`discard`、`value` を持ちます。
失敗時には状態を保ち、`discard = false` です。
`TerminateTask` / `ChainTask` の成功時は、C の実行基盤が `discard` に従い、呼び出し元の続きへ戻りません。

| Lean の状態 | テスト入出力の数値 | 意味 |
|---|---|---|
| `ok` | `0` | 成功 |
| `id` | `1` | 設定にないタスク ID |
| `limit` | `2` | 未完了の起動要求数が上限に到達 |
| `callevel` | `3` | 対応しない呼び出し条件 |
| `resource` | `4` | 終了・連鎖・Schedule 時に資源保持の印がある |
| `badInput` | `5` | 不明な操作などのプロジェクト固有の不正入力 |

複数の条件違反が重なる場合の判定順は関数本体で確認します。
対応する一部の条件をモデル化しており、標準の全エラー順序を実装したものではありません。

## 呼び出し条件と観測用操作

`ctx = 0` はタスク、`ctx = 1` は Category 2 ISR を表します。
`4` を加えると資源保持中の印です。`2` / `3` の呼び出し種別や `8` 以上は対応しません。
タスクの呼び出しは ISR 深さが `0`、ISR の呼び出しは深さが正である必要があります。
起動は実行中タスクまたは ISR から、終了・連鎖・Schedule は実行中タスクから呼びます。
二つの問い合わせは対応するタスク・ISR 条件で使えます。

| 観測用操作 | 役割 | 制限 |
|---|---|---|
| `stepPc s ctx` | 実行中フレームのモデル上の進行値を増やす | OSEK サービスではない。一般モデルだけ |
| `enterISR s` | モデル上の ISR 深さを増やす | 物理割り込みを発生させない |
| `exitISR cfg s` | 深さを減らし、最外側の終了で再選択する | 入れ子なしでの終了は `callevel` |

資源保持の印は資源管理そのものではなく、ISR 深さは割り込み禁止状態を表しません。

## テストと C の境界

`TaskMain.lean` の入力は、設定と操作列を 1 行にまとめたテスト用形式です。
操作番号は `0` 起動、`1` 終了、`2` 連鎖、`3` Schedule、`4` ID 問い合わせ、
`5` 状態問い合わせ、`6` 進行、`7` ISR 入場、`8` ISR 退場です。
行全体の構文が不正なら `INVALID` を出します。
完全な形式は [Protocol.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Protocol.lean) を参照してください。

ターゲット向け生成 C の入口は次です。

```c
uint64_t lean_osek_step(uint64_t config, uint64_t state,
                       uint64_t operation, uint64_t id, uint64_t context);
```

最大 4 タスク、優先度 `0〜15`、起動上限の合計 `8` 以下、モデル上の ISR 深さ `15` 以下です。
観測用の操作 `6` は対応しません。
この形式と、入門用の `lean_cp_step` は別の ABI です。
ビット配置と不正値の取り扱いは [QEMU 資料](https://github.com/4ge32/lean-cp-os/blob/main/docs/QEMU.md)、
関数本体は [Task/Model.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Model.lean) を確認してください。
