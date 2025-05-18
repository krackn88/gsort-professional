"""
Password evolution simulator for gSort Professional.
Implements realistic password change patterns based on research.
"""

import re
import random
import logging
from typing import List, Dict, Any, Tuple, Callable
from datetime import datetime
import string

from gsort.core.processor import ComboProcessor


class PasswordEvolutionSimulator:
    """
    Simulates realistic password changes based on how users typically
    modify their passwords when prompted to change them.
    """
    
    def __init__(self):
        """Initialize the simulator"""
        self.logger = logging.getLogger(__name__)
        
        # Common character substitutions
        self.char_substitutions = {
            'a': ['@', '4'],
            'b': ['8'],
            'e': ['3'],
            'i': ['1', '!'],
            'l': ['1'],
            'o': ['0'],
            's': ['$', '5'],
            't': ['7'],
            ' ': ['.', '_', '-'],
        }
        
        # Common patterns for adding digits/symbols to end
        self.common_suffixes = [
            lambda: str(random.randint(0, 9)),
            lambda: str(random.randint(10, 99)),
            lambda: random.choice(string.punctuation),
            lambda: datetime.now().strftime("%y"),
            lambda: datetime.now().strftime("%Y"),
            lambda: datetime.now().strftime("%m"),
            lambda: random.choice(['!', '.', '*', '#', '$'])
        ]
        
        # Common words to append (seasonal, etc.)
        self.common_append_words = [
            datetime.now().strftime("%b").lower(),  # Current month abbreviation
            datetime.now().strftime("%B").lower(),  # Current month name
            datetime.now().year,                    # Current year
            f"{datetime.now().year}",              # Current year as string
            "new",
            "secure",
            "safe",
        ]
        
        # Common seasons to append
        current_month = datetime.now().month
        if 3 <= current_month <= 5:
            self.season = "spring"
        elif 6 <= current_month <= 8:
            self.season = "summer"
        elif 9 <= current_month <= 11:
            self.season = "fall"
        else:
            self.season = "winter"
    
    def evolve_password(self, password: str, strategy: str = "random") -> str:
        """
        Apply a password evolution strategy to create a new password.
        
        Args:
            password: The original password
            strategy: The evolution strategy to use
                "random" - Choose a random strategy
                "increment" - Increment numbers or add a number
                "substitute" - Replace characters with similar-looking alternatives
                "capitalize" - Change capitalization pattern
                "append" - Append temporal information
                "symbol" - Add or change symbols
                "combined" - Apply multiple strategies
        
        Returns:
            Evolved password
        """
        if strategy == "random":
            # Choose a random strategy
            strategies = ["increment", "substitute", "capitalize", "append", "symbol", "combined"]
            weights = [0.35, 0.2, 0.15, 0.15, 0.1, 0.05]  # Based on observed frequencies
            strategy = random.choices(strategies, weights=weights, k=1)[0]
        
        if strategy == "increment":
            return self._increment_strategy(password)
        elif strategy == "substitute":
            return self._substitute_strategy(password)
        elif strategy == "capitalize":
            return self._capitalize_strategy(password)
        elif strategy == "append":
            return self._append_strategy(password)
        elif strategy == "symbol":
            return self._symbol_strategy(password)
        elif strategy == "combined":
            # Apply 2-3 strategies in sequence
            num_strategies = random.randint(2, 3)
            strategies = random.sample(["increment", "substitute", "capitalize", "append", "symbol"], num_strategies)
            evolved = password
            for strat in strategies:
                evolved = self.evolve_password(evolved, strat)
            return evolved
        else:
            return password  # Invalid strategy
    
    def _increment_strategy(self, password: str) -> str:
        """Increment numbers in the password or add a number if none exists"""
        # Check if password ends with a number
        match = re.search(r'(\d+)$', password)
        if match:
            # Increment the number at the end
            num = int(match.group(1))
            new_num = num + 1
            return password[:match.start(1)] + str(new_num)
        else:
            # Add a digit to the end
            return password + str(random.randint(1, 9))
    
    def _substitute_strategy(self, password: str) -> str:
        """Replace some characters with similar-looking alternatives"""
        new_password = list(password)
        substitutions_made = 0
        
        # Try to make 1-2 substitutions
        target_substitutions = random.randint(1, min(2, len(password)))
        
        # Get indices of characters that can be substituted
        substitutable_indices = [
            i for i, char in enumerate(password.lower())
            if char in self.char_substitutions
        ]
        
        if substitutable_indices:
            # Randomly choose indices to substitute
            indices_to_substitute = random.sample(
                substitutable_indices,
                min(target_substitutions, len(substitutable_indices))
            )
            
            # Make substitutions
            for i in indices_to_substitute:
                char = password[i].lower()
                if char in self.char_substitutions:
                    substitution = random.choice(self.char_substitutions[char])
                    new_password[i] = substitution
                    substitutions_made += 1
        
        # If no substitutions were made, try to add a number or special char
        if substitutions_made == 0:
            return self._increment_strategy(password)
        
        return ''.join(new_password)
    
    def _capitalize_strategy(self, password: str) -> str:
        """Change the capitalization pattern"""
        if password.islower():
            # Capitalize the first letter
            return password[0].upper() + password[1:]
        elif password.isupper():
            # Convert to lowercase
            return password.lower()
        else:
            # Mix up the capitalization
            new_password = list(password.lower())
            
            # Capitalize 1-3 letters
            num_to_capitalize = random.randint(1, min(3, len(password)))
            
            # Select indices to capitalize (only letters)
            letter_indices = [i for i, c in enumerate(new_password) if c.isalpha()]
            
            if letter_indices:
                indices_to_capitalize = random.sample(
                    letter_indices,
                    min(num_to_capitalize, len(letter_indices))
                )
                
                for i in indices_to_capitalize:
                    new_password[i] = new_password[i].upper()
            
            return ''.join(new_password)
    
    def _append_strategy(self, password: str) -> str:
        """Append temporal information or common patterns"""
        append_type = random.choice([
            "month", "year", "season", "word"
        ])
        
        if append_type == "month":
            # Add current month (numeric or abbreviated)
            return password + random.choice([
                datetime.now().strftime("%m"),
                datetime.now().strftime("%b").lower()
            ])
        elif append_type == "year":
            # Add current year (full or last 2 digits)
            return password + random.choice([
                datetime.now().strftime("%Y"),
                datetime.now().strftime("%y")
            ])
        elif append_type == "season":
            # Add current season
            return password + self.season
        elif append_type == "word":
            # Add a common append word
            return password + str(random.choice(self.common_append_words))
    
    def _symbol_strategy(self, password: str) -> str:
        """Add or change symbols in the password"""
        # Check if password already has symbols
        symbols = set(c for c in password if c in string.punctuation)
        
        if symbols:
            # Replace a random symbol with another
            new_password = list(password)
            symbol_indices = [i for i, c in enumerate(password) if c in symbols]
            
            if symbol_indices:
                index = random.choice(symbol_indices)
                new_symbol = random.choice(string.punctuation)
                
                # Avoid replacing with the same symbol
                while new_symbol == password[index]:
                    new_symbol = random.choice(string.punctuation)
                
                new_password[index] = new_symbol
                return ''.join(new_password)
        else:
            # Add a symbol
            position = random.choice(["start", "end", "middle"])
            symbol = random.choice(['!', '@', '#', '$', '%', '&', '*', '.'])
            
            if position == "start":
                return symbol + password
            elif position == "end":
                return password + symbol
            else:
                # Insert at a random middle position
                pos = random.randint(1, len(password) - 1)
                return password[:pos] + symbol + password[pos:]
    
    def generate_evolved_combos(self, combos: List[str], percentage: int = 100, 
                               strategy: str = "random") -> List[str]:
        """
        Generate evolved password combinations based on original combos.
        
        Args:
            combos: List of original email:password combinations
            percentage: Percentage of combos to evolve (1-100)
            strategy: Evolution strategy to use
        
        Returns:
            List of evolved combos
        """
        if not combos:
            return []
        
        # Validate percentage
        percentage = max(1, min(100, percentage))
        
        # Calculate how many passwords to evolve
        num_to_evolve = int(len(combos) * percentage / 100)
        
        # Select random combos to evolve
        indices_to_evolve = random.sample(range(len(combos)), num_to_evolve)
        
        # Create new combo list
        evolved_combos = combos.copy()
        
        # Evolution stats for logging
        strategy_counts = {
            "increment": 0,
            "substitute": 0,
            "capitalize": 0, 
            "append": 0,
            "symbol": 0,
            "combined": 0
        }
        
        # Evolve selected combos
        for idx in indices_to_evolve:
            combo = combos[idx]
            
            # Split combo into email and password
            parts = combo.split(":", 1)
            if len(parts) != 2:
                continue
                
            email, password = parts
            
            # Select strategy for this password
            if strategy == "random":
                current_strategy = random.choices(
                    list(strategy_counts.keys()),
                    weights=[0.35, 0.2, 0.15, 0.15, 0.1, 0.05],
                    k=1
                )[0]
            else:
                current_strategy = strategy
                
            # Update stats
            strategy_counts[current_strategy] += 1
            
            # Evolve password
            evolved_password = self.evolve_password(password, current_strategy)
            
            # Create new combo
            evolved_combo = f"{email}:{evolved_password}"
            
            # Update combo in list
            evolved_combos[idx] = evolved_combo
        
        # Log stats
        total_evolved = sum(strategy_counts.values())
        self.logger.info(f"Evolved {total_evolved} passwords:")
        for strat, count in strategy_counts.items():
            if count > 0:
                percentage = (count / total_evolved) * 100
                self.logger.info(f"  - {strat}: {count} ({percentage:.1f}%)")
        
        return evolved_combos