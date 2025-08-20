#!/usr/bin/env python3
"""
Case Reports Figure Analysis Pipeline
=====================================

Main entry point for retrieving case reports, scraping figures, and generating MCQs.

Usage:
    # Get case reports from specific month/year
    python main.py --month 12 --year 2024 --max_papers 50

    # Get example set of 10 case reports
    python main.py --example

    # Get case reports from date range
    python main.py --start_date 2024-01-01 --end_date 2024-12-31 --max_papers 100

Arguments:
    --month: Month (1-12)
    --year: Year (e.g., 2024)
    --start_date: Start date (YYYY-MM-DD)
    --end_date: End date (YYYY-MM-DD)
    --max_papers: Maximum number of papers to retrieve
    --example: Use example mode (10 recent case reports)
    --email: NCBI email (required)
    --api_key: NCBI API key (optional)
    --openai_key: OpenAI API key (optional, for MCQ generation)
    --output_dir: Output directory (default: outputs/)

Output:
    outputs/
    ├── case_reports_YYYYMMDD_HHMMSS.csv
    ├── logs/
    └── temp/
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.case_reports_retriever import CaseReportsRetriever
from src.figure_scraper import FigureScraper
from src.mcq_generator import MCQGenerator
from src.utils import setup_logging, create_output_directories, save_results_csv
from src.config import Config

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Case Reports Figure Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --month 12 --year 2024 --max_papers 50
  python main.py --example
  python main.py --start_date 2024-01-01 --end_date 2024-12-31
        """
    )
    
    # Time period options (mutually exclusive)
    time_group = parser.add_mutually_exclusive_group(required=True)
    time_group.add_argument('--month', type=int, choices=range(1, 13),
                           help='Month (1-12)')
    time_group.add_argument('--example', action='store_true',
                           help='Use example mode (10 recent case reports)')
    time_group.add_argument('--start_date', type=str,
                           help='Start date (YYYY-MM-DD)')
    
    # Year (required if month is specified)
    parser.add_argument('--year', type=int,
                       help='Year (required if --month is used)')
    parser.add_argument('--end_date', type=str,
                       help='End date (YYYY-MM-DD, required if --start_date is used)')
    
    # Processing options
    parser.add_argument('--max_papers', type=int, default=20,
                       help='Maximum number of papers to retrieve (default: 20)')
    
    # API configuration
    parser.add_argument('--email', type=str, default="user@example.com",
                       help='NCBI email address (required)')
    parser.add_argument('--api_key', type=str,
                       help='NCBI API key (optional but recommended)')
    parser.add_argument('--openai_key', type=str,
                       help='OpenAI API key (for MCQ generation)')
    
    # Output configuration
    parser.add_argument('--output_dir', type=str, default="outputs",
                       help='Output directory (default: outputs/)')
    parser.add_argument('--disable_mcq', action='store_true',
                       help='Disable MCQ generation')
    
    return parser.parse_args()

def validate_arguments(args):
    """Validate command line arguments"""
    
    # Validate month/year combination
    if args.month and not args.year:
        raise ValueError("--year is required when --month is specified")
    
    # Validate date range
    if args.start_date and not args.end_date:
        raise ValueError("--end_date is required when --start_date is specified")
    
    # Validate date formats
    if args.start_date:
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format")
    
    # Validate email
    if not args.email or '@' not in args.email:
        raise ValueError("Valid email address is required for NCBI API")
    
    return True

def create_date_range(args):
    """Create date range based on arguments"""
    
    if args.example:
        # Last 30 days for example
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    elif args.month and args.year:
        # Specific month/year
        start_date = datetime(args.year, args.month, 1)
        if args.month == 12:
            end_date = datetime(args.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(args.year, args.month + 1, 1) - timedelta(days=1)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    elif args.start_date and args.end_date:
        # Date range
        return args.start_date, args.end_date
    
    else:
        raise ValueError("Invalid date specification")

def main():
    """Main pipeline execution"""
    
    print("🏥 Case Reports Figure Analysis Pipeline")
    print("=" * 50)
    
    try:
        # Parse and validate arguments
        args = parse_arguments()
        validate_arguments(args)
        
        # Setup configuration
        config = Config(
            email=args.email,
            ncbi_api_key=args.api_key,
            openai_api_key=args.openai_key or os.getenv('OPENAI_API_KEY'),
            enable_mcq=not args.disable_mcq,
            max_papers=args.max_papers if not args.example else 10
        )
        
        # Create output directories
        output_base = Path(args.output_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_dir = output_base / f"session_{timestamp}"
        
        directories = create_output_directories(session_dir)
        
        # Setup logging
        logger = setup_logging(directories['logs'])
        logger.info("Starting Case Reports Figure Analysis Pipeline")
        
        # Determine date range
        start_date, end_date = create_date_range(args)
        logger.info(f"Date range: {start_date} to {end_date}")
        
        print(f"\n📅 Processing period: {start_date} to {end_date}")
        print(f"📊 Maximum papers: {config.max_papers}")
        print(f"📁 Output directory: {session_dir}")
        
        # Initialize components
        retriever = CaseReportsRetriever(config)
        scraper = FigureScraper(config)
        mcq_gen = MCQGenerator(config) if config.enable_mcq else None
        
        # Step 1: Retrieve case reports
        print(f"\n📋 Step 1: Retrieving case reports...")
        case_reports = retriever.get_case_reports_by_date_range(
            start_date=start_date,
            end_date=end_date,
            max_papers=config.max_papers
        )
        
        if not case_reports:
            print("❌ No case reports found for the specified criteria")
            return
        
        logger.info(f"Retrieved {len(case_reports)} case reports")
        print(f"✅ Found {len(case_reports)} case reports")
        
        # Step 2: Scrape figures
        print(f"\n🖼️  Step 2: Scraping figures from papers...")
        figure_data = []
        
        for i, paper in enumerate(case_reports, 1):
            print(f"   [{i}/{len(case_reports)}] Processing {paper['pmcid']}")
            
            figures = scraper.scrape_figures(paper['pmcid'])
            
            for fig_num, figure in enumerate(figures, 1):
                # Combine paper and figure data
                combined_data = {
                    'pmcid': paper['pmcid'],
                    'title': paper['title'],
                    'journal': paper['journal'],
                    'abstract': paper['abstract'],
                    'figure_number': fig_num,
                    'figure_label': figure['label'],
                    'paper_link': paper['pmc_url'],
                    'figure_link': figure['figure_url'],  # This now contains the CDN URL
                    'caption': figure['caption'],
                    'image_url': figure['image_url']      # This also contains the CDN URL
                }
                
                # Step 3: Generate MCQ if enabled
                if mcq_gen and figure['caption']:
                    print(f"      🧠 Generating MCQ for Figure {fig_num}...")
                    mcq_data = mcq_gen.generate_mcq(
                        abstract=paper['abstract'],
                        caption=figure['caption'],
                        title=paper['title']
                    )
                    combined_data.update(mcq_data)
                else:
                    # Add empty MCQ fields
                    combined_data.update({
                        'mcq_question': '',
                        'option_a': '', 'option_b': '', 'option_c': '', 'option_d': '', 'option_e': '',
                        'answer': '', 'commentary': '', 'subject': '', 'hashtags': '',
                        'difficulty_level': ''
                    })
                
                figure_data.append(combined_data)
        
        print(f"✅ Processed {len(figure_data)} figures total")
        
        # Show CDN URL extraction stats
        if figure_data:
            cdn_urls = sum(1 for f in figure_data if f.get('figure_link') and 'cdn.ncbi.nlm.nih.gov/pmc/blobs/' in f['figure_link'])
            print(f"🔗 Direct CDN URLs extracted: {cdn_urls}/{len(figure_data)} ({cdn_urls/len(figure_data)*100:.1f}%)")
        
        # Step 4: Save results
        print(f"\n💾 Step 3: Saving results...")
        
        if figure_data:
            output_file = save_results_csv(figure_data, directories['outputs'])
            
            print(f"✅ Results saved to: {output_file}")
            logger.info(f"Results saved to: {output_file}")
            
            # Print summary
            print(f"\n📊 PIPELINE SUMMARY")
            print(f"=" * 30)
            print(f"Papers processed: {len(case_reports)}")
            print(f"Figures extracted: {len(figure_data)}")
            print(f"MCQs generated: {len([f for f in figure_data if f.get('mcq_question')])}")
            if figure_data:
                cdn_urls = sum(1 for f in figure_data if f.get('figure_link') and 'cdn.ncbi.nlm.nih.gov/pmc/blobs/' in f['figure_link'])
                print(f"Direct CDN URLs: {cdn_urls}/{len(figure_data)} ({cdn_urls/len(figure_data)*100:.1f}%)")
                
                # Show sample URLs
                print(f"\n📋 Sample figure URLs:")
                for i, f in enumerate(figure_data[:3], 1):
                    url = f.get('figure_link', 'No URL')
                    url_type = "🎯 CDN" if 'cdn.ncbi.nlm.nih.gov/pmc/blobs/' in url else "📄 PMC"
                    print(f"   {i}. {url_type}: {url}")
            
            print(f"Output file: {output_file}")
            print(f"Session directory: {session_dir}")
        else:
            print("❌ No figures were extracted")
            logger.warning("No figures were extracted")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        if 'logger' in locals():
            logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()