"""
Core processor module for gSort Professional.
Handles high-performance processing of email:password combinations.
"""

import os
import re
import mmap
import random
import logging
import threading
from typing import List, Tuple, Dict, Set, Optional, Callable, Iterator
import concurrent.futures
from dataclasses import dataclass
import pandas as pd
import numpy as np
from tqdm import tqdm

# Constants for processing
CHUNK_SIZE = 16 * 1024 * 1024       # 16 MB for better throughput
MAX_MMAP_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
DEFAULT_THREAD_COUNT = 8            # Modern CPUs often have 8+ cores

# Regular expressions for different patterns
EMAIL_PASS_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b:[^\s:]{4,}'
)
SYMBOL_SET = set("!@#$%^&*()_+-=[]{}|;:',.<>?/")

# Password strength characteristics
HAS_UPPERCASE = re.compile(r'[A-Z]')
HAS_LOWERCASE = re.compile(r'[a-z]')
HAS_DIGIT = re.compile(r'[0-9]')
HAS_SYMBOL = re.compile(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\]')


@dataclass
class ProcessingStats:
    """Statistics from combo processing"""
    total_combos: int = 0
    unique_combos: int = 0
    duplicates_removed: int = 0
    processing_time_ms: int = 0
    bytes_processed: int = 0


@dataclass
class PasswordStrengthStats:
    """Password strength statistics"""
    very_weak: int = 0
    weak: int = 0
    medium: int = 0
    strong: int = 0
    very_strong: int = 0


class ComboProcessor:
    """
    High-performance processor for email:password combinations.
    Uses parallel processing, memory mapping, and pandas for optimal speed.
    """
    
    def __init__(self, max_workers: int = DEFAULT_THREAD_COUNT):
        """Initialize the processor with the specified number of worker threads"""
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
    
    def process_files(
        self,
        file_paths: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[List[str], ProcessingStats]:
        """
        Process multiple files containing email:password combinations.
        
        Args:
            file_paths: List of file paths to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (unique_combos, stats)
        """
        import time
        start_time = time.time()
        
        # Calculate total size for progress reporting
        total_size = sum(os.path.getsize(fp) for fp in file_paths)
        processed_bytes = 0
        
        # Shared state between threads
        stats = ProcessingStats()
        lock = threading.Lock()
        
        # For duplicate detection
        unique_emails_lower = set()
        unique_combos = []
        
        def process_chunk(chunk: str) -> List[str]:
            """Process a chunk of text and return found combos"""
            return EMAIL_PASS_PATTERN.findall(chunk)
        
        def process_file(file_path: str) -> List[str]:
            """Process a single file and return unique combos"""
            nonlocal processed_bytes
            file_size = os.path.getsize(file_path)
            self.logger.info(f"Processing {file_path} ({file_size/1024/1024:.2f} MB)")
            
            file_combos = []
            
            try:
                # For smaller files, use memory mapping for performance
                if file_size <= MAX_MMAP_SIZE:
                    with open(file_path, 'r+b') as f:
                        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                            content = mm.read().decode('utf-8', errors='ignore')
                            file_combos = process_chunk(content)
                else:
                    # For larger files, read in chunks
                    file_combos = []
                    with open(file_path, 'r', errors='ignore') as f:
                        # Keep a buffer to handle combos that cross chunk boundaries
                        buffer = ''
                        while True:
                            chunk = f.read(CHUNK_SIZE)
                            if not chunk:
                                # Process any remaining buffer at the end
                                if buffer:
                                    file_combos.extend(process_chunk(buffer))
                                break
                            
                            # Combine with previous buffer
                            current_chunk = buffer + chunk
                            # Keep a small overlap to prevent missing combos at chunk boundaries
                            buffer = current_chunk[-200:] if len(current_chunk) > 200 else current_chunk
                            
                            file_combos.extend(process_chunk(current_chunk))
                
                with lock:
                    stats.bytes_processed += file_size
                    processed_bytes += file_size
                    if progress_callback:
                        progress_callback(processed_bytes, total_size)
                
                return file_combos
            
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                return []
        
        # Process files in parallel
        all_combos = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for processing
            future_to_file = {executor.submit(process_file, fp): fp for fp in file_paths}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    file_combos = future.result()
                    all_combos.extend(file_combos)
                    self.logger.info(f"Found {len(file_combos)} combos in {file_path}")
                except Exception as e:
                    self.logger.error(f"Error getting results from {file_path}: {e}")
        
        # Deduplicate combos efficiently using pandas
        self.logger.info(f"Deduplicating {len(all_combos)} combos")
        
        if all_combos:
            # Use pandas for efficient deduplication
            df = pd.DataFrame(all_combos, columns=['combo'])
            
            # Create lowercase version for case-insensitive deduplication
            df['combo_lower'] = df['combo'].str.lower()
            
            # Drop duplicates based on lowercase version
            df_unique = df.drop_duplicates(subset=['combo_lower'])
            
            # Get original combos and count duplicates
            unique_combos = df_unique['combo'].tolist()
            duplicates_removed = len(all_combos) - len(unique_combos)
            
            # Randomize the order
            random.shuffle(unique_combos)
            
            # Update stats
            stats.total_combos = len(all_combos)
            stats.unique_combos = len(unique_combos)
            stats.duplicates_removed = duplicates_removed
        else:
            self.logger.warning("No combos found in provided files")
        
        # Calculate processing time
        stats.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return unique_combos, stats
    
    @staticmethod
    def get_domain_stats(combos: List[str]) -> Dict[str, int]:
        """
        Calculate statistics on email domains in the combo list.
        
        Args:
            combos: List of email:password combinations
            
        Returns:
            Dictionary mapping domain to count
        """
        if not combos:
            return {}
        
        # Extract domains and count with pandas
        df = pd.DataFrame(combos, columns=['combo'])
        
        # Extract email part and domain
        df['email'] = df['combo'].str.split(':', n=1).str[0]
        df['domain'] = df['email'].str.split('@').str[-1].str.lower()
        
        # Count occurrences of each domain
        domain_counts = df['domain'].value_counts().to_dict()
        
        return domain_counts
    
    @staticmethod
    def password_strength(password: str) -> int:
        """
        Calculate the strength of a password on a scale of 0-4.
        
        Args:
            password: The password to evaluate
            
        Returns:
            Integer score from 0 (very weak) to 4 (very strong)
        """
        if not password:
            return 0
            
        score = 0
        
        # Length based score
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        
        # Character variety
        if HAS_UPPERCASE.search(password):
            score += 1
        if HAS_LOWERCASE.search(password):
            score += 1
        if HAS_DIGIT.search(password):
            score += 1
        if HAS_SYMBOL.search(password):
            score += 1
        
        # Normalize to 0-4 range
        return min(score, 4)
    
    @staticmethod
    def analyze_password_strength(combos: List[str]) -> PasswordStrengthStats:
        """
        Analyze the strength distribution of passwords in the combo list.
        
        Args:
            combos: List of email:password combinations
            
        Returns:
            PasswordStrengthStats object with counts for each category
        """
        if not combos:
            return PasswordStrengthStats()
        
        # Extract passwords and evaluate with pandas
        df = pd.DataFrame(combos, columns=['combo'])
        df['password'] = df['combo'].str.split(':', n=1).str[1]
        
        # Define vectorized strength function
        def strength_vec(passwords: pd.Series) -> pd.Series:
            # Vectorized version using apply
            return passwords.apply(ComboProcessor.password_strength)
        
        # Calculate strengths
        df['strength'] = strength_vec(df['password'])
        
        # Count occurrences of each strength level
        strength_counts = df['strength'].value_counts().to_dict()
        
        # Create stats object
        stats = PasswordStrengthStats(
            very_weak=strength_counts.get(0, 0),
            weak=strength_counts.get(1, 0),
            medium=strength_counts.get(2, 0),
            strong=strength_counts.get(3, 0),
            very_strong=strength_counts.get(4, 0)
        )
        
        return stats
    
    @staticmethod
    def filter_by_domain(combos: List[str], domains: List[str]) -> List[str]:
        """
        Filter combos by specified email domains.
        
        Args:
            combos: List of email:password combinations
            domains: List of domains to filter for
            
        Returns:
            Filtered list of combos
        """
        if not combos or not domains:
            return []
        
        # Convert domains to lowercase for case-insensitive matching
        domains_lower = [d.lower() for d in domains]
        
        # Use pandas for efficient filtering
        df = pd.DataFrame(combos, columns=['combo'])
        df['email'] = df['combo'].str.split(':', n=1).str[0]
        df['domain'] = df['email'].str.split('@').str[-1].str.lower()
        
        # Filter rows where domain is in the list
        filtered_df = df[df['domain'].isin(domains_lower)]
        
        return filtered_df['combo'].tolist()
    
    @staticmethod
    def filter_by_password_length(combos: List[str], min_length: int, max_length: int) -> List[str]:
        """
        Filter combos by password length.
        
        Args:
            combos: List of email:password combinations
            min_length: Minimum password length (inclusive)
            max_length: Maximum password length (inclusive)
            
        Returns:
            Filtered list of combos
        """
        if not combos:
            return []
        
        # Use pandas for efficient filtering
        df = pd.DataFrame(combos, columns=['combo'])
        df['password'] = df['combo'].str.split(':', n=1).str[1]
        df['pw_length'] = df['password'].str.len()
        
        # Filter by length
        filtered_df = df[(df['pw_length'] >= min_length) & (df['pw_length'] <= max_length)]
        
        return filtered_df['combo'].tolist()
    
    @staticmethod
    def filter_by_regex(combos: List[str], pattern: str, invert: bool = False) -> List[str]:
        """
        Filter combos using a regular expression.
        
        Args:
            combos: List of email:password combinations
            pattern: Regular expression pattern
            invert: If True, return combos that don't match the pattern
            
        Returns:
            Filtered list of combos
        """
        if not combos:
            return []
        
        try:
            regex = re.compile(pattern)
        except re.error as e:
            logging.error(f"Invalid regex pattern: {e}")
            return combos
        
        # Use pandas for efficient filtering
        df = pd.DataFrame(combos, columns=['combo'])
        
        # Apply regex filter
        if invert:
            filtered_df = df[~df['combo'].str.contains(regex)]
        else:
            filtered_df = df[df['combo'].str.contains(regex)]
        
        return filtered_df['combo'].tolist()
    
    @staticmethod
    def modify_passwords(combos: List[str], operation: str, value: str) -> List[str]:
        """
        Modify passwords in combos according to the specified operation.
        
        Args:
            combos: List of email:password combinations
            operation: The operation to perform ('append', 'prepend', 'replace', 'capitalize')
            value: The value to use in the operation (not used for 'capitalize')
            
        Returns:
            List of modified combos
        """
        if not combos:
            return []
        
        # Use pandas for efficient modification
        df = pd.DataFrame(combos, columns=['combo'])
        df[['email', 'password']] = df['combo'].str.split(':', n=1, expand=True)
        
        # Apply the requested operation
        if operation == 'append':
            df['password'] = df['password'] + value
        elif operation == 'prepend':
            df['password'] = value + df['password']
        elif operation == 'replace':
            # Split value as old:new
            if ':' in value:
                old, new = value.split(':', 1)
                df['password'] = df['password'].str.replace(old, new, regex=False)
        elif operation == 'capitalize':
            # Capitalize first letter only if it's lowercase
            def cap_first(s):
                return s[0].upper() + s[1:] if s and s[0].islower() else s
            
            df['password'] = df['password'].apply(cap_first)
        
        # Recombine email and password
        df['new_combo'] = df['email'] + ':' + df['password']
        
        return df['new_combo'].tolist()
    
    @staticmethod
    def batch_process(combos: List[str], operations: List[Dict]) -> List[str]:
        """
        Apply a series of operations to the combo list.
        
        Args:
            combos: List of email:password combinations
            operations: List of operation dictionaries with keys 'type' and 'params'
            
        Returns:
            Processed list of combos
        """
        result = combos.copy()
        
        for op in operations:
            op_type = op.get('type', '')
            params = op.get('params', {})
            
            if op_type == 'filter_domain':
                domains = params.get('domains', [])
                result = ComboProcessor.filter_by_domain(result, domains)
            
            elif op_type == 'filter_length':
                min_len = params.get('min_length', 1)
                max_len = params.get('max_length', 100)
                result = ComboProcessor.filter_by_password_length(result, min_len, max_len)
            
            elif op_type == 'filter_regex':
                pattern = params.get('pattern', '')
                invert = params.get('invert', False)
                result = ComboProcessor.filter_by_regex(result, pattern, invert)
            
            elif op_type == 'modify':
                operation = params.get('operation', '')
                value = params.get('value', '')
                result = ComboProcessor.modify_passwords(result, operation, value)
            
            elif op_type == 'shuffle':
                random.shuffle(result)
            
            elif op_type == 'sort':
                key = params.get('key', 'combo')
                reverse = params.get('reverse', False)
                
                if key == 'combo':
                    result.sort(key=lambda x: x.lower(), reverse=reverse)
                elif key == 'domain':
                    df = pd.DataFrame(result, columns=['combo'])
                    df['email'] = df['combo'].str.split(':', n=1).str[0]
                    df['domain'] = df['email'].str.split('@').str[-1].str.lower()
                    df = df.sort_values('domain', ascending=not reverse)
                    result = df['combo'].tolist()
                elif key == 'password_length':
                    df = pd.DataFrame(result, columns=['combo'])
                    df['password'] = df['combo'].str.split(':', n=1).str[1]
                    df['pw_length'] = df['password'].str.len()
                    df = df.sort_values('pw_length', ascending=not reverse)
                    result = df['combo'].tolist()
        
        return result