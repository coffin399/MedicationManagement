# アロナちゃん - Discord服薬リマインダーBOT ドキュメント

このディレクトリには、GitHub Pages用のドキュメントサイトが含まれています。

## 📁 ファイル構成

- `index.html` - メインページ（ホーム）
- `features.html` - 機能詳細ページ
- `setup.html` - セットアップガイド
- `commands.html` - コマンド一覧
- `.nojekyll` - Jekyllを無効化（GitHub Pages用）
- `CNAME` - カスタムドメイン設定（任意）

## 🚀 GitHub Pagesでの公開方法

### 1. リポジトリの設定

1. GitHubリポジトリの「Settings」タブを開く
2. 左サイドバーの「Pages」をクリック
3. 「Source」で「Deploy from a branch」を選択
4. 「Branch」で「main」を選択
5. 「Folder」で「/docs」を選択
6. 「Save」をクリック

### 2. 公開URL

設定完了後、以下のURLでサイトにアクセスできます：
```
https://[ユーザー名].github.io/[リポジトリ名]
```

### 3. カスタムドメイン（任意）

カスタムドメインを使用する場合：

1. `CNAME`ファイルを編集してドメイン名を設定
2. DNS設定でCNAMEレコードを追加
3. GitHub Pagesの設定でカスタムドメインを有効化

## 🎨 カスタマイズ

### スタイルの変更

各HTMLファイルの`<style>`タグ内のCSSを編集することで、デザインをカスタマイズできます。

### ページの追加

新しいページを追加する場合：

1. 新しいHTMLファイルを作成
2. ナビゲーションメニューにリンクを追加
3. 既存のページから新しいページへのリンクを追加

### コンテンツの更新

- 機能の変更時は`features.html`を更新
- セットアップ手順の変更時は`setup.html`を更新
- コマンドの追加・変更時は`commands.html`を更新

## 📝 メンテナンス

- 定期的にコンテンツを最新の状態に保つ
- 新しい機能が追加されたらドキュメントを更新
- ユーザーフィードバックに基づいて改善

## 🔗 リンク

- [メインページ](index.html)
- [機能詳細](features.html)
- [セットアップガイド](setup.html)
- [コマンド一覧](commands.html)
