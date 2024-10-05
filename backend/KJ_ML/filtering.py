from flask import Flask, request, jsonify
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
app = Flask(__name__)

# Load datasets
students_df = pd.read_csv("datasets/student_data.csv")
courses_df = pd.read_csv("datasets/courses.csv")

# Create 'Profile' column for students
students_df['Profile'] = (
    students_df['Interested Domain'] + " " +
    students_df['Projects'] + " " +
    students_df['Future Career'] + " " +
    students_df['experience'].astype(str) + " " +
    students_df['certifications'].astype(str) + " " +
    students_df['technicalSkills'].astype(str)
)

students_df.drop(columns=["Python", "SQL", "Java"], axis=1, inplace=True)

# Create 'course_info' column for courses
courses_df["course_info"] = (
    courses_df['Name'] + " " +
    courses_df['about'] + " " +
    courses_df['course_description'].fillna('')
)

# Vectorize both student profiles and courses
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
combined_data = pd.concat([students_df['Profile'], courses_df['course_info']], ignore_index=True)
combined_data = combined_data.fillna("")
tfidf_vectorizer.fit(combined_data)

student_profiles_tfidf = tfidf_vectorizer.transform(students_df['Profile'])
courses_df = courses_df.fillna("")
courses_tfidf = tfidf_vectorizer.transform(courses_df['course_info'])

# Cosine similarity between student profiles and courses
similarity_matrix = cosine_similarity(student_profiles_tfidf, courses_tfidf)

# Recommend courses based on the profile text (not student ID)
def recommend_courses_by_profile(user_profile, top_n=3):
    # Transform the input profile into TF-IDF
    user_profile_tfidf = tfidf_vectorizer.transform([user_profile])
    
    # Compute similarity between the input profile and all courses
    similarity_scores = cosine_similarity(user_profile_tfidf, courses_tfidf).flatten()
    
    # Get top course recommendations based on similarity scores
    top_courses_idx = similarity_scores.argsort()[-top_n:][::-1]  # Sort in descending order
    top_course_ids = courses_df.iloc[top_courses_idx]['course_id'].tolist()
    return top_course_ids

# Flask endpoint for recommendations
@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    user_profile = data.get('profile')
    
    if not user_profile:
        return jsonify({"error": "Profile data is required"}), 400
    
    recommended_courses = recommend_courses_by_profile(user_profile)
    
    return jsonify({"recommended_courses": recommended_courses}), 200

# Load ratings matrix with course IDs as columns
ratings_df = pd.read_csv("datasets/ratings_matrix.csv")

# Load courses and create a mapping of course names to IDs
courses_df = pd.read_csv("datasets/courses.csv")  # Make sure this path is correct
course_id_mapping = pd.Series(courses_df['course_id'].values, index=courses_df['Name']).to_dict()
def get_jaccard_similarity(ratings_df):
    num_students = len(ratings_df)
    similarity_matrix = pd.DataFrame(index=ratings_df['Student ID'], columns=ratings_df['Student ID'])

    for i in range(num_students):
        set_i = set(ratings_df.columns[1:][ratings_df.iloc[i, 1:] > 0])
        for j in range(num_students):
            set_j = set(ratings_df.columns[1:][ratings_df.iloc[j, 1:] > 0])
            similarity = jaccard_similarity(set_i, set_j)
            similarity_matrix.iloc[i, j] = similarity

    similarity_matrix = similarity_matrix.astype(float)
    return similarity_matrix
# Jaccard similarity function
def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0

# Recommend courses for a new user based on similar users
def recommend_courses_for_new_user(new_user_profile, ratings_df, num_recommendations=3, top_similar=10):
    # Create a new similarity matrix including the new user profile
    similarity_matrix = get_jaccard_similarity(ratings_df)

    # Convert new user profile to a set (e.g., their rated courses)
    new_user_courses = set(new_user_profile)
    
    # Find similarity of new user with all other students
    similarities = []
    for i in range(len(ratings_df)):
        student_courses = set(ratings_df.columns[1:][ratings_df.iloc[i, 1:] > 0])
        similarity = jaccard_similarity(new_user_courses, student_courses)
        similarities.append((ratings_df.iloc[i]['Student ID'], similarity))
    
    # Sort students by similarity to the new user
    sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
    similar_students = [student for student, _ in sorted_similarities[:top_similar]]
    
    # Find courses that similar students have rated highly but the new user hasn't rated yet
    new_user_course_set = set(new_user_profile)
    recommended_courses = []
    
    for student_id in similar_students:
        student_ratings = ratings_df.loc[ratings_df['Student ID'] == student_id].iloc[:, 1:]
        student_courses = set(student_ratings.columns[student_ratings.values[0] > 0].tolist())
        
        # Get courses rated by similar students but not yet by the new user
        recommendations = student_courses - new_user_course_set
        recommended_courses.extend(recommendations)
        
        if len(recommended_courses) >= num_recommendations:
            break
    
    # Return the course IDs as recommendations
    # Map course names to their IDs
    recommended_course_ids = [course_id_mapping[course] for course in recommended_courses if course in course_id_mapping]
    
    return recommended_course_ids[:num_recommendations]

# Flask endpoint for recommendations
@app.route('/jaccard-recommend', methods=['POST'])
def jaccard_recommend():
    data = request.json
    new_user_profile = data.get('profile')

    if not new_user_profile:
        return jsonify({"error": "Profile data is required"}), 400

    recommended_courses = recommend_courses_for_new_user(new_user_profile, ratings_df)

    return jsonify({"recommended_course_ids": recommended_courses}), 200


@app.route('/search-events', methods=['GET'])
def search_events():
    # Extract query parameters from the request
    query = request.args.get('query', 'Hackathon')  # Default query: 'Hackathon'
    date = request.args.get('date', 'any')          # Default date: 'any'
    is_virtual = request.args.get('is_virtual', 'false')  # Default: 'false'
    start = request.args.get('start', '0')          # Default start index: 0

    # API URL and headers
    url = "https://real-time-events-search.p.rapidapi.com/search-events"
    headers = {
        "x-rapidapi-key": "31f9f38f67msh61dc71a007fa815p1d2c63jsnf6de091561b4",
        "x-rapidapi-host": "real-time-events-search.p.rapidapi.com"
    }
    
    # Request parameters
    querystring = {
        "query": query,
        "date": date,
        "is_virtual": is_virtual,
        "start": start
    }
    
    # Send the GET request to the external API
    response = requests.get(url, headers=headers, params=querystring)

    # Check if the request was successful
    if response.status_code == 200:
        events = response.json().get('data', [])
        event_list = []

        # Loop through each event and extract the required fields
        for event in events:
            event_info = {
                'event_name': event.get('name', 'N/A'),
                'link': event.get('link', 'N/A'),
                'venue': event.get('venue', {}).get('google_location', 'N/A'),
                'publisher': event.get('publisher', 'N/A'),
                'info_links': event.get('info_links', [{'link': 'N/A'}])[0].get('link', 'N/A'),
                'start_time': event.get('start_time', 'N/A'),
                'end_time': event.get('end_time', 'N/A'),
                'description': event.get('description', 'N/A')
            }
            event_list.append(event_info)

        # Return the event list as JSON response
        return jsonify(event_list)

    else:
        return jsonify({"error": f"Failed to fetch data. Status code: {response.status_code}"}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
