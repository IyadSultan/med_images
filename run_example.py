#!/usr/bin/env python3
"""
Quick Start Example for Case Reports Pipeline

This script provides easy examples to get started with the pipeline.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_requirements():
    """Check if required packages are installed"""
    
    required_packages = ['requests', 'beautifulsoup4', 'pandas']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    return True

def check_api_keys():
    """Check API key configuration"""
    
    ncbi_email = os.getenv('NCBI_EMAIL', '').strip()
    ncbi_api_key = os.getenv('NCBI_API_KEY', '').strip()
    openai_api_key = os.getenv('OPENAI_API_KEY', '').strip()
    
    print("🔑 API Configuration:")
    
    if ncbi_email and '@' in ncbi_email:
        print(f"   ✅ NCBI Email: {ncbi_email}")
    else:
        print("   ❌ NCBI Email: Not set (required)")
        print("      Set with: export NCBI_EMAIL='your-email@example.com'")
    
    if ncbi_api_key:
        print("   ✅ NCBI API Key: Configured")
    else:
        print("   ⚠️  NCBI API Key: Not set (recommended)")
        print("      Get one at: https://ncbiinsights.ncbi.nlm.nih.gov/")
    
    if openai_api_key:
        print("   ✅ OpenAI API Key: Configured (MCQ generation enabled)")
    else:
        print("   ⚠️  OpenAI API Key: Not set (MCQ generation disabled)")
        print("      Get one at: https://platform.openai.com/api-keys")
    
    return bool(ncbi_email and '@' in ncbi_email)

def run_example():
    """Run example pipeline"""
    
    print("🏥 Case Reports Pipeline - Quick Start")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Check API keys
    if not check_api_keys():
        print("\n❌ Please set NCBI_EMAIL before continuing")
        return False
    
    print("\n🚀 Running example with 5 case reports...")
    
    # Import after checking requirements
    try:
        from src.config import Config
        from src.case_reports_retriever import CaseReportsRetriever
        from src.figure_scraper import FigureScraper
        from src.mcq_generator import MCQGenerator
        from src.utils import create_output_directories, save_results_csv
        from datetime import datetime
        from pathlib import Path
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    try:
        # Setup configuration
        config = Config(
            email=os.getenv('NCBI_EMAIL'),
            ncbi_api_key=os.getenv('NCBI_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            max_papers=5  # Small example
        )
        
        # Create output directories
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_dir = Path("outputs") / f"example_session_{timestamp}"
        directories = create_output_directories(session_dir)
        
        print(f"📁 Output directory: {session_dir}")
        
        # Initialize components
        retriever = CaseReportsRetriever(config)
        scraper = FigureScraper(config)
        mcq_gen = MCQGenerator(config) if config.enable_mcq else None
        
        # Step 1: Get example case reports
        print(f"\n📋 Step 1: Getting example case reports...")
        case_reports = retriever.get_example_case_reports(count=5)
        
        if not case_reports:
            print("❌ No case reports found")
            return False
        
        print(f"✅ Found {len(case_reports)} case reports")
        
        # Step 2: Process figures
        print(f"\n🖼️  Step 2: Processing figures...")
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
                    'figure_link': figure['figure_url'],
                    'caption': figure['caption'],
                    'image_url': figure['image_url']
                }
                
                # Generate MCQ if enabled
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
                        'mcq_question': 'MCQ generation disabled',
                        'option_a': '', 'option_b': '', 'option_c': '', 'option_d': '', 'option_e': '',
                        'answer': '', 'commentary': '', 'subject': '', 'hashtags': '',
                        'difficulty_level': ''
                    })
                
                figure_data.append(combined_data)
        
        print(f"✅ Processed {len(figure_data)} figures")
        
        # Step 3: Save results
        print(f"\n💾 Step 3: Saving results...")
        
        if figure_data:
            output_file = save_results_csv(figure_data, directories['outputs'])
            
            print(f"\n🎉 Example completed successfully!")
            print(f"📊 Results: {len(case_reports)} papers, {len(figure_data)} figures")
            print(f"📁 Output file: {output_file}")
            print(f"📂 Session directory: {session_dir}")
            
            # Show sample data
            if figure_data:
                sample = figure_data[0]
                print(f"\n📋 Sample result:")
                print(f"   PMC: {sample['pmcid']}")
                print(f"   Title: {sample['title'][:60]}...")
                print(f"   Figure: {sample['figure_label']}")
                if sample.get('mcq_question') and sample['mcq_question'] != 'MCQ generation disabled':
                    print(f"   MCQ: {sample['mcq_question'][:60]}...")
            
            return True
        else:
            print("❌ No figures were extracted")
            return False
            
    except Exception as e:
        print(f"❌ Example failed: {e}")
        return False

def main():
    """Main function"""
    
    if run_example():
        print(f"\n✨ Next steps:")
        print(f"   1. Explore the output CSV file")
        print(f"   2. Try: python main.py --month 12 --year 2024")
        print(f"   3. Set OpenAI API key for MCQ generation")
        print(f"   4. Use --max_papers for larger datasets")
    else:
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Install requirements: pip install -r requirements.txt")
        print(f"   2. Set NCBI email: export NCBI_EMAIL='your-email@example.com'")
        print(f"   3. Check internet connection")
        print(f"   4. Try running main.py directly")

if __name__ == "__main__":
    main()