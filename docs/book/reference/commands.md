# コマンド集

すべてリポジトリのルートから実行します。
ホストの基本条件は Linux x86_64、Python 3、GCC、Git、curl、tar と zstd です。
Lean は `lean-toolchain` に指定された版を使います。

## Lean を用意する

```sh
bash scripts/bootstrap_lean.sh /tmp/lean-cp-toolchain
export PATH=/tmp/lean-cp-toolchain/lean-4.19.0-linux/bin:$PATH
lean --version
lake build
```

Lean の表示が `4.19.0` であること、ビルドが正常終了することを確認します。
準備スクリプトは初回にネットワーク接続を使います。

## 学習例と一般モデルを検査する

```sh
lake env lean examples/book/change.lean
python3 tests/test_task_control.py build/task-tests
```

教材は成功時に出力しません。比較テストは JSON を表示し、
`build/task-tests/task-control.json` に結果を保存します。
生成 C の実行ファイルを全検証で作成済みなら、追加の比較を指定できます。

```sh
python3 tests/test_task_control.py build/task-tests --scalar-runner build/task-scalar-host
```

## QEMU を準備して実行する

Debian / Ubuntu の amd64 ホストで、管理者権限を使わず指定先へ配置する例です。
対応する QEMU が既にあれば準備は省略できます。

```sh
bash scripts/bootstrap_qemu.sh "$PWD/.toolchain/qemu"
export QEMU_SYSTEM_AARCH64="$PWD/.toolchain/qemu/bin/qemu-system-aarch64"
python3 scripts/verify_qemu.py build/qemu
```

成功時は `PASS QEMU: 7 scenarios; real task stacks; generated Lean decisions` と表示されます。
`build/qemu/qemu.json` と `build/qemu/uart.log` が結果の入口です。

## 全検証を実行する

```sh
python3 scripts/verify.py --out evidence/local
```

コミット済みで変更のない作業ツリーを使います。
`build/` と `.lake/build/` を再生成するので、Book のビルドや別の検証と同時には実行しません。
結果は `evidence/local/index.html`、機械可読の情報は同じ場所の `report.json` です。
編集中に限って使う実行は次です。

```sh
python3 scripts/verify.py --out evidence/development --allow-dirty
```

変更のある作業ツリーでは `exact_commit: false` となり、コミット済み成果の検証と区別します。
結果の意味は[第 9 章](../09-evidence.md)を参照してください。

## Book を検査・表示する

```sh
bash scripts/bootstrap_mdbook.sh .toolchain/mdbook
lake build
python3 scripts/check_book.py
.toolchain/mdbook/mdbook build
python3 scripts/check_book.py --html build/book --skip-examples
.toolchain/mdbook/mdbook serve --hostname 127.0.0.1
```

ビルド先は `build/book/` です。表示されたローカル URL を開き、終了するときは `Ctrl+C` を押します。
全検証が `build/` を作り直すため、最終的な Book のビルドは全検証の後に行います。

## 変更の影響を読む

```sh
git status --short
git diff
git diff --cached
python3 scripts/impact.py HEAD~1
```

`impact.py` は指定したコミットから `HEAD` までの変更だけを読みます。
編集中の差分を含まないことに注意してください。

## 困ったとき

| 症状 | 確認すること |
|---|---|
| `lake: command not found` | このシェルで `PATH` を設定したか |
| Lean の import が見つからない | ルートで `lake build` を実行し、`lake env lean` を使っているか |
| 全検証が `working tree is not exact HEAD` で止まる | 未コミット変更を確認する。開発確認なら `--allow-dirty` の条件を理解して使う |
| `qemu-task-control` が失敗 | QEMU の配置・環境変数と工程ログを読む。未導入は成功扱いにならない |
| Book の include が失敗 | 教材の位置と、章ファイルからの相対パスを確認する |
| 検証後に Book が消えた | 全検証が `build/` を再生成したため、Book を再ビルドする |

各スクリプトの実装は [scripts/](https://github.com/4ge32/lean-cp-os/tree/main/scripts)、
ホスト固有の詳細は [RUNTIME.md](https://github.com/4ge32/lean-cp-os/blob/main/docs/RUNTIME.md)で確認できます。
