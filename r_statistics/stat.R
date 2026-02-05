# Load the data
# Use relative path from the repo root: run this script with the working directory set to the repo root
final_raw_with_ids <- read.csv("schema/final_raw_with_ids.csv")

# Independent variable
final_raw_with_ids$room_type <- as.factor(final_raw_with_ids$room_type)

names(final_raw_with_ids)

# اختار نسخة الأعمدة (x أو y)
price_col <- "realSum_x"
sat_col   <- "guest_satisfaction_overall_x"
clean_col <- "cleanliness_rating_x"
group_col <- "room_type"

# تأكد الأعمدة موجودة
stopifnot(price_col %in% names(final_raw_with_ids),
          sat_col   %in% names(final_raw_with_ids),
          clean_col %in% names(final_raw_with_ids),
          group_col %in% names(final_raw_with_ids))

# types
final_raw_with_ids[[group_col]] <- as.factor(final_raw_with_ids[[group_col]])

final_raw_with_ids[[price_col]] <- as.numeric(final_raw_with_ids[[price_col]])
final_raw_with_ids[[sat_col]]   <- as.numeric(final_raw_with_ids[[sat_col]])
final_raw_with_ids[[clean_col]] <- as.numeric(final_raw_with_ids[[clean_col]])

# dataset for analysis
df_clean <- na.omit(final_raw_with_ids[, c(price_col, sat_col, clean_col, group_col)])

# check
dim(df_clean)
summary(df_clean[[group_col]])







anova_model <- aov(df_clean[[price_col]] ~ df_clean[[group_col]])
summary(anova_model)
TukeyHSD(anova_model)









manova_model <- manova(
  cbind(df_clean[[price_col]],
        df_clean[[sat_col]],
        df_clean[[clean_col]]) ~ df_clean[[group_col]]
)

summary(manova_model, test = "Wilks")
summary.aov(manova_model)


summary(final_raw_with_ids$realSum_x)
summary(final_raw_with_ids$realSum_y)










boxplot(
  df_clean[[price_col]] ~ df_clean[[group_col]],
  col = c("#FF5A5F", "#FBB6B8", "#C81E1E"),
  main = "Price by Room Type (ANOVA)",
  xlab = "Room Type",
  ylab = "Price",
  border = "#111111"
)




#ANOVAA (Error Bar)

library(dplyr)

means_df <- df_clean %>%
  group_by(df_clean[[group_col]]) %>%
  summarise(
    mean_price = mean(df_clean[[price_col]]),
    sd_price   = sd(df_clean[[price_col]]),
    n = n()
  )

means_df$se <- means_df$sd_price / sqrt(means_df$n)

plot(
  means_df$mean_price,
  xaxt = "n",
  pch = 19,
  col = "#FF5A5F",
  ylim = c(min(means_df$mean_price - means_df$se),
           max(means_df$mean_price + means_df$se)),
  main = "Mean Price by Room Type",
  ylab = "Mean Price"
)

axis(1, at = 1:nrow(means_df), labels = means_df$`df_clean[[group_col]]`)
arrows(
  1:nrow(means_df),
  means_df$mean_price - means_df$se,
  1:nrow(means_df),
  means_df$mean_price + means_df$se,
  angle = 90, code = 3, length = 0.08
)

##################################################MANOVA#####################################################################


pairs(
  df_clean[, c(price_col, sat_col, clean_col)],
  col = as.numeric(df_clean[[group_col]]),
  pch = 19,
  main = "MANOVA: Dependent Variables Relationship"
)








#3 BOX BLOT

par(mfrow = c(1, 3))

boxplot(df_clean[[price_col]] ~ df_clean[[group_col]],
        main = "Price",
        col = "#FF5A5F")

boxplot(df_clean[[sat_col]] ~ df_clean[[group_col]],
        main = "Satisfaction",
        col = "#FBB6B8")

boxplot(df_clean[[clean_col]] ~ df_clean[[group_col]],
        main = "Cleanliness",
        col = "#C81E1E")

par(mfrow = c(1, 1))










#3 BARS 


manova_means <- df_clean %>%
  group_by(df_clean[[group_col]]) %>%
  summarise(
    Price = mean(df_clean[[price_col]]),
    Satisfaction = mean(df_clean[[sat_col]]),
    Cleanliness = mean(df_clean[[clean_col]])
  )

barplot(
  t(as.matrix(manova_means[, -1])),
  beside = TRUE,
  col = c("#FF5A5F", "#FBB6B8", "#C81E1E"),
  names.arg = manova_means$`df_clean[[group_col]]`,
  main = "MANOVA: Mean Comparison"
)

legend("topright",
       legend = colnames(manova_means[, -1]),
       fill = c("#FF5A5F", "#FBB6B8", "#C81E1E"))



