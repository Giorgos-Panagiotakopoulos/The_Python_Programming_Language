import pandas as pd
import numpy as np
import seaborn as sns
import os
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from matplotlib import pyplot
os.chdir("C:\\Users\\Giorgos\\Desktop\\ergasies_metaptxiakwn\\ergasies sgourou")
df = pd.read_csv("heart_failure_clinical_records_dataset.csv")

# data information
df.head()
df.info()

##############################################################################
###################### Random Forest Feature Selection #######################
##############################################################################
X = df.iloc[:,:-1]
y = df.iloc[:,-1]

coln = X.columns

# Standardizing the features
X = StandardScaler().fit_transform(X)

rf = RandomForestClassifier(n_jobs=-1, n_estimators=50, verbose=3)
rf.fit(X,y)

fi = pd.DataFrame(rf.feature_importances_, coln)
fi.columns = ['Importance']
# Sort the dataframe
fi = fi.sort_values('Importance', ascending=False)
fi['Features'] = fi.index

sns.factorplot(x='Importance', y='Features', data = fi, kind="bar", 
               size=14, aspect=1.9, palette='coolwarm')
pyplot.show()
##############################################################################

##############################################################################
###################### PC Feature Selection #######################
##############################################################################
from sklearn.decomposition import PCA
pca = PCA(.95)

pca.fit(X)

X_PC = pca.transform(X)

X_PC = StandardScaler().fit_transform(X_PC)

rf_PC = RandomForestClassifier(n_jobs=-1, n_estimators=50, verbose=3)
rf_PC.fit(X_PC,y)

fi_PC = pd.DataFrame(rf_PC.feature_importances_)
fi_PC.columns = ['PC_Importance']

# Sort the dataframe
fi_PC['PC_Features'] = ['PC1','PC2','PC3','PC4','PC5','PC6','PC7','PC8','PC9','PC10','PC11']
fi_PC = fi_PC.sort_values('PC_Importance', ascending=False)

sns.factorplot(x='PC_Importance', y='PC_Features', data = fi_PC, kind="bar", 
               size=14, aspect=1.9, palette='coolwarm')
pyplot.show()
##############################################################################
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score

def ROC_logistic(Xmat,ymat):
    trainX, testX, trainy, testy = train_test_split(Xmat, ymat, test_size=0.5, random_state=2)
    # generate a no skill prediction (majority class)
    ns_probs = [0 for _ in range(len(testy))]
    # fit a model
    model = LogisticRegression(solver='lbfgs')
    model.fit(trainX, trainy)
    # predict probabilities
    lr_probs = model.predict_proba(testX)
    # keep probabilities for the positive outcome only
    lr_probs = lr_probs[:, 1]
    # calculate scores
    ns_auc = roc_auc_score(testy, ns_probs)
    lr_auc = roc_auc_score(testy, lr_probs)
    # summarize scores
    print('No Skill: ROC AUC=%.3f' % (ns_auc))
    print('Logistic: ROC AUC=%.3f' % (lr_auc))
    # calculate roc curves
    ns_fpr, ns_tpr, _ = roc_curve(testy, ns_probs)
    lr_fpr, lr_tpr, _ = roc_curve(testy, lr_probs)
    # plot the roc curve for the model
    pyplot.plot(ns_fpr, ns_tpr, linestyle='--', label='No Skill')
    pyplot.plot(lr_fpr, lr_tpr, marker='.', label='Logistic')
    # axis labels
    pyplot.xlabel('False Positive Rate')
    pyplot.ylabel('True Positive Rate')
    # show the legend
    pyplot.legend()
    # show the plot
    pyplot.show()


X_feat3 = df[['time', 'ejection_fraction', 'serum_creatinine']]

ROC_logistic(X_feat3,y)

pca = PCA(n_components=11)
X_PC_scores = pca.fit_transform(X)

X_PC_scores_selected = X_PC_scores[:,[1,3,2,10,6]]

ROC_logistic(X_PC_scores_selected,y)
