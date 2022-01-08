import wbdata
import pandas
import matplotlib.pyplot as plt
import seaborn as sns

# Επιλογή χωρών για ανάακτηση δεικτών
countries = ['ESP', 'DEU', 'GRC', 'DNK']

# Επιλεγμένοι δείκτες
indicators = {'NY.GNP.PCAP.CD': 'GNI per Capita',
              'BX.KLT.DINV.CD.WD': 'Foreign direct investment, net inflows (BoP, current US$)',
              'BG.GSR.NFSV.GD.ZS': 'Trade in services (% of GDP)',
              'EN.ATM.CO2E.KT':    'CO2 emissions (kt)',
              'EN.URB.LCTY': 'Population in largest city',
              'NE.CON.TOTL.CD':    'Final consumption expenditure (current US$)',
              'SP.ADO.TFRT': 'Adolescent fertility rate (births per 1,000 women ages 15-19)',
              'SP.POP.DPND': 'Age dependency ratio (% of working-age population)',
              'FD.RES.LIQU.AS.ZS': 'Bank liquid reserves to bank assets ratio (%)'
              }

# Κλήση του API της World Bank και ανάκτηση δεδομένων σε dataframe
df = wbdata.get_dataframe(indicators, country=countries, convert_date=False)
print(df)
# Υπολογισμός της συσχέτισης των δεικτών,
# αφού πρώτα απορριφθούν οι κενές τιμές
correlation_df = df.corr().dropna(axis=0, how='all')
correlation_df = correlation_df.dropna(axis=1, how='all')
# Δημιουργία heat map
fig, ax = plt.subplots(figsize=(12, 8))
ax = sns.heatmap(correlation_df, square=True, vmin=-1, vmax=1, center=0, cmap=sns.diverging_palette(20, 220, n=200))
plt.show()
