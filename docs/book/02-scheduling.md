# 2. AUTOSAR CP の中で OS を位置づける

第 1 章では、low を起動し、high に実行を譲り、low に戻る様子を観察しました。
この章では、AUTOSAR CP 全体の中でその選択が何を担当するかを理解します。
その後に 3 タスクへ増やし、実行前に選択結果を予想してみます。

## 全体から、今回扱う部分へ

**AUTOSAR Classic Platform（CP）** は、車載 ECU のソフトウェア構造やインターフェースを定める標準です。
ECU は、車両の機能を制御するコンピューターです。CP は OS だけを指す名称ではありません。
大まかな役割を次のように分けると、OS の位置が見えます。

| 部分 | 主な役割 | 今回のプロジェクトとの関係 |
|---|---|---|
| SWC（Software Component） | アプリケーションの機能をコンポーネントとして表す | SWC の構成やアプリケーションは実装対象外 |
| RTE（Runtime Environment） | SWC 間や SWC と基本ソフトウェアとの接続を担う | RTE 自体やその生成器は実装対象外 |
| BSW（Basic Software） | OS、通信、診断、メモリー管理、ハードウェア抽象化などを提供する | このうち OS の基本タスク制御が題材 |
| MCAL（Microcontroller Abstraction Layer） | BSW の一部としてマイコン依存の周辺機能を抽象化する | QEMU 用移植層を AUTOSAR MCAL と同一視しない |
| OS | BSW のサービス層でタスクなどの実行を管理する | 起動・選択・終了を Lean でモデル化する |

これは役割の見取り図です。すべての処理が表の上から下へ順番に呼ばれるわけではありません。
SWC 内の実行単位である **Runnable** と OS の **Task** も同じ概念ではありません。
Runnable をどのタスクで実行するかなどは、システムの設定と統合に関わります。
この Book は、その接続全体を作る前に、タスクを選ぶ規則を小さく取り出して学びます。

## OSEK と AUTOSAR の基準を分ける

AUTOSAR CP OS は OSEK OS を基礎とする機能を持ち、さらに機能を拡張しています。
ただし「関係がある」ことと「同じ仕様に適合している」ことは別です。

| 対象 | このリポジトリでの位置づけ |
|---|---|
| OSEK OS **2.2.3** | 現在の単一コア・基本タスク制御の振る舞いの基準 |
| M0 | 固定 3 タスク、異なる固定優先度、起動要求は各 1 件という入門用の小さなモデル |
| 設定可能な基本タスク制御 | タスク数・優先度・起動上限、同順位の順序などを扱う現在の実装 |
| AUTOSAR CP OS **R25-11** | 将来の互換性確認先。対応関係の照合は未完了 |

R25-11 はこのプロジェクトが記録している将来の照合先であり、現在の実装済み機能の保証ではありません。
OSEK 全体、AUTOSAR CP 全体、または安全規格への適合を主張しているわけでもありません。
採用版と根拠資料は [出典の記録](https://github.com/4ge32/lean-cp-os/blob/main/docs/SOURCES.md) と
[sources.json](https://github.com/4ge32/lean-cp-os/blob/main/trace/sources.json) で管理します。

## Basic Task の三つの状態

基本タスクは起動され、CPU の実行対象となり、処理を終えて終了します。
M0 では次の三つの状態を使います。

| 状態 | 意味 | low → high → high 終了の例 |
|---|---|---|
| Suspended（休止） | 未完了の起動要求がない | まだ起動していない mid |
| Ready（実行可能） | 実行対象だが、現在は選ばれていない | high が選ばれている間の low |
| Running（実行中） | 現在選ばれている | high の終了後の low |

**Ready はイベント待ちの Waiting ではありません。** Ready は CPU が割り当てられれば実行できます。
Waiting は拡張タスクがイベントの成立を待っている状態で、現在の基本タスクモデルにはありません。
「待機」という日本語だけでは曖昧なので、この Book では Ready を「実行可能」と呼びます。

高優先度のタスクに実行を譲ることを **プリエンプション** と呼びます。
M0 は起動や終了というモデル上の操作の時点で再選択します。
機械命令の途中に割り込みが入る動作や、スタックの保存を M0 が実行しているわけではありません。

## 優先度を予想してから実行する

次の順に操作します。各行を読むたびに、選ばれるタスクを予想してください。

| 操作 | low | mid | high | 選ばれるタスク |
|---|---|---|---|---|
| low を起動 | Running | Suspended | Suspended | low |
| mid を起動 | Ready | Running | Suspended | mid |
| high を起動 | Ready | Ready | Running | high |
| high を終了 | Ready | Running | Suspended | mid |

第 1 章でビルドしたリポジトリのルートで、次を端末へ入力します。
`cat` の行から `LEAN` の行までは、実験用の Lean ファイルを作っています。

```sh
cat > /tmp/lean-cp-scheduling.lean <<'LEAN'
import LeanCpOs.Model
open LeanCpOs

def a := (activate initial (some .low)).state
def b := (activate a (some .mid)).state
def c := (activate b (some .high)).state
def d := (terminate c).state

#eval b.current
#eval c.current
#eval d.current
#guard taskState c .low = .ready
#guard taskState c .mid = .ready
#guard d.active.get .low = true
LEAN
lake env lean /tmp/lean-cp-scheduling.lean
```

期待する出力は次の 3 行です。

```text
some (LeanCpOs.Task.mid)
some (LeanCpOs.Task.high)
some (LeanCpOs.Task.mid)
```

low が選ばれない間も、`active.get .low` は `true` のままです。
ここで `active` は Ready だけでなく Running も含む「未完了の起動があるタスク」を表します。
M0 はその集合から最優先のものを選ぶため、別の Ready キューは持ちません。

## 演習：次に low は動けるか

1. `d` から現在のタスクをもう一つ終了すると、次に誰が選ばれますか。
2. high を起動して終了する操作を繰り返せば、low がいつか一定時間内に進むといえますか。
3. 同じ優先度のタスクを並べる規則は、この M0 の例から分かりますか。

<details>
<summary>答え</summary>

1. low です。実験用ファイルの末尾に `#eval (terminate d).state.current` を追加すると確認できます。
2. いえません。M0 は選択の規則を表し、時間や公平性を保証しません。
   高優先度の仕事が続く状況での飢餓防止や実行時間の上限は、別の検討が必要です。
3. 分かりません。M0 の優先度はすべて異なります。同順位の依頼順や複数起動は
   [第 6 章の設定可能なモデル](06-task-control.md)で扱います。

</details>

今読んだ規則は [Model.lean の `priority`・`select`・`taskState`](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Model.lean) にあります。
設定可能なモデルでは非プリエンプティブ設定もあるため、M0 の「常に最高優先度」をそのまま一般化できません。
その違いは [設計資料](https://github.com/4ge32/lean-cp-os/blob/main/docs/DESIGN.md) に記録されています。
次の [第 3 章](03-lean-model.md)では、この規則を表す Lean のコードを読めるようにします。
