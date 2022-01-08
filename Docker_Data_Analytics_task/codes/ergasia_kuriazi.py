import pandas as pd
import matplotlib.pyplot as plt
import requests
from requests.auth import HTTPDigestAuth
import json
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import numpy as np

def insights1():
    # Mean number of employees in companies
    # grouped by MSA description (Area)
    data = pd.read_csv("Datasets\\dataset.csv")
    grouped_df = data.groupby("MSADSCR")
    #upologizei ton meso oro ergazomenwn mias perioxhs
    mean_df = grouped_df.mean()
    #to reset_index kanei tis prwtes stiles 0,1,2,3,4 kanei thn arithmisi twn grammwn ews to 933
    mean_df = mean_df.reset_index()
    print(mean_df[["MSADSCR", "EMPLTOT_N"]])


def insights2():
    # Estimate correlation between enterpise size
    # and payrol columns of the dataset
    data = pd.read_csv("Datasets\\dataset.csv")
    column_1 = data["ENTRSIZE"]
    column_2 = data["PAYRTOT_N"]
    #to correlation vriskei th susxetisi tou mege8ous ths epixeirhshs me tous misthous pou dinei h epixeirhsh,dhladh oso megalwnei h epixeirhsh dinei megaluterous misthous
    correlation = column_1.corr(column_2)
    #to correlation einai enas arithmos pou kumainetai apo 0 ews 1. oso poio megalos arithmos einai aftos, toso pio isxuri einai h susxetish
    #to 4 einai na mou tupwsei 4 dekadika psifia
    print("Correlation between size of enterprise and salary expenses:" + str(round(correlation, 4)))


def insights3():
    #upologizei oles tis susxetiseis olwn twn stilwn tou dataframe metaksu tous
    # Calculate correlations among all columns of the dataset.
    # Negative correlations indicate that when the first column increases
    # the second column decreases and vice versa
    data = pd.read_csv("Datasets\\dataset.csv")
    # Remove an unnamed column from the dataset that contains
    # just the numbering of rows
    del data['Unnamed: 0']
    correlation_df = data.corr().dropna(axis=0, how='all')
    correlation_df = correlation_df.dropna(axis=1, how='all')
    print(correlation_df)


def visual1():
    # Shows a heatmap of correlations among all columns of the dataset.
    # Negative correlations indicate that when the first column increases
    # the second column decreases and vice versa
    data = pd.read_csv("Datasets\\dataset.csv")
    # Remove an unnamed column from the dataset that contains
    # just the numbering of rows
    del data['Unnamed: 0']
    correlation_df = data.corr().dropna(axis=0, how='all')
    correlation_df = correlation_df.dropna(axis=1, how='all')
    print(correlation_df)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax = sns.heatmap(correlation_df, square=True, vmin=-1, vmax=1, center=0, cmap=sns.diverging_palette(20, 220, n=200))
    plt.show()




def web_parser1():
    #sundeetai se ena web service(ena programma sto opoio upovallw ena erwtima mesa xrhsimopoiwntas ena url)
    pass
    url = "http://api.naics.us/v0/q?year=2012"

    restResponse = requests.get(url)

    # For successful API call, response code will be 200 (OK)
    #ta dedomena pou einai sto dataset ta pairnei mesa sto programma mas me tin entoli request.get (line 74)
    #gia na epikoinwnisw me to server, elegxw an exei ginei h epikoinwnia
    if (restResponse.ok):
        df = pd.DataFrame(json.loads(restResponse.content))
        #den eksuphretousan kapoies times. Aftes oi times egrafan se mia sthlh 31-33 kai egw kratisa to 31
        df = df.replace(to_replace="31-33", value="31")
        df = df.replace(to_replace="44-45", value="44")
        df = df.replace(to_replace="48-49", value="48")

        df.to_csv('Datasets\\restdata.csv')
    else:
        # If response code is not ok (200), print the resulting http error code with description
        restResponse.raise_for_status()




def insights4():
    # Calculate the median of employes of companies
    # per sector title sorted by total number of employees
    data1 = pd.read_csv("Datasets\\dataset.csv")
    data2 = pd.read_csv("Datasets\\restdata.csv")

    # Merge the master dataset with NAICS dataset
    data2 = data2[["code", "title"]]
    data2 = data2.rename({'code': 'NAICS'}, axis=1)
    data2["NAICS"] = data2["NAICS"].astype(str).astype(int)
    data1 = data1.merge(data2, on='NAICS', how='left')
    # Group data by sector title
    grouped_df = data1.groupby("title")
    mean_df = grouped_df.median()
    mean_df = mean_df.reset_index()
    print(mean_df[["title", "EMPLTOT_N"]].sort_values('EMPLTOT_N'))


def insights5():
    # Groups companies by county and size code
    # and provides the total number of employees per company size per county
    data1 = pd.read_csv("Datasets\\dataset.csv")
    data2 = pd.read_csv("Datasets\\scrapedata.csv")

    data2 = data2[["CBSA 2003 Code", "Counties/Other Areas"]]
    data2 = data2.rename({'CBSA 2003 Code': 'MSA'}, axis=1)
    data1 = data1.merge(data2, on='MSA', how='left')

    data1 = data1[['Counties/Other Areas', 'sizedscr', 'EMPLTOT_N']]
    grouped_df = data1.groupby(['Counties/Other Areas', 'sizedscr'])
    sum_df = grouped_df.sum()
    print(sum_df)



def visual2():
    # Creates a scatter clustering diagram which
    # clusters together companies according to their
    # number of establishments and total number of employees
    data = pd.read_csv("Datasets\\dataset.csv")
    data = data[['ESTBTOT', 'EMPLTOT_N']]
    print(data)
    # x = StandardScaler().fit_transform(data)
    scaler = StandardScaler()
    # transform data
    scaled = scaler.fit_transform(data)
    kmeans = KMeans(n_clusters=5, init='random')
    kmeans.fit(scaled)
    pred = kmeans.predict(scaled)
    np.unique(pred)
    fig, ax = plt.subplots(figsize=(12, 8))
    plt.scatter(scaled[:, 0], scaled[:, 1], c=pred, cmap='viridis')
    plt.show()





def visual3():
    # Creates a bar chart with sum of companies per
    # NAICS code
    data = pd.read_csv("Datasets\\dataset.csv")
    data = data[['NCSDSCR', 'FIRMTOT']]
    grouped_df = data.groupby(['NCSDSCR'])
    sum_df = grouped_df.sum().sort_values('FIRMTOT')
    plt.rcParams["figure.figsize"] = [20, 6]
    sum_df.plot(kind="bar")
    plt.show()





def summary1():
    # Merges the master dataset with the CBSA data
    # and exports result to the "summary1.csv" file
    data1 = pd.read_csv("Datasets\\dataset.csv")
    data2 = pd.read_csv("Datasets\\scrapedata.csv")

    data2 = data2[["CBSA 2003 Code", "Counties/Other Areas"]]
    data2 = data2.rename({'CBSA 2003 Code': 'MSA'}, axis=1)
    data1 = data1.merge(data2, on='MSA', how='left')
    data1.to_csv('Datasets\\summary1.csv')




def summary2():
    # Groups companies by county and size code
    # and provides the total number of employees per company size per county
    # The result is exported to a JSON file
    data1 = pd.read_csv("Datasets\\dataset.csv")
    data2 = pd.read_csv("Datasets\\scrapedata.csv")

    data2 = data2[["CBSA 2003 Code", "Counties/Other Areas"]]
    data2 = data2.rename({'CBSA 2003 Code': 'MSA'}, axis=1)
    data1 = data1.merge(data2, on='MSA', how='left')

    data1 = data1[['Counties/Other Areas', 'sizedscr', 'EMPLTOT_N']]
    grouped_df = data1.groupby(['Counties/Other Areas', 'sizedscr'])
    sum_df = grouped_df.sum()
    sum_df.to_json('Datasets\\summary2.json')


def main():

    web_parser1()
    insights1()
    insights2()
    insights3()
    insights4()
    insights5()
    visual1()
    visual2()
    visual3()
    summary1()
    summary2()

if __name__=="__main__":
    main()