"""
Empirical Data Visualization Service
Creates visualizations from real Norwegian maritime data
All visualizations are data-driven from actual observations
"""

import logging
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class EmpiricalVisualizer:
    """
    Creates visualizations from empirical maritime data.
    Every chart is based on real data from verified sources.
    """
    
    def __init__(self, color_scheme: str = 'plotly'):
        """Initialize with visualization preferences."""
        self.color_scheme = color_scheme
        logger.info("🎨 Empirical Visualizer initialized - Real Data Visualization")
    
    def create_traffic_density_map(self, vessels: List, city_name: str) -> Dict[str, Any]:
        """
        Create heatmap of vessel density from real AIS data.
        
        Args:
            vessels: List of EmpiricalVessel objects
            city_name: Norwegian city for context
            
        Returns:
            Plotly figure as dictionary
        """
        if not vessels:
            return self._create_empty_visualization("No empirical data available")
        
        # Extract coordinates from real data
        lats = [v.latitude for v in vessels]
        lons = [v.longitude for v in vessels]
        
        # Create empirical heatmap
        fig = go.Figure()
        
        # Add density heatmap
        fig.add_trace(go.Densitymapbox(
            lat=lats,
            lon=lons,
            radius=10,
            colorscale='Viridis',
            showscale=True,
            opacity=0.6
        ))
        
        # Add individual vessel points
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=dict(size=8, color='red'),
            text=[f"{v.name}<br>Speed: {v.speed_knots} kn" for v in vessels],
            hoverinfo='text',
            name='Vessels'
        ))
        
        # Configure map
        center_lat = np.mean(lats) if lats else 60.0
        center_lon = np.mean(lons) if lons else 5.0
        
        fig.update_layout(
            title=f"Empirical Vessel Density - {city_name}",
            mapbox=dict(
                style="carto-positron",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=10
            ),
            showlegend=True,
            height=600,
            annotations=[{
                'text': f'Data: Kystdatahuset API | Vessels: {len(vessels)}',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0,
                'y': 0,
                'bgcolor': 'white',
                'opacity': 0.8
            }]
        )
        
        return fig.to_dict()
    
    def create_vessel_type_chart(self, vessels: List) -> Dict[str, Any]:
        """
        Create bar chart of vessel type distribution from real data.
        """
        if not vessels:
            return self._create_empty_visualization("No vessel data")
        
        # Count vessel types from empirical data
        type_counts = {}
        for vessel in vessels:
            v_type = vessel.vessel_type
            type_counts[v_type] = type_counts.get(v_type, 0) + 1
        
        # Create DataFrame for plotting
        df = pd.DataFrame({
            'Vessel Type': list(type_counts.keys()),
            'Count': list(type_counts.values())
        }).sort_values('Count', ascending=False)
        
        # Create empirical bar chart
        fig = px.bar(
            df,
            x='Vessel Type',
            y='Count',
            title='Empirical Vessel Type Distribution',
            color='Count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title="Vessel Type",
            yaxis_title="Number of Vessels",
            showlegend=False,
            annotations=[{
                'text': f'Total Vessels: {len(vessels)} | Data: Real-time AIS',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0,
                'y': -0.1
            }]
        )
        
        return fig.to_dict()
    
    def create_speed_distribution_chart(self, vessels: List) -> Dict[str, Any]:
        """
        Create histogram of vessel speeds from real data.
        """
        if not vessels:
            return self._create_empty_visualization("No speed data")
        
        # Extract speeds from empirical data
        speeds = [v.speed_knots for v in vessels if hasattr(v, 'speed_knots')]
        
        if not speeds:
            return self._create_empty_visualization("No speed measurements")
        
        # Create empirical histogram
        fig = px.histogram(
            x=speeds,
            nbins=20,
            title='Empirical Vessel Speed Distribution',
            labels={'x': 'Speed (knots)', 'y': 'Number of Vessels'}
        )
        
        # Add statistical annotations
        mean_speed = np.mean(speeds)
        median_speed = np.median(speeds)
        
        fig.update_layout(
            annotations=[
                {
                    'text': f'Mean: {mean_speed:.1f} knots<br>Median: {median_speed:.1f} knots',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.95,
                    'y': 0.95,
                    'bgcolor': 'white',
                    'opacity': 0.8
                },
                {
                    'text': f'Data: {len(speeds)} empirical measurements',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0,
                    'y': -0.1
                }
            ]
        )
        
        return fig.to_dict()
    
    def create_city_comparison_chart(self, comparison_data: Dict) -> Dict[str, Any]:
        """
        Create comparison chart between two cities from empirical data.
        """
        if 'empirical_metrics' not in comparison_data:
            return self._create_empty_visualization("Invalid comparison data")
        
        metrics = comparison_data['empirical_metrics']
        cities = comparison_data.get('cities', ['City A', 'City B'])
        
        # Prepare data for grouped bar chart
        chart_data = []
        
        # Vessel counts
        counts = metrics.get('vessel_count', {})
        for city in cities:
            if city in counts and isinstance(counts[city], (int, float)):
                chart_data.append({
                    'City': city,
                    'Metric': 'Vessel Count',
                    'Value': float(counts[city])
                })
        
        # Average speeds
        speeds = metrics.get('average_speed', {})
        for city in cities:
            if city in speeds and isinstance(speeds[city], (int, float)):
                chart_data.append({
                    'City': city,
                    'Metric': 'Average Speed (knots)',
                    'Value': float(speeds[city])
                })
        
        if not chart_data:
            return self._create_empty_visualization("No comparable metrics")
        
        df = pd.DataFrame(chart_data)
        
        # Create grouped bar chart
        fig = px.bar(
            df,
            x='Metric',
            y='Value',
            color='City',
            barmode='group',
            title='Empirical City Comparison',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig.update_layout(
            xaxis_title="Metric",
            yaxis_title="Value",
            annotations=[{
                'text': f'Data: Real-time AIS comparison | {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0,
                'y': -0.15
            }]
        )
        
        return fig.to_dict()
    
    def _create_empty_visualization(self, message: str) -> Dict[str, Any]:
        """Create placeholder visualization when no data is available."""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        
        fig.update_layout(
            title="No Empirical Data Available",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        return fig.to_dict()


# Global visualizer instance
empirical_visualizer = EmpiricalVisualizer()