# Mobile Order Mock Backend

## 概要

モバイルオーダーアプリのフロントエンド練習用バックエンドです。

## 起動方法

```bash
docker compose up --build
```

## APIドキュメント

起動後、以下にアクセスしてください。

[http://localhost:8000/docs](http://localhost:8000/docs)

## ユーザ仕様

今回はログイン機能はありません。
すべて user_id = 1 のユーザとして処理されます。

## 初期データ

以下の商品が登録されています。

- アイスコーヒー
- ホットコーヒー
- カフェラテ
- 紅茶
- サンドイッチ
- チーズケーキ

## フロントエンドで作ってほしい画面

- 商品一覧画面
- カート画面
- 注文完了画面
- 注文履歴画面
- 注文詳細画面

## テスト実行（Dockerのみ）

ローカルPython環境を汚さずに、Docker上だけでテストできます。

`test` サービスは `test` プロファイルに分離しているため、通常の起動コマンド
`docker compose up --build` では実行されません。

```bash
docker compose run --rm test
```

APIサーバーを起動したい場合は、従来どおり以下を使います。

```bash
docker compose up --build
```
