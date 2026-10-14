# 模型から CPU 上の実行へ

前章で保存した `pc` は観察用の数値でした。
今度は本物の関数の途中で止まり、別のタスクを動かしてから、元の続きへ戻ります。
QEMU 上の AArch64 ターゲットで、ローカル変数・保存対象レジスタ・実行順序を確認しましょう。

## まず動かす

リポジトリのルートで実行します。
`lean` と `lake` は `lean-toolchain` の指定版を PATH に設定してください。
ホストには Python 3 と `nm`、QEMU の `qemu-system-aarch64` が必要です。
クロスコンパイルには Lean 配布物の `clang` と `ld.lld` を使います。

Debian / Ubuntu でパッケージをインストールできる場合は、次の手順です。

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends qemu-system-arm
python3 scripts/verify_qemu.py build/qemu
```

管理者権限を使わない Debian / Ubuntu amd64 環境では、ローカル展開も使えます。
以下は上のインストール手順の代替です。
展開先への書き込み権限が必要です。

```sh
sh scripts/bootstrap_qemu.sh "$PWD/.toolchain/qemu"
export QEMU_SYSTEM_AARCH64="$PWD/.toolchain/qemu/bin/qemu-system-aarch64"
python3 scripts/verify_qemu.py build/qemu
```

別の展開先を使う場合は `QEMU_SYSTEM_AARCH64` も合わせてください。
必要に応じて `LEAN_CLANG` と `LEAN_LLD` でコンパイラとリンカを指定できます。
成功すると7シナリオの TRACE / PASS と、最後に次の行が表示されます。

```text
PASS QEMU: 7 scenarios; real task stacks; generated Lean decisions
```

QEMU を用意できない場合は失敗として報告されます。
実行していないテストを成功扱いにはしません。
失敗時には `build/qemu/build.log` と `build/qemu/qemu.json` の `error` を確認します。

## A の続きへ戻る

最初のシナリオは次のトレースです。

```text
TRACE preempt-resume-registers-stack: 10 20 30 11
```

| 番号 | 実行した処理 |
|---|---|
| 10 | 低優先度 A がローカル変数を用意し、高優先度 B を起動する前に記録 |
| 20 | B が実行され、中優先度 C を起動 |
| 30 | B が終了した後、C が実行 |
| 11 | C も終了した後、A が元の呼び出しの続きへ戻る |

優先度は A = 1、B = 3、C = 2 です。
第1章の固定モデルの名前 `low / mid / high` と、ここでの A / B / C の順序は異なります。
A の C 関数は `preempt_low`、B は `preempt_high`、C は `preempt_mid` です。

[`target/aarch64/tests.c`](https://github.com/4ge32/lean-cp-os/blob/main/target/aarch64/tests.c)
の `preempt_low` は、スタックに8個の値を置いてから `os_register_probe(preempt_callback)` を呼びます。
コールバック内の `ActivateTask(1)` が B への切り替えを起こします。
戻ったときには、値が変わらず、AArch64 の x19〜x29 も保存されていることを検査します。

A を最初から呼び直しただけなら、再び10を出してしまいます。
11まで到達する順序と、保存した値の検査を組み合わせて、中断と再開を確認します。
これは終了後に次の起動要求を最初から始める動作とは区別されます。

## 実行対象の決定と、切り替えの役割

つながりは次のようになります。
点線に相当する最初の対応はテストで確認しており、形式的な精密化証明ではありません。

```text
Task/Model.lean ── 具体的な入力で比較 ── Task/Scalar.lean
                                             │ Lean が C を生成
                                             ▼
                                      lean_osek_step
                                             │ 次状態・status・discard
                                             ▼
                              target/aarch64/runtime.c
                                             │ 保存・復元を依頼
                                             ▼
                              target/aarch64/context.S
```

一般モデルのリストや自然数を、そのまま最小のターゲットへ持ち込んでいるわけではありません。
`Task/Scalar.lean` は設定と状態を `UInt64` に詰めた別の表現です。
次に動かすタスクの判断はこの Lean ソースにあり、C の runtime に同じスケジューラーを書き直してはいません。

`verify_qemu.py` は次の形式で C を生成し、C とアセンブリをクロスコンパイルして ELF にリンクします。
通常は検証スクリプトが全体を実行するので、この1行を別に実行する必要はありません。

```sh
lake env lean -c build/qemu/TaskScalar.c LeanCpOs/Task/Scalar.lean
```

生成したエントリの型は次のとおりです。
これは実験用のスカラー ABI で、OSEK の規定ヘッダーやバイナリ ABI 互換を表すものではありません。

```c
uint64_t lean_osek_step(uint64_t config, uint64_t state,
                       uint64_t operation, uint64_t id, uint64_t context);
```

戻り値は次状態と結果をビットに詰めています。
`runtime.c` の `os_service` はそこから、タスクを切り替えるか、継続を破棄するかを判断します。
`discard` が立てば古いタスクを非 live にし、その続きへ戻らないようにします。
単なる中断なら保存済みの context を残し、再び選ばれたときに復元します。

`context.S` は x19〜x30 と SP を保存・復元します。
x30 は復帰位置に関わるレジスタです。
新しい起動要求では、16 KiB のタスクスタックと `start_task` から始まる context を準備します。
一般モデルの `pc` を、マシンの実行アドレスとしてコピーしているわけではありません。

## 容量と検証の境界

| 項目 | このターゲットの条件 |
|---|---|
| タスク数 | 1〜4 |
| 優先度 | 0〜15 |
| 起動上限 | 各タスクで正、設定した上限の合計が8以下 |
| モデル上の ISR 深さ | 0〜15 |
| CPU | QEMU `virt`、Cortex-A53、単一コア |
| 切り替え位置 | OS サービスを呼ぶ位置、AAPCS64 の呼び出し境界 |

コンパイルは `-mgeneral-regs-only` で行い、浮動小数点・SIMD は使いません。
実ハードウェア割り込みによる任意位置の中断、FPU の保存、割り込みコントローラの動作は対象外です。
`modeled-isr-defers-dispatch` はソフトウェアでモデルの ISR 入退場を呼ぶテストです。

生成 C は実際の Lean 配布物のヘッダーを使います。
必要な実行経路は純粋な `UInt64` の計算に限定し、未使用のラッパーや初期化コードをリンク時に除去します。
検証スクリプトは初期化依存のある定数や、ELF の未解決シンボルを検出すると失敗します。
一般モデルとの対応、C 生成器、C コンパイラ、runtime、アセンブリの正しさ全体を証明したわけではありません。

## 少し変えて確かめる

**演習:** `target/aarch64/tests.c` の `qemu_main` にある最初の設定
`{3, {1,3,2}, {1,1,1}, {1,1,1}}` について、A の preemptive を0にすると、
トレースはどう変わるでしょうか。作業ブランチで最後の配列の先頭だけを変え、再実行します。

<details>
<summary>答え</summary>

`10 11 20 30` になります。
A は B を起動しても動き続け、そのまま11を記録して終了します。
その後に B、C の順に進みます。
元の期待順序 `10 20 30 11` を残したままなら、このテストは失敗するはずです。
この変更は中断・再開の検査を別の動作に変えてしまうので、観察後は元へ戻してください。

期待値は C の `EXPECT` と Python の検証スクリプトの両方にあります。
成功させるためだけに両方を書き換えず、どの性質を確認したいテストか考えます。
非プリエンプティブ設定と `Schedule` の検査は、別の
`nonpreemptive-explicit-schedule` シナリオが担当しています。

</details>

## 成果物と対応するソース

`build/qemu/` には `qemu.json`、`uart.log`、`TaskScalar.c`、`osek-task.elf`、
`symbols.txt`、`build.log` が残ります。
JSON にはツールの版と成果物の SHA-256 があり、どの出力を確認したか追えます。
この7シナリオの成功から、実機のタイミング、WCET、あらゆる割り込み状況まで結論付けることはできません。

- [Scalar アダプター](https://github.com/4ge32/lean-cp-os/blob/main/LeanCpOs/Task/Scalar.lean): `step` と `lean_osek_step` の export。
- [ターゲットの runtime](https://github.com/4ge32/lean-cp-os/blob/main/target/aarch64/runtime.c): `os_service`、`os_run`、継続の破棄と再開。
- [context 保存・復元](https://github.com/4ge32/lean-cp-os/blob/main/target/aarch64/context.S): レジスタと SP の受け渡し。
- [QEMU 検証](https://github.com/4ge32/lean-cp-os/blob/main/scripts/verify_qemu.py): C 生成、リンク、実行、7シナリオの期待順序。
- [QEMU の詳細手順と ABI](https://github.com/4ge32/lean-cp-os/blob/main/docs/QEMU.md): ビット配置、前提、全シナリオ。
