# 指定PIPS分上昇するか下降するかの2値分類問題

## 実行方法
### モデル生成
`python3 bin/create_model.py -s {symbol} -t {term} -p {base_pips} -f {from_year} -u {until_year} -m {model_type} -c {script_mode}`

- symbol: 大文字英字のシンボル（USDJPY）
- term: 時間足（1分足なら、M1）
- base_pips: 目的変数となる指定PIPS
- from_year: データ読み込み開始年
- until_year: データ読み込み終了年
- model_type: 使用モデル
    - `decision_tree`: 決定木
    - `random_forest`: ランダムフォレスト
script_mode: スクリプトモード
    - 1: モデル生成 & 保存しない
    - 2: モデル生成 & 保存
    - 3: 既存訓練済みモデルに特徴料を投入して予測のみ行う

※ モデル訓練は低スペックサーバだと厳しいので、cloud経由で転送する<br>
gitでも容量オーバーとなるので、google driveを活用する

## 環境構築
### python実行仮想環境を作成
1. anacondaをインストールしていない場合はインストール
2. 仮想環境作成
    - `conda create -n pyenv pip python`
    - 以下で環境を切り替えられる
        - `conda activate pyenv`

※ 参考：https://qiita.com/c60evaporator/items/aef6cc1581d2c4676504#%E3%83%91%E3%82%BF%E3%83%BC%E3%83%B31miniforge%E3%81%AB%E3%82%88%E3%82%8B%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB

### ライブラリのインストール
- talib
    - `conda install -c conda-forge ta-lib`
- tensorflow
    - `conda install -c apple tensorflow`


## Appendix
### Python仮想環境でJupyterを立ち上げる（MAC OSの場合）
1. 仮想環境に切り替え
    - `conda activate pyenv`
2. Jupyter Notebookをインストール
    - `conda install notebook ipykernel`
3. Jupyter Notebookのkernelに仮想環境を追加
    - `ipython kernel install --user --name vir_env`
4. 以下で仮想環境が追加されていればOK
    - `jupyter kernelspec list`
5. 立ち上げ
    - `jupyter notebook`