import os
from numpy import true_divide
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
import time
import pandas as pd
from bs4 import BeautifulSoup
import datetime as dt
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

pd.set_option('display.unicode.east_asian_width', True)


# Chromeを起動する関数

def set_driver(driver_path, headless_flg):

    if "chrome" in driver_path:
        options = ChromeOptions()
    else:
        options = Options()

    # ヘッドレスモード（画面非表示モード）の設定
    if headless_flg == True:
        options.add_argument('--headless')

    # 起動オプションの設定
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36')
    # options.add_argument('log-level=3')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--incognito')          # シークレットモードの設定を付与

    # ChromeのWebDriverオブジェクトを作成する。
    if "chrome" in driver_path:
        return Chrome(executable_path=os.getcwd() + "/" + driver_path,options=options)
    else:
        return Firefox(executable_path=os.getcwd()  + "/" + driver_path,options=options)


# ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪
# ページ内のデータ取得用関数
# DataFrameと、次ページへのリンクのタグ返す
# ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪

def page_process(page_html):
    # htmlをparse
    parse_html = BeautifulSoup(page_html, 'html.parser')

    ### 会社名を取得　→　co_name-list
    #　h3 をリストに
    h3_lists = parse_html.find_all('h3', class_='cassetteRecruit__name')
    #　h3 テキストをリストに
    h3_text_lists=[ list.string for list in h3_lists ]  
    #　テキストから会社名だけ抜いて　リストに
    co_name_list = [list.split(' |')[0] for list in h3_text_lists]

    ### 情報更新日を取得　→　update_list
    #　情報更新日の<p>を取得
    update_p_lists = parse_html.find_all('p', class_='cassetteRecruit__updateDate')
    #　<p>の中の<span>の文字列を抜き出す
    update_list=[list.select('span')[0].string for list in update_p_lists]

    #　給与の情報を取得　→　salary_list
    #　tableタグを取得
    # DataFrameに。１列目をindexに指定
    tables = parse_html.find_all('table', class_='tableCondition')
    df = pd.read_html(str(tables), header=None, index_col=0)
    #　indexが給与の値を取得
    salary_list = [ table.loc["給与",1] for table in df ]

    ###listからDataFrameへ
    df2 = pd.DataFrame({'会社名':co_name_list, '給与':salary_list, '情報更新日':update_list})

    is_next = parse_html.select_one('.pager__next > .iconFont--arrowLeft')
    
    return df2, is_next


# main処理


def main():

    url = "https://tenshoku.mynavi.jp/"
    
    search_keyword  = input("検索キーワードを入力して、エンターキーを押して下さい。＞＞")
    #ログファイル用の準備
    i =  0  #ページ数カウンター
    log_list = [f"{dt.datetime.now()}：作業開始"]   #リストに作業進捗を記録
    
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # driverを起動
    if os.name == 'nt': #Windows
        driver = set_driver("chromedriver.exe", False)
    elif os.name == 'posix': #Mac
        driver = set_driver("chromedriver", False)
    # Webサイトを開く
    driver.get(url)
    time.sleep(5)
    # ポップアップを閉じる
    driver.execute_script('document.querySelector(".karte-close").click()')
    time.sleep(5)
    # ポップアップを閉じる
    driver.execute_script('document.querySelector(".karte-close").click()')

    # 検索窓に入力
    driver.find_element_by_class_name(
        "topSearch__text").send_keys(search_keyword)
    # 検索ボタンクリック
    driver.find_element_by_class_name("topSearch__button").click()

    time.sleep(3)

    #空のDataFrame準備
    df_list = pd.DataFrame()

    # 現在のページのhtml取得
    page_html = driver.page_source


    try:
        #################################
        # ページ終了まで繰り返し取得
        while True:
            re = page_process(page_html)
            df_list=pd.concat([df_list,re[0]])  #データフレームを結合
            #リストに作業進捗を追記
            #ページカウンターセット
            i += 1
            log_list.append(f"{dt.datetime.now()}：{i:02}ページ目完了")

            if re[1] == None:
                log_list.append(f"{dt.datetime.now()}：情報取得完了")
                break
            else:
                # ポップアップを閉じる
                # driver.execute_script('document.querySelector(".karte-close").click()')
                next_url = url + re[1].get('href')
                driver.get(next_url)
                time.sleep(5)
                page_html = driver.page_source

        ###### end while ################

        df_list= df_list.reset_index(drop=True)
        df_list.index = df_list.index + 1
        df_list.to_csv('test.csv', encoding='shift jis')
        data_count = str(len(df_list))

    except Exception as e:
        log_list.append(f"{dt.datetime.now()}：エラー発生\n\n※※エラー内容：{e} ")
        print("エラーが発生しました。処理を終了します。")
        print("エラー内容：" , e)

    #ログファイルの出力
    log_list.insert(0,"★★検索キーワード：" + search_keyword +"　　検索結果："+ data_count+ "件\n")   #検索キーワードを記録

    now_time = dt.datetime.now()
    with open(f"{now_time:%Y%m%d-%H%M%S}.txt", mode='w', encoding='utf-8') as f:
        f.write("\n".join(log_list))

    
    # ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪
    # ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪
        


# 直接起動された場合はmain()を起動(モジュールとして呼び出された場合は起動しないようにするため)
if __name__ == "__main__":
    main()
