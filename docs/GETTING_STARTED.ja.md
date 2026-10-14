# 3 つの仕事で学ぶ、小さな OS の模型

## まず何を作っているのか

OS の役割の一つは、実行したい仕事が複数あるときに「次はどれを動かすか」を決めることです。この仕事を **タスク**、選ぶ仕組みを **スケジューラ** と呼びます。

このプロジェクトでは、`low`、`mid`、`high` の 3 タスクだけを扱います。優先度は `low < mid < high`。実行対象になっているタスクのうち、最も優先度が高いものを選びます。最初の段階を「M0」と呼んでいます。

今はこの選択ルールを調べる模型です。実機の起動や、CPU のレジスタを保存して別の仕事に切り替える処理は、将来の段階で扱います。

## 一つの例を追う

**起動（activate）** はタスクを実行対象に加える操作、**終了（terminate）** は現在のタスクを実行対象から外す操作です。

| 操作 | low | mid | high | 選ばれるタスク |
|---|---|---|---|---|
| 最初 | 休止 | 休止 | 休止 | なし |
| low を起動 | 実行中 | 休止 | 休止 | low |
| high を起動 | 待機 | 休止 | 実行中 | high |
| 現在の high を終了 | 実行中 | 休止 | 休止 | low |
| 現在の low を終了 | 休止 | 休止 | 休止 | なし |

状態の名前は 3 つです。

- **休止（Suspended）**：実行対象に入っていない。
- **待機（Ready）**：実行対象だが、より優先度の高いタスクが選ばれている。
- **実行中（Running）**：現在選ばれている。

high を起動しても low は消えません。待機になり、high の終了後に再び選ばれます。ここでいう「実行中」は模型の状態です。実際の CPU の切り替えまで証明した、という意味ではありません。

同じタスクを終了前にもう一度起動すると、`limit` エラーになり、状態は変わりません。何も実行中でないときの終了もエラーです。

**考えてみよう：** low が実行中のときに mid を起動すると、何が選ばれるでしょうか。その後 high を起動し、high を終了するとどうなるでしょうか。

答えは、順に mid、high、mid です。low はこの間、実行対象に残っています。

## Lean で例を動かす

README の手順で Lean 4.19.0 を準備した後、リポジトリのディレクトリで次を実行できます。既存のファイルを書き換える必要はありません。

```sh
lake build
example=$(mktemp /tmp/lean-cp-example-XXXXXX.lean)
cat > "$example" <<'LEAN'
import LeanCpOs.Model
open LeanCpOs

def s1 := (activate initial (some .low)).state
def s2 := (activate s1 (some .high)).state
def s3 := (terminate s2).state

#eval s1.current
#eval s2.current
#eval taskState s2 .low
#eval s3.current
#eval (activate s2 (some .high)).control
LEAN
lake env lean "$example"
rm "$example"
```

出力は順に `some (LeanCpOs.Task.low)`、`some (LeanCpOs.Task.high)`、`LeanCpOs.TaskState.ready`、`some (LeanCpOs.Task.low)`、`LeanCpOs.Control.returned (LeanCpOs.Status.limit)` です。`some` は「タスクが一つ選ばれている」、`none` は「選ばれていない」を表します。

コードの `s1`、`s2`、`s3` はそれぞれ操作後の状態です。`.state` は操作の結果から状態を取り出し、`.current` は現在選ばれているタスクを取り出します。`#eval` は値を計算して表示する Lean の命令です。

次は `.high` を `.mid` に変えて実行してみてください。表の予想と出力を比べると、ルールを自分で確かめられます。

## 証明とテストは何が違うか

例えば「起動や終了の後も、選ばれるのは実行対象のうち最も優先度が高いタスク」というルールを考えます。

**証明**では、Lean に書いた模型について、前提を満たす状態ならそのルールが守られることを示します。Lean は証明の手順を検査します。`Valid` は「現在選ばれたタスクと、スケジューラが選ぶタスクが一致する」という条件です。起動・終了がこの条件を保つ証明が `Proofs.lean` にあります。

**テスト**では、具体的な入力で動かして結果を比較します。このプロジェクトは 2,763 ケースについて、Lean の実行結果と、Lean から生成した C の実行結果を、別に書いた Python の計算結果と比べます。変換や接続で起こる間違いを見つけるためです。

模型の証明が通っても、C コンパイラや CPU の正しさまで証明したことにはなりません。テストが全部通っても、試していない全入力の正しさをそれだけで保証することはできません。両方を使って、それぞれの範囲を確認しています。

## 検証結果を読む

README の `python3 scripts/verify.py --out evidence/local` を実行したら、`evidence/local/index.html` と `report.json` を確認します。

| 表示 | 読み方 |
|---|---|
| `passed` | その検査が実行され、成功した |
| `failed` | その検査が失敗した。対応するログで原因を確認する |
| `not_run` | 未実行。成功とは扱わない |
| `overall: passed` | この実行で必要な検査がすべて成功した |
| `coverage: incomplete` | まだ扱っていない機能や証明の境界がある |
| `exact_commit: false` | 未コミットの変更を含む検証。コミットそのものの結果とは呼べない |

`overall: passed` と `coverage: incomplete` は同時に表示されます。「今用意している検査は成功した」「OS 全体を完成・検証したわけではない」という別々の情報だからです。

GitHub Actions で今の版を検証するには **Per-commit verification → Run workflow → main → scope: head** を選びます。`history` は過去の版も一つずつ調べる設定です。過去の不具合が、その後に修正されていても、過去の版の検査は失敗します。古い実行の **Re-run** は元の版と設定を使うため、新しい版を検証するには **Run workflow** を使います。この設定は対応する変更が GitHub に反映された後に利用できます。

## 次に読むもの

1. [Model.lean](../LeanCpOs/Model.lean)：上の表を実現している短いプログラム。まず `select`、`activate`、`terminate` を読む。
2. [Proofs.lean](../LeanCpOs/Proofs.lean)：`activate_preserves` と `terminate_preserves` の主張を読む。最初から証明の全構文を理解する必要はない。
3. [設計資料](DESIGN.md)：模型の前提と、今後の開発段階を知る。
4. [C 接続の資料](RUNTIME.md)：生成した C をどう実行・検査するか知る。ABI はプログラム同士で値を受け渡すための約束、FFI は別の言語の関数を呼ぶ接続の仕組み。
5. [CI の資料](CI.md)：コミットごとの検証結果をどう残すか知る。CI は変更のたびに自動で検査する仕組み。

OSEK、AUTOSAR CP OS、TOPPERS ATK2 は、このプロジェクトが参考にしている OS の仕様や実装です。最初は名称だけ押さえて、3 タスクの例から進めてください。仕様への適合を主張できる段階にはまだ達していません。
