// frontend/src/hooks/useMaritimeData.js
/**
 * Hook for real maritime data integration
 * Fetches live ship positions and route data
 */
import { useState, useEffect } from 'react';

export const useMaritimeData = () => {
    const [maritimeData, setMaritimeData] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        const fetchMaritimeData = async () => {
            try {
                const response = await fetch('/api/maritime/live-data');
                const result = await response.json();
                
                if (result.success) {
                    setMaritimeData(result.data);
                }
            } catch (error) {
                console.error('Maritime data fetch error:', error);
            } finally {
                setLoading(false);
            }
        };
        
        fetchMaritimeData();
        const interval = setInterval(fetchMaritimeData, 30000); // 30 seconds
        
        return () => clearInterval(interval);
    }, []);
    
    return { maritimeData, loading };
};