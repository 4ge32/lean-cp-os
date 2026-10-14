# 3. Lean のコードで状態を表す

第 2 章では、タスクの状態を表で追いました。この章では、その表を表現する Lean の型と関数を読みます。
まず必要なのは、型、値、関数、場合分け、そして「値が満たしてほしい条件」の区別です。
証明の書き方を一度に覚える必要はありません。実行した値と定義を対応させながら進めます。

## 型は、扱う値の種類を決める

M0 の `Task` は、`low`、`mid`、`high` のいずれか一つを表す型です。
`inductive` はここでは、取り得る形を列挙するために使っています。

```lean
inductive Task where
  | low | mid | high
```

`Task.low` が値の完全な書き方です。期待される型が分かる場所では `.low` と短く書けます。
実際の定義には比較や表示に必要な `deriving DecidableEq, Repr` もあります。
ここでは、`DecidableEq` が等しいかの判定、`Repr` が `#eval` の表示を可能にすると押さえます。

| 記法 | 意味 | 例 |
|---|---|---|
| `x : T` | x の型は T | `s : State` |
| `:=` | 定義の中身を与える | `def untouched := initial` |
| `A → B` | A を受け取って B を返す関数の型 | `Task → Nat` |
| `f x` | 関数 f を値 x に適用する | `priority .high` |
| `s.current` | 構造体 s の current フィールドを読む | `activated.current` |
| `a = b` | a と b が等しいという命題 | `priority .high = 3` |

`Nat` は 0 以上の整数、`Bool` は `true` または `false`、`String` は文字列の型です。
Lean の通常の関数適用は `priority(.high)` ではなく、空白で区切った `priority .high` と書きます。

## 値がない場合を Option で表す

現在のタスクは `Option Task` という型です。
`some .low` はタスクがある状態、`none` は選ばれたタスクがない状態を表します。
「なし」を特定のタスク番号で代用せず、型の中で区別できます。

`activate` の対象も M0 では `Option Task` です。対象が `none` の場合は ID のエラーになります。
一方、`initial.current = none` は「何も実行していない」という正常な初期状態です。
同じ `none` でも、どのフィールドや引数にあるかを見て意味を判断します。

## 状態をまとめ、次の状態を返す

`structure` は名前の付いたフィールドをまとめた型を定義します。
M0 の `State` は、起動中のタスク集合 `active` と、選択中のタスク `current` を持ちます。

```lean
structure State where
  active : Active
  current : Option Task
```

`activate initial (some .low)` は `initial` 自体を書き換えません。
新しい状態を含む `Result` を返すので、`.state` で取り出し、次の操作に渡します。
このように外部の状態を書き換えずに計算する関数を、純粋な関数と呼びます。

実コードには `{ a with low := b }` という更新の書き方も登場します。
これは a の low フィールドだけを b にした **新しい値**を作る記法です。
元の a の値は残るため、変更前と変更後を並べて比較できます。

## 実行して、定義と表示を結ぶ

次の教材は M0 の型をそのまま使います。`label` の `|` から始まる行は、入力ごとの場合分けです。
三つの Task の形すべてに、返す文字列を定めています。

```lean
{{#include ../../examples/book/lean-basics.lean}}
```

リポジトリのルートで実行します。第 1 章の `lake build` が済んでいれば、再準備は不要です。

```sh
lake env lean examples/book/lean-basics.lean
```

期待する出力は次のとおりです。

```text
"high"
3
some (LeanCpOs.Task.low)
none
true
false
```

3 行目で low が選ばれても、4 行目の `untouched.current` は `none` のままです。
この違いで、`activate` が元の状態を書き換えていないことを観察できます。

## 型が合っていることと、規則を満たすこと

`broken` は State 型としては作れますが、誰も起動していないのに low を選んでいます。
そのような食い違いを排除する条件が、M0 の **`Valid`** です。

```lean
def Valid (s : State) : Prop := s.current = select s.active
```

`Prop` は命題の型です。この定義は「現在のタスクが、起動集合から選んだ結果と一致する」という主張を表します。
`Bool` が計算用の真偽値であるのに対し、命題には証明を与えられます。
この `Valid` は判定可能なので、`decide (Valid activated)` で真偽値にして表示できます。
5 行目の `true` と 6 行目の `false` は、その判定結果です。

教材の `example : priority .high = 3 := rfl` は、小さな証明です。
`rfl` は両辺を定義に従って展開したときに一致することを使います。
さらに `example (a : Active) : Valid (schedule a) := rfl` は、特定の a ではなく任意の a を対象にしています。
「いくつか動かして一致した」と「任意の入力について示した」の違いは [第 5 章](05-proofs.md)で掘り下げます。

## 演習：意味を変えずに書いてみる

教材を `/tmp/lean-cp-lean-basics.lean` にコピーして試してください。

```sh
cp examples/book/lean-basics.lean /tmp/lean-cp-lean-basics.lean
# 次の演習をエディターで試した後に実行する
lake env lean /tmp/lean-cp-lean-basics.lean
```

1. `broken` の `current := some .low` を `current := none` に変更したら、最後の表示はどうなりますか。
2. `label` の `.mid` の分岐を削除したら、Lean は何を指摘しますか。
3. `Valid` を満たすなら、low がいつか必ず実行されることまで分かりますか。

<details>
<summary>答え</summary>

1. `true` になります。その際は `#guard ¬ Valid broken` も `#guard Valid broken` に変更します。
   表示だけ変えて検査を直さないと、期待が食い違って実行は失敗します。
2. `.mid` に対応する場合が足りないと指摘します。関数は Task の各入力に対する結果を定める必要があります。
3. 分かりません。M0 の `Valid` は一つの状態の選択結果に関する条件です。時間や公平性は含んでいません。

</details>

実際の型と関数は [Model.lean](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Model.lean)、
教材全体は [lean-basics.lean](https://github.com/4ge32/lean-cp-os/blob/main/examples/book/lean-basics.lean) にあります。
次の [第 4 章](04-repository.md)では、このモデルから証明・C・QEMU へつながるリポジトリの地図を作ります。
