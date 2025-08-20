"""
Case Reports Retriever - NCBI PMC Integration
"""

import requests
import xml.etree.ElementTree as ET
import time
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache

from .config import Config

class CaseReportsRetriever:
    """Retrieves case reports from NCBI PMC"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseReportsAnalysis/1.0',
            'Accept': 'application/xml'
        })
    
    def get_case_reports_by_date_range(self, start_date: str, end_date: str, max_papers: int) -> List[Dict[str, Any]]:
        """
        Retrieve case reports within a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_papers: Maximum number of papers to retrieve
        
        Returns:
            List of case report dictionaries
        """
        
        # Construct search query
        query = f'"case report"[ti] AND open access[filter] AND ("{start_date}"[PDAT]:"{end_date}"[PDAT])'
        
        print(f"   🔍 Query: {query}")
        
        # Search for PMCIDs
        pmcids = self._search_pmc(query, max_papers)
        
        if not pmcids:
            print("   ❌ No PMCIDs found")
            return []
        
        print(f"   ✅ Found {len(pmcids)} PMCIDs")
        
        # Get detailed metadata for each PMCID
        case_reports = []
        
        for i, pmcid in enumerate(pmcids, 1):
            print(f"      📄 [{i}/{len(pmcids)}] Processing PMC{pmcid}")
            
            try:
                metadata = self._get_paper_metadata(pmcid)
                if metadata:
                    case_reports.append(metadata)
                    
            except Exception as e:
                print(f"         ❌ Error processing PMC{pmcid}: {e}")
                continue
            
            # Rate limiting
            time.sleep(self.config.delay_between_requests)
        
        return case_reports
    
    def _search_pmc(self, query: str, max_results: int) -> List[str]:
        """Search PMC and return list of PMCIDs"""
        
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        
        params = {
            "db": "pmc",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "email": self.config.email,
        }
        
        if self.config.ncbi_api_key:
            params["api_key"] = self.config.ncbi_api_key
        
        try:
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            pmcids = [id_elem.text for id_elem in root.findall(".//Id")]
            
            return pmcids
            
        except Exception as e:
            print(f"         ❌ Search error: {e}")
            return []
    
    def _get_paper_metadata(self, pmcid: str) -> Optional[Dict[str, Any]]:
        """Get detailed metadata for a PMCID"""
        
        # Get basic metadata from esummary
        summary_data = self._get_summary_metadata(pmcid)
        
        # Get abstract and detailed info
        detailed_data = self._get_detailed_metadata(pmcid)
        
        # Combine data
        if summary_data:
            summary_data.update(detailed_data)
            return summary_data
        
        return None
    
    def _get_summary_metadata(self, pmcid: str) -> Optional[Dict[str, Any]]:
        """Get summary metadata from esummary"""
        
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        
        params = {
            "db": "pmc",
            "id": pmcid,
            "retmode": "xml",
            "email": self.config.email,
        }
        
        if self.config.ncbi_api_key:
            params["api_key"] = self.config.ncbi_api_key
        
        try:
            response = self.session.get(summary_url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            title = root.findtext(".//Item[@Name='Title']") or ""
            source = root.findtext(".//Item[@Name='Source']") or ""
            full_journal = root.findtext(".//Item[@Name='FullJournalName']") or ""
            pub_date = root.findtext(".//Item[@Name='PubDate']") or ""
            
            # Extract PMID if available
            pmid = self._extract_pmid_from_summary(root)
            
            return {
                'pmcid': f"PMC{pmcid}",
                'pmid': pmid or "",
                'title': title,
                'journal': full_journal or source,
                'pub_date': pub_date,
                'year': self._extract_year_from_date(pub_date),
                'pmc_url': f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/",
                'pubmed_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            }
            
        except Exception as e:
            print(f"         ❌ Summary error: {e}")
            return None
    
    @lru_cache(maxsize=100)
    def _get_detailed_metadata(self, pmcid: str) -> Dict[str, Any]:
        """Get detailed metadata including abstract from efetch (cached)"""
        
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        
        params = {
            "db": "pmc",
            "id": pmcid,
            "retmode": "xml",
            "email": self.config.email
        }
        
        if self.config.ncbi_api_key:
            params["api_key"] = self.config.ncbi_api_key
        
        try:
            response = self.session.get(efetch_url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Extract abstract
            abstract = self._extract_abstract(root)
            
            return {
                'abstract': abstract
            }
            
        except Exception as e:
            print(f"         ⚠️  Detailed metadata error: {e}")
            return {'abstract': 'Abstract not available'}
    
    def _extract_pmid_from_summary(self, root: ET.Element) -> Optional[str]:
        """Extract PMID from summary XML"""
        
        article_ids = root.findtext(".//Item[@Name='ArticleIds']") or ""
        
        # Look for PMID pattern
        pmid_match = re.search(r'pmid[:\s]*(\d+)', article_ids, re.IGNORECASE)
        if pmid_match:
            return pmid_match.group(1)
        
        return None
    
    def _extract_year_from_date(self, pub_date: str) -> Optional[int]:
        """Extract year from publication date"""
        
        if not pub_date:
            return None
        
        year_match = re.search(r'(\d{4})', pub_date)
        if year_match:
            return int(year_match.group(1))
        
        return None
    
    def _extract_abstract(self, root: ET.Element) -> str:
        """Extract abstract from PMC XML"""
        
        # Try different abstract patterns
        abstract_patterns = [
            ".//abstract",
            ".//Abstract",
            ".//sec[@sec-type='abstract']",
            ".//abstract-group"
        ]
        
        for pattern in abstract_patterns:
            abstracts = root.findall(pattern)
            for abstract in abstracts:
                # Get all text from the abstract element
                abstract_text = ''.join(abstract.itertext()).strip()
                if abstract_text and len(abstract_text) > 50:
                    # Clean up whitespace
                    abstract_text = re.sub(r'\s+', ' ', abstract_text)
                    return abstract_text
        
        return "Abstract not available"
    
    def get_example_case_reports(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get example case reports for testing"""
        
        # Use recent case reports query
        query = '"case report"[ti] AND open access[filter]'
        
        print(f"   🔍 Getting {count} example case reports")
        
        # Search for PMCIDs
        pmcids = self._search_pmc(query, count)
        
        if not pmcids:
            return []
        
        # Get metadata
        case_reports = []
        
        for i, pmcid in enumerate(pmcids, 1):
            print(f"      📄 [{i}/{len(pmcids)}] Processing PMC{pmcid}")
            
            try:
                metadata = self._get_paper_metadata(pmcid)
                if metadata:
                    case_reports.append(metadata)
                    
            except Exception as e:
                print(f"         ❌ Error: {e}")
                continue
            
            time.sleep(self.config.delay_between_requests)
        
        return case_reports