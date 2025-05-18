"""
Analytics module for gSort Professional.
Provides advanced analytics and visualizations for email:password data.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure

from gsort.core.processor import ComboProcessor, PasswordStrengthStats


@dataclass
class AnalyticsResult:
    """
    Container for analytics results and visualizations.
    """
    title: str
    description: str
    figures: List[Figure]
    data: Dict[str, Any]
    summary: str


class ComboAnalytics:
    """
    Analytics engine for email:password combinations.
    """
    
    def __init__(self):
        """Initialize the analytics engine"""
        self.logger = logging.getLogger(__name__)
    
    def domain_analysis(self, combos: List[str], top_n: int = 20) -> AnalyticsResult:
        """
        Analyze the distribution of email domains in the combo list.
        
        Args:
            combos: List of email:password combinations
            top_n: Number of top domains to include in visualizations
            
        Returns:
            AnalyticsResult with domain analysis data and visualizations
        """
        if not combos:
            return AnalyticsResult(
                title="Domain Analysis",
                description="No data available for analysis",
                figures=[],
                data={},
                summary="No combos provided for analysis"
            )
        
        # Get domain stats
        domain_stats = ComboProcessor.get_domain_stats(combos)
        
        # Convert to dataframe for analysis
        domains_df = pd.DataFrame({
            'domain': list(domain_stats.keys()),
            'count': list(domain_stats.values())
        })
        
        # Sort by count descending
        domains_df = domains_df.sort_values('count', ascending=False).reset_index(drop=True)
        
        # Calculate percentage
        total_count = domains_df['count'].sum()
        domains_df['percentage'] = domains_df['count'] / total_count * 100
        
        # Get top N domains for visualization
        top_domains = domains_df.head(top_n).copy()
        
        # Add an "Other" category for the rest if there are more than top_n domains
        if len(domains_df) > top_n:
            other_count = domains_df.iloc[top_n:]['count'].sum()
            other_percentage = domains_df.iloc[top_n:]['percentage'].sum()
            other_row = pd.DataFrame({
                'domain': ['Other'],
                'count': [other_count],
                'percentage': [other_percentage]
            })
            top_domains = pd.concat([top_domains, other_row]).reset_index(drop=True)
        
        # Create visualizations
        figures = []
        
        # Bar chart of top domains
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(x='count', y='domain', data=top_domains, ax=ax1)
        ax1.set_title('Top Email Domains')
        ax1.set_xlabel('Count')
        ax1.set_ylabel('Domain')
        figures.append(fig1)
        
        # Pie chart of top domains
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        ax2.pie(
            top_domains['count'],
            labels=top_domains['domain'],
            autopct='%1.1f%%',
            startangle=90
        )
        ax2.axis('equal')
        ax2.set_title('Email Domain Distribution')
        figures.append(fig2)
        
        # Calculate summary statistics
        total_domains = len(domain_stats)
        top_domain = domains_df.iloc[0]['domain'] if not domains_df.empty else 'N/A'
        top_domain_count = domains_df.iloc[0]['count'] if not domains_df.empty else 0
        top_domain_pct = domains_df.iloc[0]['percentage'] if not domains_df.empty else 0
        
        # Format summary text
        summary = (
            f"Total unique domains: {total_domains}\n"
            f"Most common domain: {top_domain} ({top_domain_count} occurrences, {top_domain_pct:.1f}%)\n"
            f"Top 5 domains account for {domains_df.head(5)['percentage'].sum():.1f}% of all combos"
        )
        
        # Prepare return data
        data = {
            'total_domains': total_domains,
            'domain_counts': domain_stats,
            'top_domains': top_domains.to_dict('records')
        }
        
        return AnalyticsResult(
            title="Domain Analysis",
            description="Analysis of email domain distribution in the dataset",
            figures=figures,
            data=data,
            summary=summary
        )
    
    def password_strength_analysis(self, combos: List[str]) -> AnalyticsResult:
        """
        Analyze the strength of passwords in the combo list.
        
        Args:
            combos: List of email:password combinations
            
        Returns:
            AnalyticsResult with password strength analysis
        """
        if not combos:
            return AnalyticsResult(
                title="Password Strength Analysis",
                description="No data available for analysis",
                figures=[],
                data={},
                summary="No combos provided for analysis"
            )
        
        # Get password strength stats
        strength_stats = ComboProcessor.analyze_password_strength(combos)
        
        # Create dataframe for visualization
        strength_df = pd.DataFrame({
            'category': ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'],
            'count': [
                strength_stats.very_weak,
                strength_stats.weak,
                strength_stats.medium,
                strength_stats.strong,
                strength_stats.very_strong
            ]
        })
        
        # Calculate percentage
        total_count = strength_df['count'].sum()
        strength_df['percentage'] = strength_df['count'] / total_count * 100
        
        # Create visualizations
        figures = []
        
        # Bar chart of strength distribution
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        bars = sns.barplot(
            x='category', 
            y='count', 
            data=strength_df, 
            ax=ax1,
            palette=['darkred', 'red', 'orange', 'yellowgreen', 'green']
        )
        
        # Add percentage labels on top of bars
        for i, p in enumerate(bars.patches):
            ax1.annotate(
                f'{strength_df.iloc[i]["percentage"]:.1f}%',
                (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center',
                va='bottom'
            )
        
        ax1.set_title('Password Strength Distribution')
        ax1.set_xlabel('Strength Category')
        ax1.set_ylabel('Count')
        figures.append(fig1)
        
        # Pie chart of strength distribution
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        ax2.pie(
            strength_df['count'],
            labels=strength_df['category'],
            autopct='%1.1f%%',
            startangle=90,
            colors=['darkred', 'red', 'orange', 'yellowgreen', 'green']
        )
        ax2.axis('equal')
        ax2.set_title('Password Strength Distribution')
        figures.append(fig2)
        
        # Calculate statistics
        total_weak = strength_stats.very_weak + strength_stats.weak
        total_medium = strength_stats.medium
        total_strong = strength_stats.strong + strength_stats.very_strong
        
        pct_weak = (total_weak / total_count) * 100
        pct_medium = (total_medium / total_count) * 100
        pct_strong = (total_strong / total_count) * 100
        
        # Format summary text
        summary = (
            f"Password strength analysis of {total_count} combos:\n"
            f"Weak passwords (scores 0-1): {total_weak} ({pct_weak:.1f}%)\n"
            f"Medium passwords (score 2): {total_medium} ({pct_medium:.1f}%)\n"
            f"Strong passwords (scores 3-4): {total_strong} ({pct_strong:.1f}%)\n\n"
            f"The majority of passwords are classified as {'weak' if pct_weak > 50 else 'medium' if pct_medium > 50 else 'strong'}"
        )
        
        # Prepare return data
        data = {
            'strength_counts': {
                'very_weak': strength_stats.very_weak,
                'weak': strength_stats.weak,
                'medium': strength_stats.medium,
                'strong': strength_stats.strong,
                'very_strong': strength_stats.very_strong
            },
            'percentages': {
                'very_weak': (strength_stats.very_weak / total_count) * 100,
                'weak': (strength_stats.weak / total_count) * 100,
                'medium': (strength_stats.medium / total_count) * 100,
                'strong': (strength_stats.strong / total_count) * 100,
                'very_strong': (strength_stats.very_strong / total_count) * 100
            }
        }
        
        return AnalyticsResult(
            title="Password Strength Analysis",
            description="Analysis of password strength distribution in the dataset",
            figures=figures,
            data=data,
            summary=summary
        )
    
    def password_pattern_analysis(self, combos: List[str]) -> AnalyticsResult:
        """
        Analyze common patterns in passwords.
        
        Args:
            combos: List of email:password combinations
            
        Returns:
            AnalyticsResult with password pattern analysis
        """
        if not combos:
            return AnalyticsResult(
                title="Password Pattern Analysis",
                description="No data available for analysis",
                figures=[],
                data={},
                summary="No combos provided for analysis"
            )
        
        # Extract passwords into dataframe
        df = pd.DataFrame(combos, columns=['combo'])
        df['password'] = df['combo'].str.split(':', n=1).str[1]
        
        # Analyze password lengths
        df['length'] = df['password'].str.len()
        length_counts = df['length'].value_counts().sort_index()
        
        # Analyze character types
        df['has_upper'] = df['password'].str.contains(r'[A-Z]')
        df['has_lower'] = df['password'].str.contains(r'[a-z]')
        df['has_digit'] = df['password'].str.contains(r'[0-9]')
        df['has_symbol'] = df['password'].str.contains(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\]')
        
        char_type_counts = {
            'Uppercase': df['has_upper'].sum(),
            'Lowercase': df['has_lower'].sum(),
            'Digits': df['has_digit'].sum(),
            'Symbols': df['has_symbol'].sum()
        }
        
        # Analyze character type combinations
        df['uppercase_only'] = df['has_upper'] & ~df['has_lower'] & ~df['has_digit'] & ~df['has_symbol']
        df['lowercase_only'] = ~df['has_upper'] & df['has_lower'] & ~df['has_digit'] & ~df['has_symbol']
        df['digits_only'] = ~df['has_upper'] & ~df['has_lower'] & df['has_digit'] & ~df['has_symbol']
        df['alpha_only'] = (df['has_upper'] | df['has_lower']) & ~df['has_digit'] & ~df['has_symbol']
        df['alnum'] = (df['has_upper'] | df['has_lower']) & df['has_digit'] & ~df['has_symbol']
        df['complex'] = (df['has_upper'] | df['has_lower'] | df['has_digit']) & df['has_symbol']
        
        pattern_counts = {
            'Uppercase Only': df['uppercase_only'].sum(),
            'Lowercase Only': df['lowercase_only'].sum(),
            'Digits Only': df['digits_only'].sum(),
            'Alphabetic Only': df['alpha_only'].sum(),
            'Alphanumeric': df['alnum'].sum(),
            'Complex': df['complex'].sum()
        }
        
        # Common password endings analysis (looking for digit suffixes)
        df['ends_with_digit'] = df['password'].str.contains(r'\d+$')
        df['ends_with_year'] = df['password'].str.contains(r'(19|20)\d{2}$')
        df['ends_with_single_digit'] = df['password'].str.contains(r'\d$')
        
        ending_counts = {
            'Ends with digit': df['ends_with_digit'].sum(),
            'Ends with year': df['ends_with_year'].sum(),
            'Ends with single digit': df['ends_with_single_digit'].sum()
        }
        
        # Create visualizations
        figures = []
        
        # Password length distribution
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        length_counts.plot(kind='bar', ax=ax1)
        ax1.set_title('Password Length Distribution')
        ax1.set_xlabel('Length')
        ax1.set_ylabel('Count')
        figures.append(fig1)
        
        # Character type usage
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        char_types = list(char_type_counts.keys())
        char_counts = list(char_type_counts.values())
        percentages = [count / len(df) * 100 for count in char_counts]
        
        bars = ax2.bar(char_types, percentages, color=['#4285F4', '#34A853', '#FBBC05', '#EA4335'])
        ax2.set_title('Character Types in Passwords')
        ax2.set_xlabel('Character Type')
        ax2.set_ylabel('Percentage of Passwords')
        ax2.set_ylim(0, 100)
        
        # Add percentage labels
        for i, bar in enumerate(bars):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f'{percentages[i]:.1f}%',
                ha='center',
                va='bottom'
            )
        
        figures.append(fig2)
        
        # Password pattern distribution
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        patterns = list(pattern_counts.keys())
        pattern_values = list(pattern_counts.values())
        pattern_percentages = [val / len(df) * 100 for val in pattern_values]
        
        pattern_bars = ax3.bar(patterns, pattern_percentages)
        ax3.set_title('Password Pattern Distribution')
        ax3.set_xlabel('Pattern')
        ax3.set_ylabel('Percentage of Passwords')
        ax3.set_ylim(0, 100)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Add percentage labels
        for i, bar in enumerate(pattern_bars):
            ax3.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f'{pattern_percentages[i]:.1f}%',
                ha='center',
                va='bottom'
            )
        
        figures.append(fig3)
        
        # Calculate statistics for summary
        most_common_length = length_counts.idxmax()
        avg_length = df['length'].mean()
        
        max_pattern = max(pattern_counts.items(), key=lambda x: x[1])
        max_pattern_name = max_pattern[0]
        max_pattern_pct = (max_pattern[1] / len(df)) * 100
        
        year_ending_pct = (ending_counts['Ends with year'] / len(df)) * 100
        
        # Format summary text
        summary = (
            f"Password pattern analysis of {len(df)} combos:\n\n"
            f"Length statistics:\n"
            f"- Most common length: {most_common_length} characters\n"
            f"- Average length: {avg_length:.1f} characters\n\n"
            f"Character usage:\n"
            f"- Uppercase letters: {char_type_counts['Uppercase']} passwords ({char_type_counts['Uppercase']/len(df)*100:.1f}%)\n"
            f"- Lowercase letters: {char_type_counts['Lowercase']} passwords ({char_type_counts['Lowercase']/len(df)*100:.1f}%)\n"
            f"- Digits: {char_type_counts['Digits']} passwords ({char_type_counts['Digits']/len(df)*100:.1f}%)\n"
            f"- Symbols: {char_type_counts['Symbols']} passwords ({char_type_counts['Symbols']/len(df)*100:.1f}%)\n\n"
            f"Most common pattern: {max_pattern_name} ({max_pattern_pct:.1f}%)\n"
            f"Passwords ending with a year (19xx/20xx): {year_ending_pct:.1f}%"
        )
        
        # Prepare return data
        data = {
            'length_distribution': length_counts.to_dict(),
            'char_type_counts': char_type_counts,
            'pattern_counts': pattern_counts,
            'ending_counts': ending_counts,
            'statistics': {
                'most_common_length': int(most_common_length),
                'average_length': float(avg_length),
                'most_common_pattern': max_pattern_name,
                'most_common_pattern_pct': float(max_pattern_pct)
            }
        }
        
        return AnalyticsResult(
            title="Password Pattern Analysis",
            description="Analysis of common patterns in passwords",
            figures=figures,
            data=data,
            summary=summary
        )
    
    def email_password_correlation(self, combos: List[str]) -> AnalyticsResult:
        """
        Analyze correlations between email addresses and passwords.
        
        Args:
            combos: List of email:password combinations
            
        Returns:
            AnalyticsResult with correlation analysis
        """
        if not combos:
            return AnalyticsResult(
                title="Email-Password Correlation Analysis",
                description="No data available for analysis",
                figures=[],
                data={},
                summary="No combos provided for analysis"
            )
        
        # Extract email and password into dataframe
        df = pd.DataFrame(combos, columns=['combo'])
        df[['email', 'password']] = df['combo'].str.split(':', n=1, expand=True)
        
        # Extract username from email
        df['username'] = df['email'].str.split('@').str[0]
        
        # Check if password contains username
        df['password_contains_username'] = df.apply(
            lambda row: row['username'].lower() in row['password'].lower(), 
            axis=1
        )
        
        # Check if password contains email domain
        df['domain'] = df['email'].str.split('@').str[1]
        df['domain_base'] = df['domain'].str.split('.').str[0]
        df['password_contains_domain'] = df.apply(
            lambda row: row['domain_base'].lower() in row['password'].lower(),
            axis=1
        )
        
        # Check for common patterns
        username_in_password_count = df['password_contains_username'].sum()
        domain_in_password_count = df['password_contains_domain'].sum()
        
        username_pct = (username_in_password_count / len(df)) * 100
        domain_pct = (domain_in_password_count / len(df)) * 100
        
        # Create visualizations
        figures = []
        
        # Bar chart of correlation patterns
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        correlation_data = pd.DataFrame({
            'pattern': ['Username in password', 'Domain in password'],
            'count': [username_in_password_count, domain_in_password_count],
            'percentage': [username_pct, domain_pct]
        })
        
        bars = ax1.bar(
            correlation_data['pattern'],
            correlation_data['percentage'],
            color=['#4285F4', '#34A853']
        )
        
        # Add percentage labels
        for i, bar in enumerate(bars):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f'{correlation_data.iloc[i]["percentage"]:.1f}%',
                ha='center',
                va='bottom'
            )
        
        ax1.set_title('Email-Password Correlation Patterns')
        ax1.set_xlabel('Pattern')
        ax1.set_ylabel('Percentage of Passwords')
        ax1.set_ylim(0, max(max(correlation_data['percentage']) + 5, 20))
        figures.append(fig1)
        
        # Format summary text
        summary = (
            f"Email-password correlation analysis of {len(df)} combos:\n\n"
            f"- Passwords containing the email username: {username_in_password_count} ({username_pct:.1f}%)\n"
            f"- Passwords containing the email domain: {domain_in_password_count} ({domain_pct:.1f}%)\n\n"
            f"Overall, {((username_in_password_count + domain_in_password_count) / len(df) * 100):.1f}% "
            f"of passwords have some correlation with the email address."
        )
        
        # Prepare return data
        data = {
            'username_in_password': {
                'count': int(username_in_password_count),
                'percentage': float(username_pct)
            },
            'domain_in_password': {
                'count': int(domain_in_password_count),
                'percentage': float(domain_pct)
            }
        }
        
        return AnalyticsResult(
            title="Email-Password Correlation Analysis",
            description="Analysis of correlations between email addresses and passwords",
            figures=figures,
            data=data,
            summary=summary
        )
    
    def full_analysis(self, combos: List[str]) -> Dict[str, AnalyticsResult]:
        """
        Perform all available analyses on the combo list.
        
        Args:
            combos: List of email:password combinations
            
        Returns:
            Dictionary mapping analysis names to AnalyticsResult objects
        """
        return {
            'domain_analysis': self.domain_analysis(combos),
            'password_strength': self.password_strength_analysis(combos),
            'password_patterns': self.password_pattern_analysis(combos),
            'email_password_correlation': self.email_password_correlation(combos)
        }