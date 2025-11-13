"""
Statistical Validation Engine for Maritime Fuel Optimization
Empirical validation framework with statistical significance testing
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Container for statistical validation results"""
    is_significant: bool
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float
    sample_size: int
    test_type: str

class StatisticalValidator:
    """
    Empirical validation engine for maritime optimization algorithms
    Provides statistical significance testing and confidence intervals
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.logger = logging.getLogger(__name__)
    
    def ab_test_significance(self, 
                           control_group: List[float],
                           treatment_group: List[float],
                           test_type: str = "t_test") -> ValidationResult:
        """
        Perform A/B test statistical significance analysis
        
        Args:
            control_group: Performance metrics from control group
            treatment_group: Performance metrics from treatment group  
            test_type: Type of statistical test ('t_test', 'mannwhitney')
            
        Returns:
            ValidationResult with statistical significance metrics
        """
        try:
            if len(control_group) < 2 or len(treatment_group) < 2:
                raise ValueError("Insufficient data for statistical testing")
            
            if test_type == "t_test":
                # Independent t-test for normally distributed data
                t_stat, p_value = stats.ttest_ind(treatment_group, control_group)
                effect_size = self._calculate_cohens_d(control_group, treatment_group)
            elif test_type == "mannwhitney":
                # Mann-Whitney U test for non-parametric data
                u_stat, p_value = stats.mannwhitneyu(treatment_group, control_group)
                effect_size = self._calculate_rank_biserial(control_group, treatment_group)
            else:
                raise ValueError(f"Unsupported test type: {test_type}")
            
            # Calculate confidence interval for mean difference
            ci_low, ci_high = self._calculate_confidence_interval(
                control_group, treatment_group
            )
            
            return ValidationResult(
                is_significant=p_value < (1 - self.confidence_level),
                p_value=float(p_value),
                confidence_interval=(float(ci_low), float(ci_high)),
                effect_size=float(effect_size),
                sample_size=len(control_group) + len(treatment_group),
                test_type=test_type
            )
            
        except Exception as e:
            self.logger.error(f"Statistical testing failed: {str(e)}")
            raise
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size for t-test"""
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        mean_diff = np.mean(group2) - np.mean(group1)
        
        return mean_diff / pooled_std if pooled_std != 0 else 0.0
    
    def _calculate_rank_biserial(self, group1: List[float], group2: List[float]) -> float:
        """Calculate rank-biserial correlation for Mann-Whitney test"""
        u_stat, _ = stats.mannwhitneyu(group1, group2)
        n1, n2 = len(group1), len(group2)
        
        return 1 - (2 * u_stat) / (n1 * n2)
    
    def _calculate_confidence_interval(self, 
                                    group1: List[float], 
                                    group2: List[float]) -> Tuple[float, float]:
        """Calculate confidence interval for mean difference"""
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
        n1, n2 = len(group1), len(group2)
        
        # Standard error of the difference
        se_diff = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        
        # t-value for confidence level
        df = n1 + n2 - 2  # degrees of freedom
        t_val = stats.t.ppf((1 + self.confidence_level) / 2, df)
        
        margin_of_error = t_val * se_diff
        mean_diff = mean2 - mean1
        
        return (mean_diff - margin_of_error, mean_diff + margin_of_error)
    
    def validate_optimization_improvement(self,
                                        baseline_performance: List[float],
                                        optimized_performance: List[float],
                                        min_improvement: float = 0.05) -> Dict:
        """
        Validate that optimization provides statistically significant improvement
        
        Args:
            baseline_performance: Performance metrics before optimization
            optimized_performance: Performance metrics after optimization
            min_improvement: Minimum practical improvement threshold (5%)
            
        Returns:
            Dictionary with validation results and business interpretation
        """
        validation_result = self.ab_test_significance(
            baseline_performance, optimized_performance
        )
        
        # Calculate practical significance
        mean_baseline = np.mean(baseline_performance)
        mean_optimized = np.mean(optimized_performance)
        practical_improvement = (mean_optimized - mean_baseline) / mean_baseline
        
        return {
            "statistical_significance": validation_result.is_significant,
            "p_value": validation_result.p_value,
            "confidence_interval": validation_result.confidence_interval,
            "practical_improvement": practical_improvement,
            "practically_significant": practical_improvement >= min_improvement,
            "mean_baseline": mean_baseline,
            "mean_optimized": mean_optimized,
            "sample_size": validation_result.sample_size,
            "recommendation": self._generate_recommendation(validation_result, practical_improvement)
        }
    
    def _generate_recommendation(self, 
                               result: ValidationResult,
                               practical_improvement: float) -> str:
        """Generate business recommendation based on statistical results"""
        if not result.is_significant:
            return "Insufficient evidence: Optimization effect not statistically significant"
        
        if practical_improvement < 0.02:  # 2% threshold for practical significance
            return "Statistically significant but practically negligible improvement"
        
        if practical_improvement >= 0.05:  # 5% threshold for strong recommendation
            return "STRONG RECOMMENDATION: Statistically and practically significant improvement"
        
        return "MODERATE RECOMMENDATION: Statistically significant with modest practical improvement"

# Example usage and testing
if __name__ == "__main__":
    # Example A/B test data
    validator = StatisticalValidator()
    
    # Simulated fuel consumption data (tons per day)
    control_group = [45.2, 46.1, 44.8, 45.9, 46.3, 45.5, 44.9, 46.0, 45.7, 45.1]
    treatment_group = [42.1, 41.8, 42.5, 41.9, 42.3, 41.7, 42.0, 42.2, 41.6, 42.4]
    
    result = validator.ab_test_significance(control_group, treatment_group)
    print(f"Statistical significance: {result.is_significant}")
    print(f"P-value: {result.p_value:.4f}")
    print(f"Confidence interval: {result.confidence_interval}")
    print(f"Effect size: {result.effect_size:.3f}")