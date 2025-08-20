# Case Reports Figure Analysis Pipeline

Automated pipeline for retrieving medical case reports, extracting figures, and generating educational MCQs using AI.

## 🎯 Features

- **Case Reports Retrieval**: Searches NCBI PMC for case reports by date range
- **Figure Extraction**: Scrapes figures and captions from PMC papers
- **MCQ Generation**: Creates USMLE-aligned multiple choice questions using GPT-4o-mini
- **Medical Hashtags**: Automatic extraction of medical terminology for searchability
- **Structured Output**: CSV format with standardized columns for analysis

## 📊 Output Format

Each row in the final CSV represents one figure with complete metadata:

| Column | Description |
|--------|-------------|
| `pmcid` | PMC identifier |
| `title` | Paper title |
| `journal` | Journal name |
| `abstract` | Paper abstract |
| `Figure` | Figure label/number |
| `link to paper` | PMC paper URL |
| `link to figure` | PMC figure page URL |
| `caption` | Figure caption |
| `MCQ` | Multiple choice question |
| `optionA-E` | MCQ options |
| `answer` | Correct answer (A-E) |
| `commentary` | Explanation summarizing findings |
| `subject` | USMLE subject area |
| `hashtags` | Medical hashtags |
| `difficulty_level` | easy/intermediate/difficult |

## 🚀 Quick Start

### 1. Installation

```bash
git clone <repository-url>
cd case-reports-pipeline
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Required: NCBI email
export NCBI_EMAIL="your-email@example.com"

# Optional but recommended: NCBI API key
export NCBI_API_KEY="your-ncbi-api-key"

# Optional: OpenAI API key for MCQ generation
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Usage Examples

```bash
# Get 10 example case reports (good for testing)
python main.py --example

# Get case reports from December 2024
python main.py --month 12 --year 2024 --max_papers 50

# Get case reports from date range
python main.py --start_date 2024-01-01 --end_date 2024-12-31 --max_papers 100

# Disable MCQ generation (faster processing)
python main.py --example --disable_mcq
```

## 📁 Repository Structure

```
case-reports-pipeline/
├── main.py                    # Entry point
├── src/
│   ├── config.py             # Configuration management
│   ├── case_reports_retriever.py  # NCBI case reports retrieval
│   ├── figure_scraper.py     # PMC figure scraping
│   ├── mcq_generator.py      # OpenAI MCQ generation
│   └── utils.py              # Utility functions
├── outputs/                   # Generated results (created automatically)
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## 🔧 Configuration

### Command Line Arguments

```bash
python main.py --help
```

**Time Period (choose one):**
- `--month` + `--year`: Specific month (e.g., `--month 12 --year 2024`)
- `--example`: Get 10 recent case reports for testing
- `--start_date` + `--end_date`: Date range (YYYY-MM-DD format)

**Processing Options:**
- `--max_papers`: Maximum papers to retrieve (default: 20)
- `--email`: NCBI email address (required)
- `--api_key`: NCBI API key (optional but recommended)
- `--openai_key`: OpenAI API key (for MCQ generation)
- `--output_dir`: Output directory (default: outputs/)
- `--disable_mcq`: Disable MCQ generation

### Environment Variables

```bash
# NCBI Configuration
export NCBI_EMAIL="your-email@example.com"
export NCBI_API_KEY="your-ncbi-api-key"

# OpenAI Configuration
export OPENAI_API_KEY="your-openai-api-key"

# Processing Configuration
export MAX_PAPERS=50
export DELAY_SECONDS=1.0
export ENABLE_MCQ=true
```

## 📚 API Keys Setup

### NCBI API Key (Recommended)
1. Visit: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
2. Register for free API key
3. Increases rate limits from 3 to 10 requests/second

### OpenAI API Key (For MCQ Generation)
1. Visit: https://platform.openai.com/api-keys
2. Create API key
3. Enables AI-powered MCQ generation with GPT-4o-mini

## 🏥 Medical Education Features

### MCQ Generation
- **Image-focused questions** based on figure captions
- **USMLE-aligned** subjects (Radiology, Pathology, Surgery, etc.)
- **Difficulty levels**: easy, intermediate, difficult
- **Randomized answers** to prevent bias
- **Detailed explanations** citing visual features

### Medical Hashtags
- Automatic extraction of medical terminology
- Includes: anatomy, pathology, imaging modalities, procedures
- Enhances searchability and categorization

### Subject Classification
**USMLE Step 1:** Anatomy, Physiology, Biochemistry, Pharmacology, Microbiology & Immunology, Pathology, Behavioral Science & Biostatistics, Genetics

**USMLE Step 2:** Internal Medicine, Surgery, Pediatrics, Obstetrics & Gynecology, Psychiatry, Neurology, Emergency Medicine, Family Medicine, Radiology, Onc