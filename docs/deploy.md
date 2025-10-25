# GitHub Pages デプロイガイド

このガイドでは、アロナちゃんのドキュメントサイトをGitHub Pagesにデプロイする方法を説明します。

## 🚀 デプロイ手順

### 1. リポジトリの準備

1. GitHubにリポジトリを作成（まだの場合）
2. ローカルでコードをコミット・プッシュ

```bash
git add .
git commit -m "Add documentation site"
git push origin main
```

### 2. GitHub Pagesの設定

1. GitHubリポジトリのページに移動
2. 「Settings」タブをクリック
3. 左サイドバーの「Pages」をクリック
4. 「Source」で「Deploy from a branch」を選択
5. 「Branch」で「main」を選択
6. 「Folder」で「/docs」を選択
7. 「Save」をクリック

### 3. デプロイの確認

設定完了後、数分でサイトが公開されます：

```
https://[ユーザー名].github.io/[リポジトリ名]
```

例：`https://username.github.io/MedicationManagement`

### 4. カスタムドメインの設定（任意）

カスタムドメインを使用する場合：

1. `docs/CNAME`ファイルを編集
2. ドメイン名を設定
3. DNS設定でCNAMEレコードを追加
4. GitHub Pagesの設定でカスタムドメインを有効化

## 🔧 トラブルシューティング

### よくある問題

1. **サイトが表示されない**
   - 設定が正しいか確認
   - 数分待ってから再確認
   - ブラウザのキャッシュをクリア

2. **スタイルが適用されない**
   - `.nojekyll`ファイルが存在するか確認
   - ファイルパスが正しいか確認

3. **画像が表示されない**
   - 画像ファイルのパスが正しいか確認
   - ファイルがコミットされているか確認

### デバッグ方法

1. GitHub Actionsのログを確認
2. ブラウザの開発者ツールでエラーを確認
3. ファイルの存在を確認

## 📝 メンテナンス

### 定期的な更新

1. コンテンツの最新化
2. リンクの確認
3. 画像の最適化
4. パフォーマンスの確認

### バックアップ

- 定期的にリポジトリをバックアップ
- 重要な変更はタグを作成

## 🔗 関連リンク

- [GitHub Pages ドキュメント](https://docs.github.com/ja/pages)
- [Jekyll ドキュメント](https://jekyllrb.com/docs/)
- [Markdown ガイド](https://www.markdownguide.org/)

## 📞 サポート

問題が発生した場合：

1. このドキュメントを確認
2. GitHub Issuesで報告
3. コミュニティで質問

---

**注意**: このドキュメントは定期的に更新されます。最新の情報はGitHubリポジトリを確認してください。
