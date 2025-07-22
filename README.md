# MeCab による日本語動詞抽出スクリプト

## 概要

このリポジトリでは、太宰治『走れメロス』冒頭のテキストから動詞の基本形を抽出するためのスクリプトを提供しています。形態素解析エンジン MeCab を使用し、品詞情報をもとに動詞のみを抽出します。

## セットアップ

```bash
# 仮想環境の作成（任意）
python3 -m venv .venv
source .venv/bin/activate

# MeCab のインストール（macOSの場合）
brew install mecab mecab-ipadic

# Pythonバインディングのインストール
pip install mecab-python3