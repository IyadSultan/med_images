"""
Utility functions for Case Reports Pipeline
"""

import csv
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def setup_logging(log_dir: Path) -> logging.Logger:
    """Setup logging configuration"""
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('case_reports_pipeline')
    logger.setLevel(logging.INFO)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("Logging initialized")
    
    return logger

def create_output_directories(base_dir: Path) -> Dict[str, Path]:
    """Create output directory structure"""
    
    directories = {
        'base': base_dir,
        'outputs': base_dir / 'outputs',
        'logs': base_dir / 'logs',
        'temp': base_dir / 'temp'
    }
    
    # Create all directories
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"   📁 Created: {path}")
    
    return directories

def save_results_csv(figure_data: List[Dict[str, Any]], output_dir: Path) -> str:
    """
    Save figure data to CSV with specified column order
    
    Args:
        figure_data: List of figure dictionaries
        output_dir: Output directory path
    
    Returns:
        Path to saved CSV file
    """
    
    if not figure_data:
        raise ValueError("No figure data to save")
    
    # Define exact column order as requested
    columns = [
        'pmcid',
        'title',
        'journal',
        'abstract',
        'figure_number',  # This will be "Figure" in the CSV
        'paper_link',
        'figure_link',
        'caption',
        'mcq_question',  # This will be "MCQ" in the CSV
        'option_a',      # This will be "optionA" in the CSV
        'option_b',      # This will be "optionB" in the CSV
        'option_c',      # This will be "optionC" in the CSV
        'option_d',      # This will be "optionD" in the CSV
        'option_e',      # This will be "optionE" in the CSV
        'answer',
        'commentary',
        'subject',
        'hashtags',
        'difficulty_level'
    ]
    
    # Create CSV filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"case_reports_figures_{timestamp}.csv"
    csv_path = output_dir / csv_filename
    
    # Prepare data with correct column mapping
    processed_data = []
    
    for row in figure_data:
        processed_row = {}
        
        for col in columns:
            if col == 'figure_number':
                # Map figure_number to a more descriptive format
                fig_num = row.get('figure_number', 1)
                fig_label = row.get('figure_label', f'Figure {fig_num}')
                processed_row['Figure'] = fig_label
                
            elif col == 'mcq_question':
                processed_row['MCQ'] = row.get('mcq_question', '')
                
            elif col == 'option_a':
                processed_row['optionA'] = row.get('option_a', '')
            elif col == 'option_b':
                processed_row['optionB'] = row.get('option_b', '')
            elif col == 'option_c':
                processed_row['optionC'] = row.get('option_c', '')
            elif col == 'option_d':
                processed_row['optionD'] = row.get('option_d', '')
            elif col == 'option_e':
                processed_row['optionE'] = row.get('option_e', '')
                
            elif col == 'paper_link':
                processed_row['link to paper'] = row.get('paper_link', '')
            elif col == 'figure_link':
                processed_row['link to figure'] = row.get('figure_link', '')
                
            else:
                # Direct mapping for other columns
                processed_row[col] = row.get(col, '')
        
        processed_data.append(processed_row)
    
    # Write CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Use the processed column names
        fieldnames = [
            'pmcid', 'title', 'journal', 'abstract', 'Figure',
            'link to paper', 'link to figure', 'caption', 'MCQ',
            'optionA', 'optionB', 'optionC', 'optionD', 'optionE',
            'answer', 'commentary', 'subject', 'hashtags', 'difficulty_level'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_data)
    
    print(f"   💾 CSV saved: {csv_path}")
    
    return str(csv_path)

def save_summary_json(data: Dict[str, Any], output_dir: Path) -> str:
    """Save processing summary as JSON"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"processing_summary_{timestamp}.json"
    json_path = output_dir / json_filename
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return str(json_path)

def validate_csv_output(csv_path: str) -> Dict[str, Any]:
    """Validate the generated CSV and return statistics"""
    
    if not os.path.exists(csv_path):
        return {'error': 'CSV file not found'}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return {'error': 'CSV file is empty'}
        
        # Count various metrics
        total_rows = len(rows)
        rows_with_mcq = sum(1 for row in rows if row.get('MCQ', '').strip())
        rows_with_figures = sum(1 for row in rows if row.get('Figure', '').strip())
        rows_with_captions = sum(1 for row in rows if row.get('caption', '').strip())
        
        # Unique papers
        unique_pmcids = len(set(row.get('pmcid', '') for row in rows if row.get('pmcid', '')))
        
        # Subject distribution
        subjects = {}
        for row in rows:
            subject = row.get('subject', 'Unknown').strip()
            if subject:
                subjects[subject] = subjects.get(subject, 0) + 1
        
        # Difficulty distribution
        difficulties = {}
        for row in rows:
            difficulty = row.get('difficulty_level', 'Unknown').strip()
            if difficulty:
                difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
        
        return {
            'total_rows': total_rows,
            'unique_papers': unique_pmcids,
            'rows_with_mcq': rows_with_mcq,
            'rows_with_figures': rows_with_figures,
            'rows_with_captions': rows_with_captions,
            'mcq_coverage': round(rows_with_mcq / total_rows * 100, 1) if total_rows > 0 else 0,
            'subject_distribution': subjects,
            'difficulty_distribution': difficulties,
            'columns': list(rows[0].keys()) if rows else []
        }
        
    except Exception as e:
        return {'error': f'Error reading CSV: {e}'}

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    else:
        return f"{seconds/3600:.1f} hours"

def clean_text(text: str, max_length: int = None) -> str:
    """Clean and truncate text for CSV output"""
    
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove problematic characters for CSV
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Truncate if necessary
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text

def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    
    return 0.0

def create_readme(output_dir: Path, config_dict: Dict[str, Any]) -> str:
    """Create README file for the output directory"""
    
    readme_content = f"""# Case Reports Figure Analysis Results

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Configuration
- Max papers: {config_dict.get('max_papers', 'Unknown')}
- MCQ generation: {'Enabled' if config_dict.get('enable_mcq', False) else 'Disabled'}
- Email: {config_dict.get('email', 'Unknown')}
- NCBI API key: {'Yes' if config_dict.get('has_ncbi_api_key', False) else 'No'}
- OpenAI API key: {'Yes' if config_dict.get('has_openai_api_key', False) else 'No'}

## Output Files
- **case_reports_figures_*.csv**: Main results file with figure data and MCQs
- **processing_summary_*.json**: Detailed processing statistics
- **logs/**: Processing logs
- **temp/**: Temporary files (can be deleted)

## CSV Columns
1. **pmcid**: PMC identifier
2. **title**: Paper title
3. **journal**: Journal name
4. **abstract**: Paper abstract
5. **Figure**: Figure label/number
6. **link to paper**: PMC paper URL
7. **link to figure**: PMC figure page URL
8. **caption**: Figure caption
9. **MCQ**: Multiple choice question
10. **optionA-E**: MCQ options
11. **answer**: Correct answer (A-E)
12. **commentary**: Explanation and key findings
13. **subject**: USMLE subject area
14. **hashtags**: Medical hashtags for searchability
15. **difficulty_level**: easy/intermediate/difficult

## Usage
This data can be used for:
- Medical education platforms
- USMLE preparation tools
- Figure-based learning systems
- Research on medical imaging
- Machine learning training data

## Notes
- Each row represents one figure from a case report
- MCQs are generated using GPT-4o-mini
- Images are sourced from PMC open access articles
- Subjects follow USMLE classification
"""
    
    readme_path = output_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    return str(readme_path)