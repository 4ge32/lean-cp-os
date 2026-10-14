# Lean CP OS

## はじめて読む方へ

**[Lean CP OS Book を読む](https://4ge32.github.io/lean-cp-os/)** — 小さな OS を動かしながら AUTOSAR CP、Lean、リポジトリの構造と保守を学ぶ、全10章の日本語教材です。[検証履歴](https://4ge32.github.io/lean-cp-os/verification/index.html)からコミットごとの実行結果も参照できます。

このプロジェクトは、OS の「次にどの仕事を動かすか」を Lean で実装し、証明と実行テストの両方で確かめるプロジェクトです。3 タスクの入門用モデルから始め、設定可能な基本タスク制御と、QEMU 上での実際のタスク切り替えへ進みます。

まず [日本語の入門ガイド](docs/GETTING_STARTED.ja.md)で、タスクの動きと「証明・テストの違い」を追ってみてください。OS や Lean の予備知識は必要ありません。その後、下の実行手順、設計資料、検証結果の順に進めます。

A Lean implementation of **single-core basic-task control**, with an executable model, proofs, generated C and QEMU task execution. OSEK OS is the behavioral reference; AUTOSAR Classic Platform OS and TOPPERS ATK2 provide longer-term context. This is a kernel foundation, not a production OS or a conformance claim.

**入門用の M0:** one core; exactly three statically configured Basic Tasks, priorities 1 < 2 < 3; at most one activation each; immediate priority selection at modeled scheduling points. Suspended/Ready/Running, activation, termination and two queries are implemented in Lean 4.19.0. Actual generated C is linked to host C and exercised through a scalar C ABI.

## 今回の完成範囲

単一コアの **基本タスク**（起動して処理し、終了する仕事）を対象に、次を一つの開発段階として実装・検証します。拡張タスクは次の段階です。

1. タスク数、優先度、起動要求の上限を設定できる。同じ優先度の待ち順と、複数回の起動要求を扱う。
2. `ActivateTask`（起動）、`TerminateTask`（終了）、`ChainTask`（終了して次の仕事を起動）、`Schedule`（明示的な再選択）、`GetTaskID`、`GetTaskState` がそろう。
3. 中断された仕事は続きから、新たな起動は先頭から実行する。終了に成功した仕事の続きには戻らない。
4. Lean のモデルを証明・比較テストし、Lean から生成した C と実際のスタック切り替えを QEMU で実行する。
5. 各機能に、仕様の根拠、実装、証明または検査、学習用の説明を対応させる。

動作の基準は **OSEK OS 2.2.3** です。AUTOSAR CP OS R25-11 は将来の照合先として維持します。イベントを待って再開する拡張タスク、資源管理、アラーム、実際の割り込みハンドラは次の段階です。今回はその連携に必要な呼び出し条件をモデルに記録します。OSEK 全体への適合や、安全規格への適合を主張するものではありません。

## リポジトリの構造

| 場所 | 何を担当するか | 読むと分かること |
|---|---|---|
| `LeanCpOs/Model.lean` | 固定 3 タスクの入門用モデル | 起動・終了で状態がどう変わるか |
| `LeanCpOs/Proofs.lean` | 入門用モデルの証明 | 実行中のタスクが最大一つであることなど |
| `LeanCpOs/Bridge.lean`、`Main.lean` | 入門用モデルと C・テストとの接続 | 入力をモデルに渡し、結果を比較する方法 |
| `LeanCpOs/Task/` | 設定可能な基本タスク制御、証明、QEMU 用の容量制限付き実装 | 優先度、待ち順、複数起動、実行継続の扱い |
| `TaskMain.lean` | 基本タスクモデルの入力・出力 | 操作の列を与えて状態変化を観察する方法 |
| `c/` | ホスト C との接続と制御フロー検査 | Lean が決めた結果を C がどう使うか |
| `target/` | QEMU の起動、UART 出力、タスクのスタック・レジスタ切り替え | 選ばれたタスクを CPU 上で実際に動かす方法 |
| `tests/` | 独立した Python の計算と各実装の比較 | 想定した入力で同じ結果になるか |
| `scripts/` | ツール準備、ビルド、証明・実行検査、レポート作成 | 一連の確認を再現する方法 |
| `.github/workflows/` | push・手動実行時の検証と結果公開 | コミット単位で結果を残す方法 |
| `trace/` | 要求、根拠資料、証明、テストの対応表 | どの要求を、何で確認しているか |
| `docs/` | 入門、設計、実行方法、証明の範囲 | なぜその設計にしたか、何が未対応か |
| `build/`、`.lake/`、`evidence/` | 自動生成されるコード、実行ファイル、検証結果（Git 管理外） | 実行結果とログ。通常ここを手で編集しない |

`Model` がルールを決め、`Proofs` がその性質を示し、`Bridge` や実行基盤が外の世界につなぎます。テストは別に書いた期待動作と比較します。QEMU で動いたことと、数学的に証明したことは、それぞれの範囲を分けて記録します。

## Run

Linux x86_64, Python 3, GCC, Git, curl and tar with zstd are needed. There are no external Lean package dependencies.

```sh
bash scripts/bootstrap_lean.sh /tmp/lean-cp-toolchain
export PATH=/tmp/lean-cp-toolchain/lean-4.19.0-linux/bin:$PATH
bash scripts/bootstrap_qemu.sh "$PWD/.toolchain/qemu"
export QEMU_SYSTEM_AARCH64="$PWD/.toolchain/qemu/bin/qemu-system-aarch64"
python3 scripts/verify.py --out evidence/local
```

QEMU がすでにインストールされていれば、`bootstrap_qemu.sh` とその環境変数の設定は省略できます。上記の QEMU 準備スクリプトは Debian / Ubuntu の amd64 ホスト向けです。署名付き APT メタデータとパッケージハッシュを検証して、指定先に展開します。

一般モデルだけを試す場合は `lake build` と `python3 tests/test_task_control.py build/task-tests`、QEMU の実行だけなら `python3 scripts/verify_qemu.py build/qemu` を使います。完成判定には上の全検証を使ってください。

The verifier requires a clean committed tree. For development only, `--allow-dirty` records `exact_commit: false`; such results must not be attributed to the commit. The report is `evidence/local/index.html`; `report.json`, `trace.json`, `axioms.json`, `runtime.json`, logs, generated C, binaries and SHA256SUMS accompany it.

## What is checked

- Lean checks 76 theorem declarations: 28 for the M0 example and 48 for configurable Basic Tasks, including arbitrary finite-sequence invariant preservation, selection, FIFO head behavior, activation counts, error atomicity, and continuation/discard semantics.
- The verifier generates a complete theorem audit from the project modules; `Audit.lean` also lists the current declarations for manual use. The gate accepts only Lean's standard propositional extensionality (`propext`); additional axioms, admitted goals and native-evaluation proof bypass are rejected.
- 2,763 vectors are checked by Lean execution and linked generated C against an independent Python set-based oracle: 240 finite cases, 23 boundary cases and 625 sequences of four operations.
- A host C dispatcher demonstrates that successful termination skips the task's continuation; an idle error returns. It uses `setjmp/longjmp`, not a target context-switch implementation.
- The configurable kernel is compared with an independent Python oracle over 9,815 traces (74,056 transitions). Another 62,991 vectors exercise its bounded generated-C adapter, including invalid inputs and capacity limits; 12 cases check protocol rejection/acceptance.
- Seven QEMU AArch64 scenarios exercise real separate stacks and saved registers: preemption/resumption, FIFO, queued fresh activations, self/other ChainTask, nonpreemptive scheduling, returning errors, and modeled ISR dispatch deferral. This uses actual Lean-generated C for scheduling decisions.
- Trace links and gaps are checked separately. A structurally complete map is not complete verification.

## Navigate

### Book の編集とプレビュー

本文は `docs/book/`、目次は `docs/book/SUMMARY.md`、実行できる教材は `examples/book/` にあります。Lean を準備してから、リポジトリのルートで実行します。

```sh
bash scripts/bootstrap_mdbook.sh .toolchain/mdbook
lake build
python3 scripts/check_book.py
.toolchain/mdbook/mdbook build
python3 scripts/check_book.py --html build/book --skip-examples
.toolchain/mdbook/mdbook serve --hostname 127.0.0.1
```

ブラウザーで `http://127.0.0.1:3000` を開きます。Book は mdBook 0.4.52 を使い、インストーラーは Linux x86_64 用です。本文の Lean 例を変更したら、必ず `check_book.py` を再実行してください。PR でも教材・リンク・HTML・公開合成の検査を行います。公開時には既存の検証履歴と Book を組み合わせ、過去のレポート URL を維持します。

### 設計と検証の詳細

- [Design, proof boundary and milestones](docs/DESIGN.md)
- [基本タスク制御を理解する](docs/TASK_CONTROL.md)
- [QEMU で実際のタスクを動かす](docs/QEMU.md)
- [Sources, versions and rights](docs/SOURCES.md)
- [Runtime / C ABI audit](docs/RUNTIME.md)
- [CI, per-commit evidence and publication](docs/CI.md)
- [Machine-readable requirements](trace/requirements.json), [sources](trace/sources.json), [test catalogue](trace/tests.json)

`python3 scripts/impact.py <base-sha>` reports conservative affected requirements, theorems and tests. All gates still run for every enumerated commit.

## Current limitations

一般モデルは設定可能ですが、QEMU 用の実装は **最大 4 タスク、優先度 0〜15、起動上限の合計 8、モデル上の ISR 深さ 15** に制限しています。容量超過を黙って切り詰めず、拒否します。

拡張タスク・イベント、資源管理、アラーム、物理割り込み、マルチコア、保護、フック、完全な StartOS/ShutdownOS は未対応です。ISR の入れ子や資源保持の検査は連携条件のモデルであり、それぞれのサブシステムの実装ではありません。C の公開インターフェースと数値エラーは、このプロジェクトの対応範囲に限定します。

一般モデルと容量制限付きアダプターの対応、C への変換、アセンブリー、CPU までの精密化は形式証明していません。テストと証明の範囲はレポートに分けて記録します。飢餓防止、WCET、総スタック・メモリ上限、非同期割り込みの安全性、および BCC1/BCC2、SC1、AUTOSAR、ISO 26262 への適合も今回の完了条件には含めません。

実際の CI 結果は [GitHub Actions](https://github.com/4ge32/lean-cp-os/actions) で確認できます。過去コミットも検証した実行では、現在の版が成功していても過去の失敗によって全体が失敗になることがあります。現在の版だけを確認する場合は **Run workflow → main → scope: head** を選びます。

A source-code license has deliberately **not been selected**. Public visibility and licensing are separate decisions. No third-party specification text or reference implementation code is included.

Basic-task behavior reference: **OSEK OS 2.2.3**. Future compatibility target: **AUTOSAR CP OS R25-11** (official release checked on 2026-10-12). R25-11 OS document mapping is pending; no compatibility claim. See [source policy](docs/SOURCES.md).
