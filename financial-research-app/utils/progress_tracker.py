# Progress Tracker
# Real-time progress tracking for research operations

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config.logging_config import get_logger

logger = get_logger('progress_tracker')

class ProgressTracker:
    """Track progress of multi-company research operations"""
    
    def __init__(self, total_items: int):
        """
        Initialize progress tracker
        
        Args:
            total_items: Total number of items to process
        """
        self.total_items = total_items
        self.completed_items = 0
        self.failed_items = 0
        self.in_progress_items = []
        self.start_time = time.time()
        self.item_details = {}  # Store details for each item
        
    def start_item(self, item_id: str, description: str = ""):
        """Mark an item as started"""
        self.in_progress_items.append(item_id)
        self.item_details[item_id] = {
            'status': 'in_progress',
            'description': description,
            'start_time': time.time(),
            'error': None
        }
        logger.info(f"Started: {item_id}")
    
    def complete_item(self, item_id: str):
        """Mark an item as completed"""
        if item_id in self.in_progress_items:
            self.in_progress_items.remove(item_id)
        
        self.completed_items += 1
        if item_id in self.item_details:
            self.item_details[item_id]['status'] = 'completed'
            self.item_details[item_id]['end_time'] = time.time()
        
        logger.info(f"Completed: {item_id} ({self.completed_items}/{self.total_items})")
    
    def fail_item(self, item_id: str, error: str = ""):
        """Mark an item as failed"""
        if item_id in self.in_progress_items:
            self.in_progress_items.remove(item_id)
        
        self.failed_items += 1
        if item_id in self.item_details:
            self.item_details[item_id]['status'] = 'failed'
            self.item_details[item_id]['error'] = error
            self.item_details[item_id]['end_time'] = time.time()
        
        logger.warning(f"Failed: {item_id} - {error}")
    
    def get_progress_percent(self) -> float:
        """Get current progress percentage"""
        if self.total_items == 0:
            return 100.0
        return (self.completed_items / self.total_items) * 100
    
    def get_eta_seconds(self) -> Optional[float]:
        """Calculate estimated time to completion"""
        if self.completed_items == 0:
            return None
        
        elapsed = time.time() - self.start_time
        avg_time_per_item = elapsed / self.completed_items
        remaining_items = self.total_items - self.completed_items
        
        return avg_time_per_item * remaining_items
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        processed = self.completed_items + self.failed_items
        if processed == 0:
            return 100.0
        return (self.completed_items / processed) * 100
    
    def print_progress(self):
        """Print formatted progress bar to console"""
        progress_pct = self.get_progress_percent()
        bar_length = 40
        filled = int(bar_length * progress_pct / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n[{bar}] {progress_pct:.1f}% Complete ({self.completed_items}/{self.total_items})")
        
        # Show in-progress items
        if self.in_progress_items:
            for item_id in self.in_progress_items[:3]:  # Show first 3
                desc = self.item_details.get(item_id, {}).get('description', item_id)
                print(f"⏳ {desc} - In progress...")
        
        # Show recently completed
        completed_items = [k for k, v in self.item_details.items() if v['status'] == 'completed']
        for item_id in completed_items[-3:]:  # Show last 3 completed
            desc = self.item_details[item_id].get('description', item_id)
            print(f"✓ {desc} - Completed")
        
        # Show failed items
        failed_items = [k for k, v in self.item_details.items() if v['status'] == 'failed']
        for item_id in failed_items[-3:]:  # Show last 3 failed
            desc = self.item_details[item_id].get('description', item_id)
            error = self.item_details[item_id].get('error', 'Unknown error')
            print(f"✗ {desc} - Failed: {error}")
        
        # Show ETA
        eta_seconds = self.get_eta_seconds()
        if eta_seconds:
            eta_str = str(timedelta(seconds=int(eta_seconds)))
            success_rate = self.get_success_rate()
            print(f"\nETA: {eta_str} | Success Rate: {success_rate:.1f}%")
    
    def get_summary(self) -> Dict:
        """Get comprehensive progress summary"""
        elapsed = time.time() - self.start_time
        eta = self.get_eta_seconds()
        
        return {
            'total_items': self.total_items,
            'completed': self.completed_items,
            'failed': self.failed_items,
            'in_progress': len(self.in_progress_items),
            'progress_percent': round(self.get_progress_percent(), 2),
            'success_rate': round(self.get_success_rate(), 2),
            'elapsed_seconds': round(elapsed, 2),
            'eta_seconds': round(eta, 2) if eta else None,
            'items': self.item_details
        }
