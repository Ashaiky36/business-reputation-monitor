import pandas as pd

# Read the original CSV
df = pd.read_csv('reviews.csv')

# Combine title and content for full review text
df['full_review'] = df['title'].fillna('') + ' ' + df['content'].fillna('')

# Extract just the full review text
content_df = df[['full_review']]

# Rename column for clarity
content_df.columns = ['review_content']

# Save to new CSV
content_df.to_csv('review_content.csv', index=False)

print(f"✅ Extracted {len(content_df)} reviews to 'review_content.csv'")
print(f"📊 Preview of first 3 rows:")
print(content_df.head(3))