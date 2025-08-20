"""
Configuration management for Case Reports Pipeline
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

@dataclass
class Config:
    """Configuration class for the pipeline"""
    # NCBI configuration
    email: str = os.getenv('NCBI_EMAIL')
    ncbi_api_key: Optional[str] = os.getenv('NCBI_API_KEY')
    
    # OpenAI configuration
    openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
    enable_mcq: bool = True
    
    # Processing configuration
    max_papers: int = 20
    delay_between_requests: float = 1.0
    
    # MCQ generation settings
    mcq_model: str = "gpt-4o-mini"
    mcq_timeout: float = 45.0
    min_caption_length: int = 40
    
    # Output configuration
    output_format: str = "csv"
    include_debug_info: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        
        if not self.email or '@' not in self.email:
            raise ValueError("Valid email address is required for NCBI API")
        
        # Set rate limiting based on API key availability
        if self.ncbi_api_key:
            self.delay_between_requests = max(0.1, self.delay_between_requests * 0.5)
        
        # Disable MCQ if no OpenAI key
        if self.enable_mcq and not self.openai_api_key:
            print("⚠️  No OpenAI API key provided - MCQ generation disabled")
            self.enable_mcq = False
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        return cls(
            email=os.getenv('NCBI_EMAIL', 'user@example.com'),
            ncbi_api_key=os.getenv('NCBI_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            enable_mcq=os.getenv('ENABLE_MCQ', 'true').lower() == 'true',
            max_papers=int(os.getenv('MAX_PAPERS', '20')),
            delay_between_requests=float(os.getenv('DELAY_SECONDS', '1.0'))
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            'email': self.email,
            'has_ncbi_api_key': bool(self.ncbi_api_key),
            'has_openai_api_key': bool(self.openai_api_key),
            'enable_mcq': self.enable_mcq,
            'max_papers': self.max_papers,
            'delay_between_requests': self.delay_between_requests,
            'mcq_model': self.mcq_model,
            'mcq_timeout': self.mcq_timeout,
            'min_caption_length': self.min_caption_length
        }