import pandas as pd

df = pd.read_csv("C:\\Users\\Giorgos\Desktop\\ergasies metaptxiakwn\\ergasies sgourou\\WDIEXCEL.csv",delimiter=";")
df = df[df['Country Code'].isin(['ESP', 'DEU', 'GRC', 'DNK'])]
# Θέμα 1ο / Υπολογισμός του ποσοστού πληρότητας
completeness = 1 - df.isnull().sum(axis=1) / 60
# Προσθέτει μία στήλη στο dataframe,
#  η οποία περιέχει το ποσοστό πληρότητας της αντίστοιχης γραμμής
df=df.assign(Completeness=completeness)
# Υπολογισμός της μέσης τιμής της στήλης Completeness
# για το σύνολο των γραμμών του dataset
avg_completeness = df[['Completeness']].mean()
print("Average completeness: " + str(avg_completeness['Completeness']))

# Θέμα 1ο / Υπολογισμος συνεκτικότητας
# Γεμίζουμε τα κενά με 0, ώστε να μην υπάρχει πρόβλημα
# στις συγκρίσεις. Θεωρούμε ότι τα κελιά με τιμή # δεν περιέχουν δεδομένα.
df=df.fillna("#")
df=df.reset_index(drop=True)
# Για κάθε γραμμή του dataframe
for i in range(0, len(df)):
    total = 0
    # Η μεταβλητή coherence κρατάει τον αριθμό που
    # αντιστοιχεί στο μέγιστο πλήθος συνεκτικών κελιών
    # που υπάρχει σε μία γραμμή.
    coherence = 0
    # Για κάθε στήλη που αντιστοιχεί σε έτος
    # (από το 2019 έως το 1960
    for j in range(2019, 1959, -1):
        # Εάν το κελί είναι διαφορετικό από το #
        if (df.loc[i, str(j)]!='#'):
            # Αύξησε το πλήθος των συνεκτικών κελιών
            total+=1
        else:
            # 'Οταν βρεθεί κελί με τιμή #, τότε θεώρησε ότι
            # ολοκληρώθηκε ένα συνεκτικό τμήμα με μήκος total.
            # Εάν το τρέχον total είναι μεγαλύτερο από την τιμή του coheremce,
            # τότε το coherence θα αποκτήσει την τιμή του total
            # (τη μεγαλύτερη δυλαή τιμή έως αυτό το σημείο)
            if total > coherence:
                coherence = total
            total = 0
    # Πρόσθεσε στη στήλη Coherence τη μέγιστη τιμή συνεκτικότητας (coherence)
    # που υπολογίστηκε γι' αυτή τη γραμμή
    df.loc[i, "Coherence"]=coherence
result = df[['Country Code', 'Indicator Code', 'Coherence']]
print(result)
result.to_csv("coherence.csv")
