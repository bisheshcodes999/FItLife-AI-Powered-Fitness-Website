import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
import os
from django.conf import settings
from .models import CustomUser, WorkoutPlan
import random
from typing import List, Dict, Any, Tuple


class WorkoutRecommendationEngine:

    
    def __init__(self):
        self.exercise_data = None
        self.tfidf_vectorizer = None
        self.similarity_matrix = None
        self.label_encoders = {}
        self.load_data()
  
    def load_data(self):
        """Load and preprocess the exercise dataset"""
        try:
            csv_file_path = os.path.join(settings.BASE_DIR, 'data', 'megaGymDataset.csv')
            self.exercise_data = pd.read_csv(csv_file_path)
            
            # Clean and preprocess data
            self.exercise_data['Title'] = self.exercise_data['Title'].fillna('')
            self.exercise_data['Desc'] = self.exercise_data['Desc'].fillna('')
            self.exercise_data['BodyPart'] = self.exercise_data['BodyPart'].fillna('General')
            self.exercise_data['Equipment'] = self.exercise_data['Equipment'].fillna('Bodyweight')
            self.exercise_data['Level'] = self.exercise_data['Level'].fillna('Beginner')
            self.exercise_data['Rating'] = pd.to_numeric(self.exercise_data['Rating'], errors='coerce').fillna(0.0)
            
            # Create combined features for similarity analysis
            self.exercise_data['combined_features'] = (
                self.exercise_data['Title'] + ' ' +
                self.exercise_data['Desc'] + ' ' +
                self.exercise_data['BodyPart'] + ' ' +
                self.exercise_data['Equipment'] + ' ' +
                self.exercise_data['Level']
            )
            
            # Initialize TF-IDF vectorizer for text similarity
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2)
            )
            
            # Fit and transform the combined features
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.exercise_data['combined_features'])
            self.similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Encode categorical variables
            for column in ['BodyPart', 'Equipment', 'Level', 'Type']:
                if column in self.exercise_data.columns:
                    le = LabelEncoder()
                    self.exercise_data[f'{column}_encoded'] = le.fit_transform(self.exercise_data[column])
                    self.label_encoders[column] = le
                    
        except Exception as e:
            print(f"Error loading exercise data: {e}")
            self.exercise_data = pd.DataFrame()
    
    def get_user_preference_score(self, user: CustomUser, exercise_row: pd.Series) -> float:
        """
        Calculate a preference score for an exercise based on user profile
        """
        score = 0.0
        
        # Experience level matching (30% weight)
        if user.experience_level and exercise_row['Level']:
            if user.experience_level.lower() == exercise_row['Level'].lower():
                score += 30
            elif (user.experience_level.lower() == 'beginner' and 
                  exercise_row['Level'].lower() in ['beginner', 'intermediate']):
                score += 20
            elif (user.experience_level.lower() == 'advanced' and 
                  exercise_row['Level'].lower() in ['intermediate', 'advanced']):
                score += 25
        
        # Fitness goal matching (40% weight)
        if user.fitness_goal and exercise_row['Desc']:
            goal_keywords = {
                'weight_loss': ['cardio', 'burn', 'fat', 'metabolic', 'hiit', 'conditioning'],
                'muscle_gain': ['strength', 'muscle', 'build', 'mass', 'hypertrophy', 'power'],
                'endurance': ['endurance', 'cardio', 'stamina', 'aerobic', 'conditioning'],
                'flexibility': ['stretch', 'flexibility', 'mobility', 'range', 'movement'],
                'general_health': ['functional', 'movement', 'core', 'stability', 'balance']
            }
            
            if user.fitness_goal in goal_keywords:
                keywords = goal_keywords[user.fitness_goal]
                desc_lower = exercise_row['Desc'].lower()
                title_lower = exercise_row['Title'].lower()
                
                for keyword in keywords:
                    if keyword in desc_lower or keyword in title_lower:
                        score += 8  # 40/5 keywords max
        
        # Rating bonus (20% weight)
        if exercise_row['Rating'] > 0:
            score += (exercise_row['Rating'] / 10.0) * 20
        
        # Body part preference (10% weight)
        if user.fitness_goal == 'muscle_gain':
            strength_parts = ['chest', 'back', 'shoulders', 'legs', 'arms']
            if any(part in exercise_row['BodyPart'].lower() for part in strength_parts):
                score += 10
        elif user.fitness_goal == 'weight_loss':
            cardio_parts = ['abdominals', 'full body', 'legs']
            if any(part in exercise_row['BodyPart'].lower() for part in cardio_parts):
                score += 10
        
        return score
    
    def get_personalized_recommendations(self, user: CustomUser, num_recommendations: int = 6) -> List[Dict]:
        """
        Get personalized exercise recommendations for a user
        """
        if self.exercise_data.empty:
            return []
        
        recommendations = []
        
        # Calculate preference scores for all exercises
        scores = []
        for idx, row in self.exercise_data.iterrows():
            score = self.get_user_preference_score(user, row)
            scores.append((idx, score, row))
        
        # Sort by score and get top recommendations
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Add some randomization to avoid always showing the same exercises
        top_candidates = scores[:num_recommendations * 3]  # Get 3x more candidates
        selected_indices = random.sample(range(len(top_candidates)), 
                                       min(num_recommendations, len(top_candidates)))
        
        for i in selected_indices:
            idx, score, row = top_candidates[i]
            recommendations.append({
                'id': idx,
                'title': row['Title'],
                'description': row['Desc'],
                'body_part': row['BodyPart'],
                'equipment': row['Equipment'],
                'level': row['Level'],
                'type': row['Type'],
                'rating': float(row['Rating']) if row['Rating'] else 0.0,
                'rating_desc': row['RatingDesc'],
                'preference_score': score,
                'match_reasons': self._get_match_reasons(user, row, score)
            })
        
        return recommendations
    
    def _get_match_reasons(self, user: CustomUser, exercise_row: pd.Series, score: float) -> List[str]:
        """
        Generate human-readable reasons why this exercise was recommended
        """
        reasons = []
        
        if user.experience_level and exercise_row['Level']:
            if user.experience_level.lower() == exercise_row['Level'].lower():
                reasons.append(f"Perfect match for your {user.experience_level} level")
            elif score > 60:
                reasons.append(f"Suitable for your {user.experience_level} level")
        
        if user.fitness_goal:
            goal_display = dict(CustomUser.FITNESS_GOAL_CHOICES).get(user.fitness_goal, user.fitness_goal)
            reasons.append(f"Aligned with your {goal_display} goal")
        
        if exercise_row['Rating'] > 8.0:
            reasons.append("Highly rated exercise")
        elif exercise_row['Rating'] > 6.0:
            reasons.append("Well-rated exercise")
        
        if exercise_row['Equipment'] == 'Bodyweight':
            reasons.append("No equipment needed")
        
        return reasons[:3]  # Limit to 3 reasons
    
    def get_similar_exercises(self, exercise_id: int, num_similar: int = 5) -> List[Dict]:
        """
        Get exercises similar to a given exercise using content-based filtering
        """
        if self.exercise_data.empty or exercise_id >= len(self.exercise_data):
            return []
        
        # Get similarity scores for the given exercise
        sim_scores = list(enumerate(self.similarity_matrix[exercise_id]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get indices of most similar exercises (excluding the exercise itself)
        similar_indices = [i[0] for i in sim_scores[1:num_similar+1]]
        
        similar_exercises = []
        for idx in similar_indices:
            row = self.exercise_data.iloc[idx]
            similar_exercises.append({
                'id': idx,
                'title': row['Title'],
                'description': row['Desc'],
                'body_part': row['BodyPart'],
                'equipment': row['Equipment'],
                'level': row['Level'],
                'type': row['Type'],
                'rating': float(row['Rating']) if row['Rating'] else 0.0,
                'rating_desc': row['RatingDesc'],
                'similarity_score': sim_scores[idx][1]
            })
        
        return similar_exercises
    
    def _collaborative_scores(self, user: CustomUser) -> Dict[int, float]:
        """
        Collaborative layer: score plans by how often SIMILAR users
        (same fitness goal or experience level) completed them.
        Returns {plan_id: score 0..30}.
        """
        from django.db.models import Count, Q
        from .models import WorkoutHistory

        similar = Q()
        if user.fitness_goal:
            similar |= Q(user__fitness_goal=user.fitness_goal)
        if user.experience_level:
            similar |= Q(user__experience_level=user.experience_level)
        if not similar:
            return {}

        rows = (WorkoutHistory.objects.filter(similar)
                .exclude(user=user)
                .values("workout_plan_id")
                .annotate(completions=Count("id"))
                .order_by("-completions"))
        if not rows:
            return {}
        max_c = rows[0]["completions"]
        # normalize to a 0..30 boost so it can outweigh a single keyword hit
        # but not the whole content score
        return {r["workout_plan_id"]: 30.0 * r["completions"] / max_c
                for r in rows}

    def get_workout_plan_recommendations(self, user: CustomUser, num_plans: int = 4) -> List[WorkoutPlan]:
        """
        HYBRID recommender: content-based scoring (goal keywords, age,
        duration fit) + collaborative scoring (what similar users completed).
        """
        plans = WorkoutPlan.objects.all()

        if not user.fitness_goal and not user.experience_level:
            return list(plans.order_by('-created_at')[:num_plans])

        collab = self._collaborative_scores(user)
        scored_plans = []

        for plan in plans:
            score = collab.get(plan.id, 0)  # collaborative component
            
            # Check if plan description matches user's fitness goal
            if user.fitness_goal:
                goal_keywords = {
                    'weight_loss': ['weight loss', 'fat burn', 'cardio', 'hiit'],
                    'muscle_gain': ['muscle', 'strength', 'build', 'mass'],
                    'endurance': ['endurance', 'cardio', 'stamina'],
                    'flexibility': ['flexibility', 'stretch', 'yoga'],
                    'general_health': ['fitness', 'health', 'wellness']
                }
                
                if user.fitness_goal in goal_keywords:
                    keywords = goal_keywords[user.fitness_goal]
                    plan_text = (plan.title + ' ' + plan.description).lower()
                    
                    for keyword in keywords:
                        if keyword in plan_text:
                            score += 10
            
            # Age matching
            if user.age:
                if plan.recommended_age_min <= user.age <= plan.recommended_age_max:
                    score += 15
            
            # Duration preference (shorter for beginners)
            if user.experience_level == 'beginner' and plan.workout_duration <= 30:
                score += 10
            elif user.experience_level == 'advanced' and plan.workout_duration >= 45:
                score += 10
            
            scored_plans.append((plan, score))
        
        # Sort by score and return top plans
        scored_plans.sort(key=lambda x: x[1], reverse=True)
        return [plan for plan, score in scored_plans[:num_plans]]
    
    def generate_user_questions(self, user: CustomUser) -> List[Dict[str, str]]:
        """
        Generate dynamic questions to better understand user preferences
        """
        questions = []
        
        if not user.fitness_goal:
            questions.append({
                'type': 'fitness_goal',
                'question': 'What is your primary fitness goal?',
                'options': [choice[1] for choice in CustomUser.FITNESS_GOAL_CHOICES]
            })
        
        if not user.experience_level:
            questions.append({
                'type': 'experience_level',
                'question': 'What is your current fitness experience level?',
                'options': [choice[1] for choice in CustomUser.EXPERIENCE_LEVEL_CHOICES]
            })
        
        if not user.workout_frequency:
            questions.append({
                'type': 'workout_frequency',
                'question': 'How many days per week do you prefer to workout?',
                'options': ['1-2 days', '3-4 days', '5-6 days', '7 days']
            })
        
        # Additional preference questions
        questions.extend([
            {
                'type': 'equipment_preference',
                'question': 'What type of equipment do you prefer?',
                'options': ['Bodyweight only', 'Basic equipment (dumbbells, bands)', 
                          'Full gym access', 'No preference']
            },
            {
                'type': 'workout_duration',
                'question': 'How long do you prefer your workouts to be?',
                'options': ['15-30 minutes', '30-45 minutes', '45-60 minutes', '60+ minutes']
            },
            {
                'type': 'body_focus',
                'question': 'Which body areas would you like to focus on most?',
                'options': ['Full body', 'Upper body', 'Lower body', 'Core/Abs', 'Cardio fitness']
            }
        ])
        
        return questions[:4]  # Return max 4 questions to avoid overwhelming


# Global instance
recommendation_engine = WorkoutRecommendationEngine()


def get_user_recommendations(user: CustomUser, num_recommendations: int = 6) -> Dict[str, Any]:
    """
    Main function to get all recommendations for a user
    """
    try:
        exercise_recommendations = recommendation_engine.get_personalized_recommendations(
            user, num_recommendations
        )
        workout_plan_recommendations = recommendation_engine.get_workout_plan_recommendations(
            user, 4
        )
        questions = recommendation_engine.generate_user_questions(user)
        
        return {
            'exercise_recommendations': exercise_recommendations,
            'workout_plan_recommendations': workout_plan_recommendations,
            'questions': questions,
            'user_profile_complete': all([
                user.fitness_goal, user.experience_level, 
                user.age, user.weight, user.height
            ])
        }
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return {
            'exercise_recommendations': [],
            'workout_plan_recommendations': [],
            'questions': [],
            'user_profile_complete': False
        }


def get_exercise_analytics() -> Dict[str, Any]:
    """
    Get analytics about the exercise database
    """
    try:
        df = recommendation_engine.exercise_data
        if df.empty:
            return {}
        
        analytics = {
            'total_exercises': len(df),
            'body_parts': df['BodyPart'].value_counts().to_dict(),
            'equipment_types': df['Equipment'].value_counts().to_dict(),
            'difficulty_levels': df['Level'].value_counts().to_dict(),
            'exercise_types': df['Type'].value_counts().to_dict(),
            'avg_rating': df['Rating'].mean(),
            'top_rated_exercises': df.nlargest(5, 'Rating')[['Title', 'Rating']].to_dict('records')
        }
        
        return analytics
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return {}
