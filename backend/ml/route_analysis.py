# backend/ml/route_analysis.py
"""
Statistical analysis and ML models for maritime routes
"""

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
import geopandas as gpd
from scipy import stats

class MaritimeRouteAnalyzer:
    def __init__(self, routes_data):
        self.df = pd.DataFrame(routes_data)
        
    def calculate_route_statistics(self):
        """Calculate descriptive statistics for routes"""
        stats = {
            'total_routes': len(self.df),
            'avg_distance_nm': self.df['total_distance_nm'].mean(),
            'std_distance': self.df['total_distance_nm'].std(),
            'median_waypoints': self.df['waypoint_count'].median(),
            'distance_skewness': stats.skew(self.df['total_distance_nm'].dropna()),
            'distance_kurtosis': stats.kurtosis(self.df['total_distance_nm'].dropna())
        }
        return stats
    
    def identify_outlier_routes(self):
        """Use Isolation Forest to identify anomalous routes"""
        features = self.df[['total_distance_nm', 'waypoint_count']].fillna(0)
        
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        predictions = iso_forest.fit_predict(features)
        
        self.df['is_outlier'] = predictions == -1
        return self.df[self.df['is_outlier']]
    
    def cluster_routes_by_pattern(self):
        """Cluster routes based on geographic patterns"""
        # Extract waypoint features
        waypoint_features = []
        for idx, route in self.df.iterrows():
            if route['waypoints']:
                # Extract start, mid, end points
                waypoints = route['waypoints']
                if len(waypoints) >= 3:
                    features = [
                        waypoints[0]['lat'], waypoints[0]['lon'],
                        waypoints[len(waypoints)//2]['lat'], 
                        waypoints[len(waypoints)//2]['lon'],
                        waypoints[-1]['lat'], waypoints[-1]['lon']
                    ]
                    waypoint_features.append(features)
        
        # Apply DBSCAN clustering
        if waypoint_features:
            clustering = DBSCAN(eps=1.0, min_samples=2)
            clusters = clustering.fit_predict(waypoint_features)
            return clusters
        
        return None
    
    def predict_route_duration(self):
        """Build regression model to predict route duration"""
        from sklearn.linear_model import LinearRegression
        from sklearn.model_selection import train_test_split
        
        # Prepare features
        X = self.df[['total_distance_nm', 'waypoint_count']].fillna(0)
        # Assume average speed of 15 knots
        y = self.df['total_distance_nm'] / 15  # Hours
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        score = model.score(X_test, y_test)
        return {
            'model': 'LinearRegression',
            'r2_score': score,
            'coefficients': model.coef_.tolist(),
            'intercept': model.intercept_
        }