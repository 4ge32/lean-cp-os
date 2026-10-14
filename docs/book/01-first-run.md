# 1. まず 3 タスクを動かす

この章では、OS や Lean の知識を前提にせず、起動した仕事がどの順に選ばれるかを確かめます。
使うのは `low`、`mid`、`high` という 3 タスクだけの入門用モデル **M0** です。
タスクとは OS が実行を管理する仕事、スケジューラとは次に実行するタスクを選ぶ仕組みです。

ここで動かすのは、状態を入力すると次の状態を返す Lean のプログラムです。
実際の CPU のスタックを切り替える実験は [第 7 章](07-target.md)で行います。
まずは「選ぶ規則」を目で追えるようになりましょう。

## 手元で実行する準備

この手順は Linux x86_64 の端末を使います。Git、curl、tar と zstd を用意してください。
後の C・検証の章では GCC と Python 3 も使います。
すでにリポジトリを取得している場合は、`lakefile.toml` があるディレクトリへ移動します。
初めて取得する場合は次のとおりです。

```sh
git clone https://github.com/4ge32/lean-cp-os.git
cd lean-cp-os
```

このプロジェクトは Lean **4.19.0** を使います。まだ準備していない場合は次を実行します。
スクリプトは公式配布ファイルを取得し、記録済みのハッシュと一致するか確認して展開します。

```sh
bash scripts/bootstrap_lean.sh /tmp/lean-cp-toolchain
export PATH=/tmp/lean-cp-toolchain/lean-4.19.0-linux/bin:$PATH
lean --version
```

出力に `version 4.19.0` が含まれることを確認します。
すでに別の場所にこの版を入れている場合は、その `bin` を `PATH` に指定してください。
`/tmp` のファイルは環境によって削除されるため、継続利用では保存先を変更できます。

次に、プロジェクトの Lean ファイルをビルドします。
Lake は Lean のビルドツールで、`lake env` はプロジェクトのライブラリを見つけられる環境で後続のコマンドを実行します。

```sh
lake build
lake env lean examples/book/first-run.lean
```

`lake build` が成功し、続けて次の 5 行が表示されれば、この章の実行は成功です。

```text
some (LeanCpOs.Task.low)
some (LeanCpOs.Task.high)
LeanCpOs.TaskState.ready
some (LeanCpOs.Task.low)
LeanCpOs.Control.returned (LeanCpOs.Status.limit)
```

`unknown module prefix` や `object file ... does not exist` が出た場合は、
リポジトリのルートで `lake build` が成功しているか確認します。
`lean: command not found` の場合は、その端末で `PATH` の設定をもう一度行ってください。

## 何が起きたのか

優先度は `low < mid < high` です。M0 は実行対象のうち、最も優先度が高いタスクを選びます。
**起動**は実行対象に加える操作、**終了**は現在のタスクを実行対象から外す操作です。

| 手順 | low | high | 選ばれるタスク |
|---|---|---|---|
| 最初 | Suspended（休止） | Suspended（休止） | なし |
| low を起動 | Running（実行中） | Suspended（休止） | low |
| high を起動 | Ready（実行可能） | Running（実行中） | high |
| high を終了 | Running（実行中） | Suspended（休止） | low |

`mid` はこの例では一度も起動しないため、ずっと Suspended です。
low は high の起動で消えません。実行可能なまま残り、high の終了後に再び選ばれます。
この Ready を、イベントの成立を待つ拡張タスクの Waiting と混同しないでください。
状態の違いは [第 2 章](02-scheduling.md)で詳しく扱います。

`some (...)` は「値がある」、`none` は「値がない」を表します。
最後の `limit` は、すでに起動している high をもう一度起動したためのエラーです。
M0 で同じタスクに受け付けられる未完了の起動要求は一つだけです。

## 実行したコードを読む

次のコードは、実行したファイルそのものを Book に取り込んでいます。
`s1`、`s2`、`s3` はそれぞれ操作後の状態です。状態を順に次の操作へ渡しています。

```lean
{{#include ../../examples/book/first-run.lean}}
```

`activate` と `terminate` は、状態と操作の応答をまとめた結果を返します。
`.state` でその中の状態を、`.current` で現在選ばれたタスクを取り出します。
`.control` は呼び出しの応答や制御移動の指示です。
`#eval` は計算結果を表示し、`#guard` は期待した結果との一致を検査します。
`#guard` は成功時には何も表示しません。違いがあれば Lean の実行がエラーになります。

`s3` は「high の終了後」の状態ですが、最後の二重起動の観察には **s2** を使っています。
これは high がまだ実行中の状態に対する別の実験です。
関数へ状態を渡すので、以前の状態から別の操作を試すこともできます。

## 演習：予想してから変える

1. high の代わりに mid を起動した場合、5 行の出力はどう変わるでしょうか。
2. high の二重起動が失敗したとき、low や現在のタスクは変わるでしょうか。

試すときは教材をコピーし、コピー内の `.high` をすべて `.mid` に変更します。
表示する操作と、対応する `#guard` の期待値の両方を変更してください。

```sh
cp examples/book/first-run.lean /tmp/lean-cp-first-run.lean
# エディターで /tmp/lean-cp-first-run.lean を変更する
lake env lean /tmp/lean-cp-first-run.lean
```

<details>
<summary>答え</summary>

1. 2 行目が `some (LeanCpOs.Task.mid)` に変わります。残りは同じです。
   low より mid の優先度が高く、mid が終了すると low に戻ります。mid の二重起動も `limit` です。
2. 変わりません。`(activate s2 (some .high)).state = s2` がそれを検査しています。
   エラーという表示だけでなく、状態が保たれたことも別に確かめています。

</details>

実装の入口は [Model.lean の `select`・`activate`・`terminate`](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Model.lean)です。
準備スクリプトは [bootstrap_lean.sh](https://github.com/4ge32/lean-cp-os/blob/main/scripts/bootstrap_lean.sh)、
教材は [first-run.lean](https://github.com/4ge32/lean-cp-os/blob/main/examples/book/first-run.lean) にあります。
次の [第 2 章](02-scheduling.md)では、この小さなモデルが AUTOSAR CP のどの部分に関わるかを整理します。
