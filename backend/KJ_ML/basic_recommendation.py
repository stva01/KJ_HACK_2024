import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load Datasets
students_df = pd.read_csv("datasets\\cs_students.csv")
courses_df = pd.read_csv("datasets\\EdX.csv")

skill_mapping = {
    'strong': 3,
    'average': 2,
    'weak': 1
}

# Convert categorical skill levels to numerical values
students_df['Python'] = students_df['Python'].map(skill_mapping)
students_df['SQL'] = students_df['SQL'].map(skill_mapping)
students_df['Java'] = students_df['Java'].map(skill_mapping)
students_df['Profile'] = (
    students_df['Interested Domain'] + " " +
    students_df['Future Career'] + " " +
    students_df['Python'].astype(str) + " " +
    students_df['SQL'].astype(str) + " " +
    students_df['Java'].astype(str)
)

courses_df['Description'] = courses_df['Course Description']

# Step 3: Text Vectorization (TF-IDF)
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
combined_data = pd.concat([students_df['Profile'], courses_df['Description']], ignore_index=True)
tfidf_vectorizer.fit(combined_data)
# Fit the vectorizer on both student profiles and course descriptions
student_profiles_tfidf = tfidf_vectorizer.fit_transform(students_df['Profile'])
courses_tfidf = tfidf_vectorizer.fit_transform(courses_df['Description'])

# Step 4: Compute Similarity (Cosine Similarity)
similarity_matrix = cosine_similarity(student_profiles_tfidf, courses_tfidf)

# Step 5: Recommend Courses
def recommend_courses(student_id, similarity_matrix, students_df, courses_df, top_n=3):
    student_idx = students_df[students_df['Student ID'] == student_id].index[0]
    similarity_scores = list(enumerate(similarity_matrix[student_idx]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    top_courses_idx = [x[0] for x in similarity_scores[:top_n]]
    return courses_df.iloc[top_courses_idx]

# Example: Recommend courses for Student with ID 1
recommended_courses = recommend_courses(1, similarity_matrix, students_df, courses_df)
print(recommended_courses[['Name', 'Description']])
