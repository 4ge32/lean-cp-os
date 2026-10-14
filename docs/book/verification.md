# 検証履歴を開く

検証履歴には、コミットごとの実行結果・ログ・証明やテストの記録を残しています。学習用の本文を読んだあとに、実際の結果と照らし合わせてください。

**[公開済みの検証履歴を開く →](verification/index.html)**

ローカルの Book 単体ビルドには過去の検証データは含まれません。履歴は GitHub Pages 公開時に組み合わせます。ローカルからは[公開サイトの履歴](https://4ge32.github.io/lean-cp-os/verification/index.html)または [GitHub Actions](https://github.com/4ge32/lean-cp-os/actions)を開けます。

## 最初に確認すること

1. 調べたいソースのコミット SHA とレポートの SHA が一致するか。
2. 実行が `passed`、`failed`、`not_run` のどれか。
3. 各段階の結果と、何を対象にした証明・テストなのか。

`passed` は、その実行で必要な検査が成功したという意味です。仕様全体への適合や、すべての実行条件について正しさが示されたという意味ではありません。詳しくは[第9章](09-evidence.md)を参照してください。

既存の `commits/<SHA>/runs/<run-id>-<attempt>/`、`runs/`、`latest.json` の場所は維持しています。`latest.json` は最新の**記録済み実行**を指し、まだ検証されていない最新コミットの成功を表すものではありません。
