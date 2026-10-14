# 動作のルールを証明する

前章までで追った「low を起動し、high に中断され、low に戻る」という動作を使い、
実行結果の確認から、任意の操作列に対する証明へ進みます。
この章の目標は、既存の定理の前提を読み、組み合わせて新しい性質を示すことです。

## まず動かす

リポジトリのルートで、ビルド済みのモデルを読み込む例を実行します。
初めて実行する場合は、第1章の環境構築と `lake build` を済ませてください。

```sh
lake env lean examples/book/proofs.lean
```

期待する表示は次の1行です。
`#guard` と定理の検査は、成功時には表示を増やしません。
表示だけでなく、コマンドが終了コード 0 で終わることを確認します。

```text
some (LeanCpOs.Task.low)
```

実行したファイルの全体です。Book にも同じファイルを取り込んでいます。

```lean
{{#include ../../examples/book/proofs.lean}}
```

`#guard observed.current = some .low` は、今回の具体的な操作列を計算して確認します。
`one_runner_after` は `cs` を具体化していません。
空の列でも、100回の起動と終了でも、どの `List Command` に対しても使える定理です。

## 「正しい状態」の意味を読む

固定3タスクモデルの `Valid` は、次の等式を意味します。

```lean
def Valid (s : State) : Prop := s.current = select s.active
```

`select` は active なタスクのうち最大優先度のタスクを選びます。
したがって `Valid s` は、「状態に記録した current と、active から計算した実行対象が一致する」です。
active が空なら、両者とも `none` です。

`State` という型だけでは、この等式までは要求しません。
例の `inconsistent` は low だけが active なのに、current を high にしています。
この値も Lean の型検査は通りますが、`#guard ¬ Valid inconsistent` が成立します。
型として表せる状態と、モデルが正しいと認める状態を区別してください。

ここで `taskState inconsistent .high` は `suspended` です。
`taskState` はまず active を調べるからです。
「current なら running」と読み替える定理 `running_current` が `Valid s` を要求する理由が見えます。

## 三つの定理をつなぐ

`one_runner_after` の証明は次の順番です。

1. `reachable_valid cs` から、初期状態に `cs` を適用した結果が `Valid` だと得る。
2. `ht` と `hu` は、その状態でそれぞれ t と u が running だという仮定。
3. `at_most_one_running` に状態、二つのタスク、三つの根拠を渡し、`t = u` を得る。

`have hv : ... := ...` は、後で使う根拠に名前を付けています。
`exact` は、今示したい命題に合う証明をそのまま渡します。
証明の中でタスクを実行したり、テスト件数を増やしたりしているわけではありません。

では、元の `at_most_one_running` はどう示しているのでしょうか。
[`LeanCpOs/Proofs.lean`](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Proofs.lean)
では、`running_current` により次の二つの等式へ変換しています。

```text
s.current = some t
s.current = some u
```

左辺が同じなので `some t = some u`、さらに `t = u` です。
`Option.some.inj` は最後の段階、つまり同じ `some` の中身が等しいことを取り出します。
最大1タスクが running という性質は、current の単一性と状態の整合性を使って示せます。

## 操作列の長さを決めずに示す

`reachable_valid` は `execution_preserves` を初期状態に適用しています。
中心になるのはリストに対する帰納法です。

| 操作列 | 証明に使うこと |
|---|---|
| 空の列 `[]` | 何も変えないので、元の `Valid s` がそのまま使える |
| 先頭 `c` と残り `cs` | `transition_preserves` で1操作後の Valid を得て、残りには帰納法の仮定を使う |

1操作の証明は `activate_preserves` と `terminate_preserves` に分かれます。
起動が ID エラーや上限エラーになれば状態を変えず、成功した場合は `schedule` で整合した状態を作ります。
成功だけでなく失敗する経路も含めて示すからこそ、任意の操作列へつなげられます。

固定3タスクの `select_highest` などでは、Bool の組合せと3種類のタスクを場合分けし、
各場合を `decide` で証明しています。
有限な状態の列挙と、任意長の操作列に対する帰納法は、異なる場所で役立つ手法です。

## 少し変えて確かめる

演習用にファイルをコピーし、末尾の解答を見る前に試してください。

```sh
mkdir -p work
cp examples/book/proofs.lean work/proofs-exercise.lean
lake env lean work/proofs-exercise.lean
```

**演習1:** `commands` の最後に high の起動を追加したら、current は何になるでしょうか。
予想を `#guard` に書き、変更後も Valid だという証明を付けてください。

<details>
<summary>答え</summary>

high になります。low が動いているところへ、より優先度の高い high を起動するためです。
ファイル末尾の `extended` と `example` が対応する解答です。
`reachable_valid` は操作列の具体的な内容に制限を置かないので、そのまま再利用できます。

</details>

**演習2:** 到達可能な状態に、さらに任意の `target : Option Task` を起動しても Valid だと示してください。
`none` を渡す場合も対象です。

<details>
<summary>答え</summary>

`valid_after_another_activation` のように、`reachable_valid cs` の結果を
`activate_preserves` の前提へ渡します。
`none` は ID エラーですが状態を維持するので、Valid は失われません。
「成功する」と「不変条件を保つ」は別の性質です。

</details>

## 証明が保証する範囲を確かめる

次章の一般タスクモデルにも `Valid` がありますが、定義は同じではありません。
[`Task/Model.lean`](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Model.lean)
では、各フレームの ID が設定内にあり、タスクごとの起動数が設定上限以下であることを表します。
非プリエンプティブな実行も扱うので、「常に最大優先度が current」という条件にはしません。
同名の定理を見つけたときは、名前空間と定義までたどる習慣を付けましょう。

証明が依存する公理は次のコマンドで確認できます。

```sh
lake env lean Audit.lean
```

例えば `LeanCpOs.reachable_valid` は `[propext]` に依存します。
これは Lean 標準の命題の外延性です。
[`scripts/audit.py`](https://github.com/4ge32/lean-cp-os/blob/main/scripts/audit.py)
はこれだけを許可し、未証明の穴や追加の公理などを拒否します。
このコマンド単体は依存の表示であり、監査ゲート全体の実行は第9章で扱います。

Lean が検査したのは、書かれたモデルと命題の間の論理的な関係です。
仕様の読み取り、生成 C、C コンパイラ、スタック保存、CPU 動作までが、この定理だけで正しくなるわけではありません。
次章では設定可能なモデルへ進み、第7章では実行の境界を別のテストで確認します。

## 対応するソース

- [固定3タスクの状態と操作](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Model.lean): `Valid`、`taskState`、`activate`、`terminate`。
- [固定3タスクの証明](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Proofs.lean): `running_current`、`at_most_one_running`、`execution_preserves`。
- [一般モデルの不変条件の証明](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Proofs.lean): `choose_perm`、`step_valid`、`reachable_valid`。
- [一般モデルのサービス契約](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Semantics.lean): 失敗時の状態保存、継続の保存・破棄。
