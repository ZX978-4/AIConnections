import pandas as pd

#筛选有base_model的

# 读取模型数据
df = pd.read_csv("data/models.csv", encoding="utf-8-sig")

# 筛选条件：base_model不是"无"、"获取失败"、空值
filter_condition = ~df["base_model"].isin(["无", "获取失败"]) & df["base_model"].notna()
filtered_df = df[filter_condition]

# 保存筛选结果
filtered_df.to_csv("data/models_with_basemodel.csv", index=False, encoding="utf-8-sig")
print(f"筛选出 {len(filtered_df)} 条有base_model的模型记录")



# 还要将对应的父模型也添加
# 用于模型调用图谱的构建