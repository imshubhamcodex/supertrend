import numpy as np
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import mplfinance as mpl
from datetime import datetime, time as datetime_time
import time
import requests
from pytz import timezone

from mercury_Bot import send_message, send_img

# Fetch data
def fetch_data(ticker="^NSEI", time_interval="1h"):
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=300)
    data = yf.download(ticker, start=start_date, end=end_date, interval=time_interval)
    return data


def fetch_todays_data_from_YF():
    current_datetime =  str(datetime.today().date())
    date_obj = datetime.strptime(current_datetime, "%Y-%m-%d")
    today_timestamp = str(date_obj.timestamp()).split('.')[0]
    current_timestamp = str(time.mktime(time.localtime())).split('.')[0]
    # today_timestamp = str((datetime.now() - timedelta(days=5)).timestamp()).split('.')[0]  # TEST
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"115\", \"Chromium\";v=\"115\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203",
        "Referer": "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?symbol=%5ENSEI&period1="+ today_timestamp +"&period2=" + current_timestamp + "&useYfid=true&interval=1h&includePrePost=true&events=div%7Csplit%7Cearn&lang=en-US&region=US&crumb=pRymmeKo5Qz&corsDomain=finance.yahoo.com"
    }
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?symbol=%5ENSEI&period1="+ today_timestamp +"&period2=" + current_timestamp + "&useYfid=true&interval=1h&includePrePost=true&events=div%7Csplit%7Cearn&lang=en-US&region=US&crumb=pRymmeKo5Qz&corsDomain=finance.yahoo.com")
    
    response = requests.get(url,headers=headers)
    json_data = response.json()

    if 'timestamp' in json_data['chart']['result'][0]:
        timestamp = json_data['chart']['result'][0]['timestamp']
        open_prices = json_data['chart']['result'][0]['indicators']['quote'][0]['open']
        high_prices = json_data['chart']['result'][0]['indicators']['quote'][0]['high']
        low_prices = json_data['chart']['result'][0]['indicators']['quote'][0]['low']
        close_prices = json_data['chart']['result'][0]['indicators']['quote'][0]['close']

        df = pd.DataFrame({
            "Time Frame": timestamp,
            "Open": open_prices,
            "High": high_prices,
            "Low": low_prices,
            "Close": close_prices
        })

        ist = timezone('Asia/Kolkata')
        df['Time Frame'] = pd.to_datetime(df['Time Frame'], unit='s').dt.tz_localize('UTC').dt.tz_convert(ist)
        df['Time Frame'] = pd.to_datetime(df['Time Frame'], unit='s')
            
        result_df = pd.DataFrame(df)
        current_date = datetime.now().date()
        
        if not result_df.empty:
            result_df['Time Frame'] = pd.to_datetime(result_df['Time Frame'], format='%H:%M:%S').apply(lambda x: x.replace(year=current_date.year, month=current_date.month, day=current_date.day))
            result_df.rename(columns={'Time Frame': 'Date'}, inplace=True)
            result_df.set_index('Date', inplace=True)
            todays_data = result_df.rename_axis('Datetime').reset_index()
            
            df = pd.DataFrame(todays_data)
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            df.set_index('Datetime', inplace=True)
            
            data = fetch_data()
            df = pd.concat([data, df], ignore_index=False)
            return df
    
    return pd.DataFrame({})

def atr(DF,n):
    df=DF.copy()
    df['High-Low']=abs(df['High']-df['Low'])
    df['High-PreviousClose']=abs(df['High']-df['Close'].shift(1))
    df['Low-PreviousClose']=abs(df['Low']-df["Close"].shift(1))
    df['TrueRange']=df[['High-Low','High-PreviousClose','Low-PreviousClose']].max(axis=1,skipna=False)
    df['ATR']=df['TrueRange'].ewm(com=n,min_periods=n).mean()
    return df['ATR']


def supertrend(DF,n,m):
    df = DF.copy()
    df['ATR'] = atr(df,n)
    df["BASIC_UPPERBAND"]=((df['High']+df['Low'])/2) + m*df['ATR'] 
    df["BASIC_LOWERBAND"]=((df['High']+df['Low'])/2) - m*df['ATR']
    df["FINAL_UPPERBAND"]=df["BASIC_UPPERBAND"]
    df["FINAL_LOWERBAND"]=df["BASIC_LOWERBAND"]
    ind = df.index
    for i in range(n,len(df)):
        if df['Close'][i-1]<=df['FINAL_UPPERBAND'][i-1]:
            df.loc[ind[i],'FINAL_UPPERBAND']=min(df['BASIC_UPPERBAND'][i],df['FINAL_UPPERBAND'][i-1])
        else:
            df.loc[ind[i],'FINAL_UPPERBAND']=df['BASIC_UPPERBAND'][i]    
    for i in range(n,len(df)):
        if df['Close'][i-1]>=df['FINAL_LOWERBAND'][i-1]:
            df.loc[ind[i],'FINAL_LOWERBAND']=max(df['BASIC_LOWERBAND'][i],df['FINAL_LOWERBAND'][i-1])
        else:
            df.loc[ind[i],'FINAL_LOWERBAND']=df['BASIC_LOWERBAND'][i]  
    df['Strend']=np.nan
    for test in range(n,len(df)):
        if df['Close'][test-1]<=df['FINAL_UPPERBAND'][test-1] and df['Close'][test]>df['FINAL_UPPERBAND'][test]:
            df.loc[ind[test],'Strend']=df['FINAL_LOWERBAND'][test]
            break
        if df['Close'][test-1]>=df['FINAL_LOWERBAND'][test-1] and df['Close'][test]<df['FINAL_LOWERBAND'][test]:
            df.loc[ind[test],'Strend']=df['FINAL_UPPERBAND'][test]
            break
    for i in range(test+1,len(df)):
        if df['Strend'][i-1]==df['FINAL_UPPERBAND'][i-1] and df['Close'][i]<=df['FINAL_UPPERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_UPPERBAND'][i]
        elif  df['Strend'][i-1]==df['FINAL_UPPERBAND'][i-1] and df['Close'][i]>=df['FINAL_UPPERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_LOWERBAND'][i]
        elif df['Strend'][i-1]==df['FINAL_LOWERBAND'][i-1] and df['Close'][i]>=df['FINAL_LOWERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_LOWERBAND'][i]
        elif df['Strend'][i-1]==df['FINAL_LOWERBAND'][i-1] and df['Close'][i]<=df['FINAL_LOWERBAND'][i]:
            df.loc[ind[i],'Strend']=df['FINAL_UPPERBAND'][i]
    return df['Strend']


def st_changes(data):
    data.index = pd.to_datetime(data.index)
    style = mpl.make_mpf_style(base_mpf_style='yahoo', gridstyle=':')
    fig, axes = mpl.plot(data, type='candle', style=style, addplot=[mpl.make_addplot(data['supertrend'], color='blue')],figsize=(16, 8) ,returnfig=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"mplfinance_chart_{timestamp}.png"
    fig.savefig(filename)
    send_img(filename)
    send_message("*SuperTrend Direction Changed on ^NSEI @ [1 hr]*")
    

def main():
    data = fetch_todays_data_from_YF()
    
    if len(data) == 0:
        return
    
    n=4
    m=18
    data['supertrend']=supertrend(data,n,m)
    
    if 'Datetime' not in data.columns:
        data = add_datetime_column(data)
    
    data.set_index('Datetime', inplace=True)
    add = mpl.make_addplot(data["supertrend"], color='blue')
    
    data['supertrend_diff'] = data['supertrend'].diff().abs()
    threshold = 300
    
    if data.iloc[-1]['supertrend_diff'] > threshold:
        st_changes(data)
        time.sleep(60 * 60)


def add_datetime_column(data):
    if 'Datetime' not in data.columns:
        data['Datetime'] = pd.date_range(start=str(data.iloc[0].name), periods=len(data), freq='15min')  # Example date range
    return data 



while True:
    current_time = datetime.now().time()
    print("\r" +"Time: "+ str(current_time), end='', flush=True)
    print(" ")
    
    for hour in range(9, 16):  # From 9 AM to 3 PM
        start_timei = datetime_time(hour, 15)                
        if start_timei <= current_time :
            main()
            break
    
    time.sleep(1 * 60)  # 60-second wait





