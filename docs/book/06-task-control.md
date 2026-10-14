# タスク制御を広げる

固定3タスクの active は Bool でした。
ここからは「A の仕事が終わる前に、もう一度 A を起動したい」という要求を扱います。
一つの起動要求を一つの `Frame` として保持し、タスクの設定と待ち行列を観察しましょう。

この章では、同じ優先度の順序、複数起動、`ChainTask`、`Schedule` を試します。
名前が同じ `State` でも、使う名前空間は `LeanCpOs.TaskControl` です。

## 動かして順番を予想する

```sh
lake env lean examples/book/task-control.lean
```

次のリストが表示され、すべての `#guard` が成功します。
数値はタスク ID で、0 が A、1 が B、2 が H です。

```text
[some 0, some 2, some 0, some 1, some 0]
```

これは A → H → A の続き → B → A の新しい実行、という順序です。
同じ A でも「中断から戻った」と「次の起動要求を始めた」では意味が違います。
コードを読むときは、ID と一緒に `pc` を追ってください。

```lean
{{#include ../../examples/book/task-control.lean}}
```

## 設定とフレームを読む

`TaskConfig` の三つの値は、優先度、同時に保持できる起動要求数、プリエンプティブかどうかです。
タスク ID は `Config` のリストの添字です。

| ID / 名前 | priority | maxActivations | preemptive |
|---|---:|---:|---|
| 0 / A | 2 | 2 | true |
| 1 / B | 2 | 1 | true |
| 2 / H | 3 | 1 | true |

大きい優先度が先に動きます。
`maxActivations` には実行中の1件も含みます。
A が実行中なら、追加で待たせられる A の要求は1件です。
同じタスクの二つの起動が、同時に走るわけではありません。

`Frame` は `task` と `pc` を持ちます。
`pc` は進行の観察用カウンターで、`stepPc` によって増えます。
CPU の命令アドレスではなく、OSEK API でもありません。
新しい依頼の `pc` は 0、中断された依頼の `pc` は保存されます。

`boot` は初期状態をモデル上の ISR に入れ、ctx = 1 で起動要求を入れ、ISR を抜けています。
タスクが存在しない初期状態から ctx = 0 で起動すると、このモデルでは `callevel` エラーになるためです。
これはテストの起動手順で、`StartOS` や OIL の autostart を実装したものではありません。

## 待ち行列の変化を読む

次の表では `A:1` を「A の pc = 1 のフレーム」と書きます。
待ち行列は優先度順にソートされた配列ではなく、要求の順序を保ったリストです。
選ぶときに `choose` が最高優先度を探します。

| 操作後の名前 | current | ready | 観察すること |
|---|---|---|---|
| `a` | A:1 | 空 | A の実行が少し進んだ |
| `ab` | A:1 | B:0 | 同順位の B は A を中断しない |
| `aba` | A:1 | B:0, A:0 | 後から頼んだ A は B の後ろ |
| `h` | H:0 | A:1, B:0, A:0 | 高順位 H が中断。元の A を先頭に保持 |
| `resumed` | A:1 | B:0, A:0 | H の終了後、A の続きを再開 |
| `b` | B:0 | A:0 | A の終了後は先に依頼された B |
| `nextA` | A:0 | 空 | 次の A は最初から始まる |

新しい要求は ready の末尾に追加します。
最高優先度が同じなら、`choose` はリストの前側を選びます。
ただし中断されたフレームは先頭へ戻すため、同順位の未開始の依頼より先に再開します。
この二つを合わせて読むと、上の実行順序を説明できます。

一般モデルの証明には `choose_fifo_head`、`choose_highest`、`mayPreempt_perm` があります。
最後の定理は切り替え前後のフレームが並べ替えの関係にあることを示します。
切り替えるだけで仕事を失ったり、二重に増やしたりしないための根拠です。

## ChainTask は終了と起動を一つの遷移にする

`rejected` では A が B へ連鎖しようとしますが、B はすでに1件待っています。
B の上限は1なので結果は `limit`、状態は `resumed` と完全に同じです。
先に A を終わらせてしまうと失敗から戻れなくなるため、検査を済ませてから状態を変えます。

`restarted` では上限1の B が自分自身へ連鎖します。
これは現在の1件を新しい1件に置き換えるので、上限に達していても成功します。
新しい B は pc = 0 で末尾へ加わり、すでに待っていた同順位の A が先に動きます。
「自己連鎖だから必ずすぐに自分を再実行する」とは限りません。

結果の `discard = true` は、呼び出し元の古い継続を破棄する指定です。
成功した `TerminateTask` と `ChainTask` に対応します。
純粋な Lean 関数は `Result` を返しますが、この指定を受け取る実行基盤は古いタスクの続きへ戻してはいけません。
その接続を次章の QEMU で検査します。

## Schedule で譲る

`cooperative` の L は `preemptive = false` です。
高優先度 H を起動しても L が current のままで、H は ready に残ります。
L が `Schedule` を呼ぶと H に譲り、H が終わると L の pc = 1 の続きへ戻ります。
ここでは `discard = false` です。

同順位の A と B に対する `schedule cfg resumed 0` は状態を変えません。
`Schedule` は同順位の順番を回す操作でも、ラウンドロビンの実装でもありません。
待っているタスクが自分より高い優先度かどうかを判断します。

ISR 内では自動・明示的な切り替え判断を保留します。
`ActivateTask` で追加した依頼は、最外側の ISR を抜けるときに切り替え候補になります。
この章の `boot` で、ISR の退場後に初めて A が current になった理由も同じです。

## 少し変えて確かめる

**演習1:** `chain cfg progressedB 1 0` の対象を2、つまり H に変えてください。
current、ready、B の起動数、discard を予想して `#guard` を書きます。

<details>
<summary>答え</summary>

末尾の `toHigh` が解答です。
H が current、ready に残るのは A:0、B の起動数は0、discard は true です。
自己連鎖と違い、新たな B は追加されません。

</details>

**演習2:** `cooperative` の L を `preemptive = true` にしたら、どの時点で H が動くでしょうか。

<details>
<summary>答え</summary>

H の起動直後です。`waiting.current` は `some ⟨1, 0⟩` になります。
元の `waiting.current = some ⟨0, 1⟩` の検査は失敗するはずです。
元のファイルをコピーしてから設定を変え、期待値も対応させてください。
その後の `Schedule` はすでに H が呼ぶ操作になるので、元の説明をそのまま当てはめないようにします。

</details>

## 今回のモデルの境界

一般モデルは任意個数の静的 Basic Task、自然数の優先度、正の起動上限を扱います。
`Valid cfg s` が示すのは ID の範囲と起動数の上限です。
エラー時の状態保存や継続の破棄は、別のサービス契約として証明しています。

資源保持の印を ctx に加えると終了・連鎖・Schedule を拒否できますが、
資源の所有者管理や優先度上限プロトコルは未実装です。
Extended Task のイベント待ち、実割り込み、タイマー、マルチコアも今回のモデルには含みません。
これは OSEK の動作を参照する段階的な実装であり、AUTOSAR CP 全体への適合を示すものではありません。

## 対応するソース

- [一般モデル](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Model.lean): 設定、待ち行列、6サービスと観測用の操作。
- [不変条件と選択順序の証明](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Proofs.lean): `choose_fifo_head`、`mayPreempt_perm`、`step_valid`。
- [サービス契約](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Semantics.lean): `chain_error_unchanged`、`self_chain_restarts_at_limit`。
- [設計と仕様の対応](https://github.com/4ge32/lean-cp-os/blob/main/docs/TASK_CONTROL.md): OSEK 2.2.3 の参照節と呼び出し条件。
