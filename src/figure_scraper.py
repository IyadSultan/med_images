"""
Figure Scraper - PMC Figure and Caption Extraction
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from .config import Config

class FigureScraper:
    """Scrapes figures and captions from PMC papers"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_figures(self, pmcid: str) -> List[Dict[str, Any]]:
        """
        Scrape all figures from a PMC paper
        
        Args:
            pmcid: PMC identifier (with or without PMC prefix)
        
        Returns:
            List of figure dictionaries
        """
        
        pmcid = self._normalize_pmcid(pmcid)
        paper_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
        
        try:
            response = self.session.get(paper_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find figure elements
            figures = self._find_figure_elements(soup)
            
            # Process each figure
            figure_data = []
            
            for i, fig_elem in enumerate(figures, 1):
                try:
                    figure_info = self._extract_figure_info(fig_elem, pmcid, i)
                    if figure_info:
                        figure_data.append(figure_info)
                        
                except Exception as e:
                    print(f"         ⚠️  Error processing figure {i}: {e}")
                    continue
            
            return figure_data
            
        except Exception as e:
            print(f"         ❌ Error scraping figures from {pmcid}: {e}")
            return []
    
    def _normalize_pmcid(self, pmcid: str) -> str:
        """Normalize PMC ID to PMC format"""
        pmcid = str(pmcid).strip()
        if not pmcid.startswith('PMC'):
            pmcid = f'PMC{pmcid}'
        return pmcid
    
    def _find_figure_elements(self, soup: BeautifulSoup) -> List:
        """Find all figure elements on the page"""
        
        figure_selectors = [
            'div.fig',
            'figure',
            '.fig-panel',
            '.boxed-text figure',
            '[id^="F"]'  # IDs starting with F
        ]
        
        figures = []
        seen_ids = set()
        
        for selector in figure_selectors:
            elements = soup.select(selector)
            
            for elem in elements:
                # Generate unique identifier
                elem_id = elem.get('id') or f"fig_{len(figures)}"
                
                if elem_id not in seen_ids:
                    seen_ids.add(elem_id)
                    figures.append(elem)
        
        return figures
    
    def _extract_figure_info(self, fig_elem, pmcid: str, fig_number: int) -> Optional[Dict[str, Any]]:
        """Extract information from a single figure element"""
        
        # Extract figure ID
        fig_id = fig_elem.get('id') or f"figure_{fig_number}"
        
        # Extract figure label/title
        label = self._extract_figure_label(fig_elem, fig_number)
        
        # Extract caption
        caption = self._extract_figure_caption(fig_elem)
        
        # Extract direct CDN image URL (this is the most important part)
        cdn_image_url = self._get_cdn_image_url(fig_elem, pmcid, fig_id)
        
        # Generate PMC figure page URL as fallback
        pmc_figure_page_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/figure/{fig_id}/"
        
        # Only return if we have meaningful content
        if caption or cdn_image_url:
            return {
                'figure_id': fig_id,
                'label': label,
                'caption': caption,
                'image_url': cdn_image_url or pmc_figure_page_url,  # Prefer CDN URL
                'figure_url': cdn_image_url or pmc_figure_page_url  # Use CDN URL as figure link
            }
        
        return None
    
    def _get_cdn_image_url(self, fig_elem, pmcid: str, fig_id: str) -> str:
        """Get the direct CDN image URL - this is the key method"""
        
        # First try to find img tag within the figure element
        img_elem = fig_elem.find('img')
        if img_elem:
            src = img_elem.get('src') or img_elem.get('data-src')
            if src and self._is_cdn_url(src):
                return self._normalize_url(src)
        
        # If not found in figure element, scrape from figure page
        return self._scrape_cdn_url_from_figure_page(pmcid, fig_id)
    
    def _scrape_cdn_url_from_figure_page(self, pmcid: str, fig_id: str) -> str:
        """Scrape the CDN URL from the PMC figure page"""
        
        figure_page_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/figure/{fig_id}/"
        
        print(f"         🔍 Scraping CDN URL from: {figure_page_url}")
        
        try:
            time.sleep(self.config.delay_between_requests * 0.3)
            response = self.session.get(figure_page_url, timeout=15)
            
            if response.status_code != 200:
                print(f"         ❌ Figure page returned status {response.status_code}")
                return ""
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Enhanced selectors specifically for CDN URLs
            cdn_selectors = [
                # Direct CDN image selectors (highest priority)
                'img[src*="cdn.ncbi.nlm.nih.gov/pmc/blobs/"]',
                'img[src*="/pmc/blobs/"]',
                
                # Figure-specific selectors
                'img.figure-image',
                '.figure-viewer img',
                '.fig-panel img',
                
                # Additional PMC selectors
                '.figure-content img',
                '.fig-main img',
                'img[src*="blobs"]',
                
                # General CDN selectors
                'img[src*="cdn.ncbi.nlm.nih.gov"]',
                
                # Fallback selectors
                '.fig img[src*=".jpg"]',
                '.fig img[src*=".png"]',
                'img[alt*="Figure"]',
                'img[alt*="Fig"]'
            ]
            
            for selector in cdn_selectors:
                img_tags = soup.select(selector)
                for img_tag in img_tags:
                    src = img_tag.get('src')
                    if src:
                        normalized_url = self._normalize_url(src)
                        if self._is_cdn_url(normalized_url):
                            print(f"         ✅ Found CDN URL: {normalized_url}")
                            return normalized_url
                        elif 'ncbi.nlm.nih.gov' in normalized_url and any(ext in normalized_url.lower() for ext in ['.jpg', '.jpeg', '.png']):
                            print(f"         📎 Found NCBI image URL: {normalized_url}")
                            return normalized_url
            
            # Debug: Show what images were found
            all_imgs = soup.find_all('img')
            print(f"         🔍 Found {len(all_imgs)} images on page")
            for i, img in enumerate(all_imgs[:3], 1):  # Show first 3
                src = img.get('src', 'No src')
                alt = img.get('alt', 'No alt')
                print(f"         📷 Image {i}: {src[:60]}... (alt: {alt[:30]}...)")
            
            print(f"         ❌ No suitable CDN URL found on figure page")
            return ""
            
        except Exception as e:
            print(f"         ❌ Error scraping figure page: {e}")
            return ""
    
    def _is_cdn_url(self, url: str) -> bool:
        """Check if URL is a direct CDN URL (not just PMC page)"""
        if not url:
            return False
        
        # Must be a direct CDN URL with blobs path
        cdn_patterns = [
            'cdn.ncbi.nlm.nih.gov/pmc/blobs/',
            'ncbi.nlm.nih.gov/pmc/blobs/'
        ]
        
        # Must contain image extension
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        has_cdn_pattern = any(pattern in url for pattern in cdn_patterns)
        has_image_extension = any(ext in url.lower() for ext in image_extensions)
        
        return has_cdn_pattern and has_image_extension
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to proper format"""
        if not url:
            return ""
        
        url = url.strip()
        
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"https://www.ncbi.nlm.nih.gov{url}"
        elif url.startswith('http'):
            return url
        else:
            return f"https://www.ncbi.nlm.nih.gov/{url}"
    
    def _extract_figure_label(self, fig_elem, fig_number: int) -> str:
        """Extract figure label/title"""
        
        label_selectors = [
            '.fig-label',
            '.figure-title',
            '.fig-title',
            'strong',
            '.caption-title',
            'h3',
            'h4'
        ]
        
        for selector in label_selectors:
            label_elem = fig_elem.select_one(selector)
            if label_elem:
                text = label_elem.get_text().strip()
                if text and len(text) < 200:  # Reasonable label length
                    return text
        
        # Fallback to generic label
        return f"Figure {fig_number}"
    
    def _extract_figure_caption(self, fig_elem) -> str:
        """Extract figure caption"""
        
        caption_selectors = [
            '.fig-caption',
            'figcaption',
            '.caption',
            '.figure-caption',
            '.caption-text'
        ]
        
        for selector in caption_selectors:
            caption_elem = fig_elem.select_one(selector)
            if caption_elem:
                text = caption_elem.get_text().strip()
                if len(text) > 10:  # Minimum caption length
                    # Clean up whitespace
                    text = re.sub(r'\s+', ' ', text)
                    return text
        
        # Try looking in sibling elements
        next_sibling = fig_elem.find_next_sibling()
        if next_sibling:
            sibling_text = next_sibling.get_text().strip()
            if sibling_text and len(sibling_text) > 20:
                return re.sub(r'\s+', ' ', sibling_text)
        
        return ""
    
        return ""
    
    def get_figure_stats(self, figures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about extracted figures"""
        
        total_figures = len(figures)
        figures_with_captions = sum(1 for f in figures if f.get('caption'))
        figures_with_images = sum(1 for f in figures if f.get('image_url'))
        
        # Check CDN URL success rate
        cdn_urls = sum(1 for f in figures if f.get('figure_url') and self._is_cdn_url(f['figure_url']))
        
        avg_caption_length = 0
        if figures_with_captions > 0:
            caption_lengths = [len(f['caption']) for f in figures if f.get('caption')]
            avg_caption_length = sum(caption_lengths) / len(caption_lengths)
        
        return {
            'total_figures': total_figures,
            'figures_with_captions': figures_with_captions,
            'figures_with_images': figures_with_images,
            'cdn_urls_extracted': cdn_urls,
            'avg_caption_length': round(avg_caption_length, 1),
            'caption_coverage': round(figures_with_captions / max(1, total_figures) * 100, 1),
            'image_coverage': round(figures_with_images / max(1, total_figures) * 100, 1),
            'cdn_success_rate': round(cdn_urls / max(1, total_figures) * 100, 1)
        }