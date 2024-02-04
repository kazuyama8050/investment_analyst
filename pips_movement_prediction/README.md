# 指定PIPS分上昇するか下降するかの2値分類問題

## 環境構築（MAC OSの場合）
### python実行仮想環境を作成
1. 仮想環境作成
    - `conda create -n pyenv pip python`
    - 以下で環境を切り替えられる
        - `conda activate pyenv`

※ 参考：https://qiita.com/c60evaporator/items/aef6cc1581d2c4676504#%E3%83%91%E3%82%BF%E3%83%BC%E3%83%B31miniforge%E3%81%AB%E3%82%88%E3%82%8B%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB

### ライブラリのインストール
- talib
    - `conda install -c conda-forge ta-lib`


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