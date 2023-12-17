# Load necessary libraries
library(tidyverse)
library(caret)
library(rpart)
library(ROCR)

# Set seed for reproducibility
set.seed(123)

# Load the dataset
bankloans <- read.csv("C:/Users/Giorgos/Desktop/ergasies_metaptxiakwn/ergasies_sgourou/Data/bankloans.csv")

# Display the first few rows of the dataset
head(bankloans)

# Check data types and missing values
str(bankloans)
summary(bankloans)
any(is.na(bankloans))

# Segregating numeric and categorical variables
numeric_var_names <- names(bankloans)[sapply(bankloans, is.numeric)]
categorical_var_names <- names(bankloans)[sapply(bankloans, is.factor)]

# Display numeric variable names
numeric_var_names

# Splitting the dataset into existing and new customers
bankloans_existing <- bankloans[!is.na(bankloans$default), ]
bankloans_new <- bankloans[is.na(bankloans$default), ]

# Descriptive statistics for existing customers
summary(bankloans_existing)

# Box plots for numeric variables
boxplot(bankloans_existing$age, main="Box-Plot of age")
boxplot(bankloans_existing$employ, main="Box-Plot of employee tenure")
boxplot(bankloans_existing$income, main="Box-Plot of employee income")
boxplot(bankloans_existing$debtinc, main="Box-Plot of employee debt to income ratio")
boxplot(bankloans_existing$creddebt, main="Box-Plot of Credit to debit ratio")

# Identify and treat outliers
outlier_capping <- function(x) {
  upper_limit <- quantile(x, 0.95)
  x <- pmin(x, upper_limit)
  return(x)
}

bankloans_existing <- as.data.frame(lapply(bankloans_existing, outlier_capping))

# Correlation matrix
cor_matrix <- cor(bankloans_existing)

# Visualize the correlation using a heatmap
heatmap(cor_matrix, annot = TRUE, fmt = "0.2f", col = heat.colors(10))

# Data dimensions
dim(bankloans_existing)
dim(bankloans_new)

# Distribution of default variable
table(bankloans_existing$default)
barplot(table(bankloans_existing$default), xlab="default", ylab="count", main="Distribution of default")

# Percentage of unique types in the indicator variable
round(prop.table(table(bankloans_existing$default)) * 100, 3)

# Bivariate analysis - Numeric (T-Test)
tstats_df <- data.frame()

for (eachvariable in numeric_var_names) {
  tstats <- t.test(bankloans_existing$age[bankloans_existing$default == 1], 
                   bankloans_existing$age[bankloans_existing$default == 0], 
                   var.equal = FALSE)
  temp <- data.frame(Variable_Name = eachvariable, 
                     T_Statistic = tstats$statistic, 
                     P_Value = tstats$p.value)
  tstats_df <- rbind(tstats_df, temp)
}

# Sort results by P-Value
tstats_df <- tstats_df[order(tstats_df$P_Value), ]

# Display t-stats results
tstats_df

# Bivariate Analysis - Visualization
bivariate_analysis_plot <- function(segment_by) {
  boxplot(bankloans_existing[, segment_by] ~ bankloans_existing$default, 
          main = paste("Box plot of", segment_by))
}

bivariate_analysis_plot("age")
bivariate_analysis_plot("ed")
bivariate_analysis_plot("employ")
bivariate_analysis_plot("address")
bivariate_analysis_plot("income")
bivariate_analysis_plot("debtinc")
bivariate_analysis_plot("creddebt")
bivariate_analysis_plot("othdebt")

# Multicollinearity Check
features <- paste(names(bankloans_existing)[!names(bankloans_existing) %in% c("default")], collapse = " + ")

# Perform VIF
vif_df <- data.frame()
for (i in 1:(length(names(bankloans_existing))-1)) {
  vif_value <- car::vif(lm(paste("default ~ ", features), data = bankloans_existing))
  temp <- data.frame(VIF_Factor = vif_value[i], Features = names(bankloans_existing)[i])
  vif_df <- rbind(vif_df, temp)
}

# Display VIF results
vif_df

# Model Building and Diagnostics
# Logistic Regression
# Split data into train and test sets
set.seed(123)
train_index <- createDataPartition(bankloans_existing$default, p = 0.8, list = FALSE)
train_data <- bankloans_existing[train_index, ]
test_data <- bankloans_existing[-train_index, ]

# Model Building
logreg_model <- glm(default ~ ., data = train_data, family = binomial)

# Display coefficients
summary(logreg_model)

# Model Performance on Test Data
test_data$predicted_probs <- predict(logreg_model, newdata = test_data, type = "response")

# Create confusion matrix
conf_matrix <- table(test_data$default, ifelse(test_data$predicted_probs > 0.224, 1, 0))

# Display confusion matrix
conf_matrix

# Calculate precision score
precision_score <- conf_matrix[2, 2] / sum(conf_matrix[, 2])
cat("Precision Score:", round(precision_score, 3), "\n")

# Calculate overall accuracy
accuracy <- sum(diag(conf_matrix)) / sum(conf_matrix)
cat("Overall Accuracy:", round(accuracy, 3), "\n")

# Classification report
cat("Classification Report:\n")
cat(classSummary(test_data$default, as.factor(ifelse(test_data$predicted_probs > 0.224, 1, 0))))

# Save the Logistic Regression Model
saveRDS(logreg_model, file = "final_model_logreg.rds")

# Decision Tree Classifier
# Model Building
dt_model <- rpart(default ~ ., data = train_data, method = "class")

# Predictions on Test Data
test_data$predicted_probs_dt <- predict(dt_model, newdata = test_data, type = "prob")[, 2]

# Create confusion matrix for Decision Tree
conf_matrix_dt <- table(test_data$default, ifelse(test_data$predicted_probs_dt > 0.224, 1, 0))

# Display confusion matrix for Decision Tree
conf_matrix_dt

# Calculate precision score for Decision Tree
precision_score_dt <- conf_matrix_dt[2, 2] / sum(conf_matrix_dt[, 2])
cat("Precision Score (Decision Tree):", round(precision_score_dt, 3), "\n")

# Calculate overall accuracy for Decision Tree
accuracy_dt <- sum(diag(conf_matrix_dt)) / sum(conf_matrix_dt)
cat("Overall Accuracy (Decision Tree):", round(accuracy_dt, 3), "\n")

# Classification report for Decision Tree
cat("Classification Report (Decision Tree):\n")
cat(classSummary(test_data$default, as.factor(ifelse(test_data$predicted_probs_dt > 0.224, 1, 0))))

# Save the Decision Tree Model
saveRDS(dt_model, file = "final_model_decisiontree.rds")

