# 4. リポジトリの地図を作る

ここまで使った `activate` は、リポジトリのどこで定義され、何と接続しているのでしょうか。
この章では M0 の一つの操作を起点に、実装、証明、テスト、根拠の場所をたどります。
目的はすべてのファイルを読むことではなく、疑問が生じたときの入口を選べるようになることです。

## 最初に二つのモデルを区別する

同じ名前の関数でも、扱うモデルが異なります。
M0 は入門用に小さく保たれ、設定可能な基本タスク制御はその隣に置かれています。

| 観点 | M0 | 設定可能な基本タスク制御 |
|---|---|---|
| 実装 | `LeanCpOs/Model.lean` | `LeanCpOs/Task/Model.lean` |
| 名前空間 | `LeanCpOs` | `LeanCpOs.TaskControl` |
| タスク | low / mid / high の 3 個 | 設定リストの要素として指定 |
| 起動の表現 | 各タスクの Bool | 起動要求ごとの Frame |
| 選択の主要関数 | `select` | `choose`、`dispatch`、`mayPreempt` |
| Valid の主な意味 | current と select の一致 | タスク ID と起動数の整合性 |

名前空間は、定義名の前に付く区切りです。
`LeanCpOs.activate` と `LeanCpOs.TaskControl.activate` は別の関数です。
M0 のファイル名だけを覚えて後者を修正すると、期待した対象に変更が届きません。
また、同じ `Valid` という名前でも定義が違うので、証明の前提を読むときは名前空間も確認します。

## 実行して定義を探す

リポジトリのルートで、Git が管理する実装ファイルから定義を探します。
`git grep` は追跡対象のファイルを検索するため、生成物を結果に混ぜずに探せます。

```sh
git grep -n -E '^namespace|^def (activate|terminate)' -- \
  LeanCpOs/Model.lean LeanCpOs/Task/Model.lean
```

期待する結果は、それぞれのファイルで一つの名前空間と、activate・terminate の定義が見つかることです。
行番号は版によって変わりますが、次の対応を確認できます。

```text
LeanCpOs/Model.lean              → namespace LeanCpOs
                                 activate (s : State) (target : Option Task)
LeanCpOs/Task/Model.lean         → namespace LeanCpOs.TaskControl
                                 activate (cfg : Config) (s : State) (target ctx : Nat)
```

後者には設定 `cfg` と呼び出し条件 `ctx` があります。
引数の違いは、後者がより広い動作条件を扱う手掛かりです。詳細は [第 6 章](06-task-control.md)で確認します。

## ファイルを役割で読む

| 場所 | 役割と読むときの問い |
|---|---|
| [Model.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Model.lean) | M0 の規則。起動すると何が変わるか |
| [Proofs.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Proofs.lean) | M0 の定理。どの前提から何を示したか |
| [Bridge.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Bridge.lean)・[Main.lean](https://github.com/4ge32/lean-cp-os/blob/main/Main.lean) | M0 を数値入出力へつなぐ。値をどう符号化するか |
| [Task/Model.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Model.lean)・[Task/Proofs.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Proofs.lean) | 設定可能な基本タスクの規則と証明 |
| [Task/Semantics.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Semantics.lean) | 継続・破棄を含む実行意味。中断と終了はどう違うか |
| [Task/Protocol.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Protocol.lean)・[TaskMain.lean](https://github.com/4ge32/lean-cp-os/blob/main/TaskMain.lean) | 設定と操作列のテスト入出力 |
| [Task/Scalar.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Scalar.lean) | 容量を制限し、固定幅の値で表すターゲット用実装 |
| [c/](https://github.com/4ge32/lean-cp-os/tree/main/c) | ホスト C との接続、戻り方や生成 C の比較 |
| [target/aarch64/](https://github.com/4ge32/lean-cp-os/tree/main/target/aarch64) | QEMU での起動、出力、スタック・レジスター切り替え |
| [tests/](https://github.com/4ge32/lean-cp-os/tree/main/tests) | 別に書いた Python の期待動作との比較や検証基盤のテスト |
| [scripts/](https://github.com/4ge32/lean-cp-os/tree/main/scripts) | ツール準備、検査、結果の収集と公開 |
| [trace/](https://github.com/4ge32/lean-cp-os/tree/main/trace) | 要求、出典、定理、テストを結び付ける記録 |

`Task/Scalar.lean` は一般モデルをそのまま名前だけ変えたものではありません。
最大 4 タスクなどの容量制限を持つ別の表現で、対応関係は比較テストで確認しています。
一般モデルから C・アセンブリーまでの対応が、すべて形式証明済みという意味ではありません。

## 一つの操作を縦に追う

例として「起動上限に達したときは、状態を変えずにエラーにする」を追ってみます。
まず第 1 章の `#guard` が、どの性質を検査していたかを思い出してください。

1. M0 の `activate` で、すでに active なら `⟨s, .returned .limit⟩` を返す分岐を読む。
2. M0 の `Proofs.lean` で `activation_limit` と `activation_error_frame` の主張を読む。
3. `Bridge.lean` の `step`・`packResult` で、その結果が外部向けの数値になる場所を読む。
4. `tests/test_differential.py` で、Lean と生成 C を独立した計算結果と比較する仕組みを見る。
5. `trace/requirements.json` で、関連する実装・定理・テスト・仕様の根拠をたどる。

次の検索で、まず 1 と 2 の入口を確認できます。

```sh
git grep -n -E 'def activate|theorem activation_(limit|error_frame)' -- \
  LeanCpOs/Model.lean LeanCpOs/Proofs.lean
lake env lean examples/book/first-run.lean
```

検索では activate の定義と二つの定理が見つかります。
実行結果の最後は `LeanCpOs.Control.returned (LeanCpOs.Status.limit)` で、検査はすべて成功するはずです。
同じ現象を、実行例・規則・定理という別々の入口から確認できました。

## 編集するものと生成されるもの

`LeanCpOs/`、`c/`、`target/` などは、規則や接続を変更する元のソースです。
一方、`.lake/` は Lean のビルド結果、`build/` は検証で生成した C や実行ファイル、
`evidence/` は検証結果を置く場所です。これらは通常 Git の管理対象にしません。

例えば生成した `build/TaskScalar.c` を直接直しても、次の生成で置き換わります。
選択規則の変更は元の Lean ファイルへ、CPU の切り替えの変更は対応する移植層へ戻します。
Book の説明は `docs/book/`、実行できる教材は `examples/book/` にあります。
説明中の取り込みコードは教材ファイルを参照するため、実行例と本文のコードを別々に更新する必要がありません。

## 演習：どのファイルから読むか

1. 固定 3 タスクで二重起動のエラーを理解したいとき、最初に読むファイルはどれですか。
2. 同じ優先度の依頼順を変更する影響を調べたいとき、M0 の `select` だけ読めば十分ですか。
3. QEMU で中断したタスクのレジスターが戻らないとき、Lean の選択結果以外にどこを調べますか。
4. コードを変更した結果が、どの要求の検証に当たるかを調べる入口はどこですか。

<details>
<summary>答え</summary>

1. `LeanCpOs/Model.lean` の `activate` です。次に `Proofs.lean` と教材の `#guard` を照らし合わせます。
2. 不十分です。`LeanCpOs/Task/Model.lean` の `choose`、`dispatch`、`mayPreempt` などを読みます。
   対応する証明・比較テスト・容量制限付き実装も影響調査の対象です。
3. `target/aarch64/context.S` の保存・復元と `runtime.c` の制御移動を調べ、`tests.c` のシナリオで確認します。
4. `trace/requirements.json` です。テスト ID は `trace/tests.json`、根拠資料は `trace/sources.json` と対応させます。

</details>

変更を実際に進める手順は [第 8 章](08-change.md)、根拠や文書の維持は [第 10 章](10-maintenance.md)で扱います。
次の [第 5 章](05-proofs.md)では、ここで見つけた定理を「何を証明しているか」から読み解きます。
