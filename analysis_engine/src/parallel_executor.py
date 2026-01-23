"""Parallel execution orchestrator for API calls with rate limiting.

This module provides a reusable ParallelExecutor class that handles:
- Concurrent execution with configurable limits per provider
- Rate limiting to prevent hitting API quotas
- Progress reporting with callbacks
- Error handling and collection
- Same output format as sequential execution

Supports multiple providers with different rate limits:
- OpenAI (Tier 5): 30,000 RPM - very high, can use 20+ concurrent
- Gemini: Conservative 15-60 RPM depending on tier
- Firecrawl: No concurrency (sequential only)

Usage:
    executor = ParallelExecutor(
        provider="openai",
        max_concurrent=10,
        rate_limit_rpm=1000
    )
    
    results = await executor.execute(
        items=products,
        process_func=process_product,
        progress_callback=on_progress
    )
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import (
    Any, 
    Callable, 
    Coroutine, 
    Dict, 
    Generic, 
    List, 
    Optional, 
    TypeVar,
    Union
)
from enum import Enum


# =============================================================================
# Type Variables for Generic Support
# =============================================================================

T = TypeVar('T')  # Input item type
R = TypeVar('R')  # Result type


# =============================================================================
# Provider Configuration
# =============================================================================

class Provider(Enum):
    """Supported API providers with their default limits."""
    OPENAI = "openai"
    OPENAI_MINI = "openai_mini"
    GEMINI = "gemini"
    GEMINI_VISION = "gemini_vision"
    FIRECRAWL = "firecrawl"


@dataclass
class ProviderLimits:
    """Rate limit configuration for a provider."""
    max_concurrent: int  # Maximum concurrent requests
    rate_limit_rpm: int  # Requests per minute limit
    min_delay_seconds: float = 0.0  # Minimum delay between requests
    
    @property
    def delay_between_requests(self) -> float:
        """Calculate delay between requests to stay within RPM limit."""
        if self.rate_limit_rpm <= 0:
            return self.min_delay_seconds
        # Add 10% buffer to RPM calculation
        rpm_delay = 60.0 / (self.rate_limit_rpm * 0.9)
        return max(rpm_delay, self.min_delay_seconds)


# Default limits per provider
# These are conservative defaults that can be overridden
DEFAULT_PROVIDER_LIMITS: Dict[Provider, ProviderLimits] = {
    # OpenAI Tier 5: 30,000 RPM - can handle high concurrency
    Provider.OPENAI: ProviderLimits(
        max_concurrent=15,
        rate_limit_rpm=1000,  # Conservative: use 1000 of 30000
        min_delay_seconds=0.05
    ),
    Provider.OPENAI_MINI: ProviderLimits(
        max_concurrent=15,
        rate_limit_rpm=1000,
        min_delay_seconds=0.05
    ),
    # Gemini: Upgraded tier - 10 concurrent, 60 RPM
    Provider.GEMINI: ProviderLimits(
        max_concurrent=10,
        rate_limit_rpm=60,
        min_delay_seconds=0.2
    ),
    Provider.GEMINI_VISION: ProviderLimits(
        max_concurrent=10,
        rate_limit_rpm=60,
        min_delay_seconds=0.2
    ),
    # Firecrawl: Up to 5 concurrent (upgraded subscription)
    Provider.FIRECRAWL: ProviderLimits(
        max_concurrent=5,
        rate_limit_rpm=60,
        min_delay_seconds=0.1  # Minimal delay since scraping different domains
    ),
}


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class ExecutionResult(Generic[R]):
    """Result of executing a single item."""
    index: int
    success: bool
    result: Optional[R] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class BatchResult(Generic[R]):
    """Result of executing a batch of items."""
    results: List[ExecutionResult[R]] = field(default_factory=list)
    total_items: int = 0
    successful_count: int = 0
    failed_count: int = 0
    total_duration_seconds: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.successful_count / self.total_items) * 100
    
    def get_successful_results(self) -> List[R]:
        """Get only successful results in order."""
        return [r.result for r in sorted(self.results, key=lambda x: x.index) 
                if r.success and r.result is not None]
    
    def get_all_results_ordered(self) -> List[Optional[R]]:
        """Get all results in original order (None for failures)."""
        sorted_results = sorted(self.results, key=lambda x: x.index)
        return [r.result if r.success else None for r in sorted_results]


# =============================================================================
# Progress Callback Type
# =============================================================================

ProgressCallback = Callable[[int, int, str, Optional[str]], None]
# Args: (completed, total, status_message, item_identifier)


# =============================================================================
# Main ParallelExecutor Class
# =============================================================================

class ParallelExecutor(Generic[T, R]):
    """Orchestrates parallel execution of API calls with rate limiting.
    
    Features:
    - Configurable concurrency per provider
    - Rate limiting to prevent quota exhaustion
    - Progress callbacks for UI updates
    - Error handling with result collection
    - Maintains order of results
    
    Example:
        async def process_product(product: Product) -> ProductDetails:
            return await api.get_details(product)
        
        executor = ParallelExecutor(provider=Provider.OPENAI)
        batch_result = await executor.execute(
            items=products,
            process_func=process_product,
            get_item_id=lambda p: p.name
        )
        
        # Get results in original order
        details = batch_result.get_successful_results()
    """
    
    def __init__(
        self,
        provider: Provider,
        limits: Optional[ProviderLimits] = None,
        max_retries: int = 2,
        retry_delay_seconds: float = 1.0
    ):
        """Initialize the executor.
        
        Args:
            provider: API provider to use (determines default limits)
            limits: Optional custom limits (overrides defaults)
            max_retries: Maximum retries per item on failure
            retry_delay_seconds: Delay between retries
        """
        self.provider = provider
        self.limits = limits or DEFAULT_PROVIDER_LIMITS.get(
            provider, 
            ProviderLimits(max_concurrent=1, rate_limit_rpm=10)
        )
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        
        # Execution state
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._last_request_time: float = 0
        self._request_lock: Optional[asyncio.Lock] = None
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait if needed to respect rate limits."""
        if self._request_lock is None:
            self._request_lock = asyncio.Lock()
        
        async with self._request_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            delay_needed = self.limits.delay_between_requests - elapsed
            
            if delay_needed > 0:
                await asyncio.sleep(delay_needed)
            
            self._last_request_time = time.time()
    
    async def _execute_single(
        self,
        index: int,
        item: T,
        process_func: Callable[[T], Coroutine[Any, Any, R]],
        get_item_id: Optional[Callable[[T], str]] = None
    ) -> ExecutionResult[R]:
        """Execute a single item with retries.
        
        Args:
            index: Item index for ordering
            item: Item to process
            process_func: Async function to process the item
            get_item_id: Optional function to get item identifier for logging
            
        Returns:
            ExecutionResult with success/failure and result
        """
        item_id = get_item_id(item) if get_item_id else f"item_{index}"
        start_time = time.time()
        last_error: Optional[str] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Wait for rate limit
                await self._wait_for_rate_limit()
                
                # Acquire semaphore for concurrency control
                async with self._semaphore:
                    result = await process_func(item)
                    
                    duration = time.time() - start_time
                    return ExecutionResult(
                        index=index,
                        success=True,
                        result=result,
                        duration_seconds=duration
                    )
                    
            except Exception as e:
                last_error = str(e)
                
                if attempt < self.max_retries:
                    # Retry after delay
                    await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
                    continue
        
        # All retries failed
        duration = time.time() - start_time
        return ExecutionResult(
            index=index,
            success=False,
            error=last_error,
            duration_seconds=duration
        )
    
    async def execute(
        self,
        items: List[T],
        process_func: Callable[[T], Coroutine[Any, Any, R]],
        get_item_id: Optional[Callable[[T], str]] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> BatchResult[R]:
        """Execute processing for all items in parallel.
        
        Args:
            items: List of items to process
            process_func: Async function to process each item
            get_item_id: Optional function to get item identifier
            progress_callback: Optional callback for progress updates
            
        Returns:
            BatchResult containing all results
        """
        if not items:
            return BatchResult(total_items=0)
        
        # Initialize semaphore for this batch
        self._semaphore = asyncio.Semaphore(self.limits.max_concurrent)
        self._request_lock = asyncio.Lock()
        self._last_request_time = 0
        
        total = len(items)
        start_time = time.time()
        results: List[ExecutionResult[R]] = []
        completed = 0
        
        # Report start
        if progress_callback:
            progress_callback(0, total, "Starting...", None)
        
        # Create tasks for all items
        tasks = [
            self._execute_single(i, item, process_func, get_item_id)
            for i, item in enumerate(items)
        ]
        
        # Execute with progress tracking
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1
            
            # Report progress
            if progress_callback:
                item_id = get_item_id(items[result.index]) if get_item_id else None
                status = "✓" if result.success else "✗"
                progress_callback(completed, total, status, item_id)
        
        # Calculate summary
        total_duration = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        return BatchResult(
            results=results,
            total_items=total,
            successful_count=successful,
            failed_count=failed,
            total_duration_seconds=total_duration
        )
    
    def execute_sync(
        self,
        items: List[T],
        process_func: Callable[[T], Coroutine[Any, Any, R]],
        get_item_id: Optional[Callable[[T], str]] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> BatchResult[R]:
        """Synchronous wrapper for execute().
        
        Use this when calling from synchronous code.
        """
        return asyncio.run(self.execute(
            items=items,
            process_func=process_func,
            get_item_id=get_item_id,
            progress_callback=progress_callback
        ))


# =============================================================================
# Convenience Functions
# =============================================================================

def create_executor(
    provider: Union[Provider, str],
    max_concurrent: Optional[int] = None,
    rate_limit_rpm: Optional[int] = None
) -> ParallelExecutor:
    """Create an executor with optional custom limits.
    
    Args:
        provider: Provider name or enum
        max_concurrent: Override max concurrent requests
        rate_limit_rpm: Override rate limit
        
    Returns:
        Configured ParallelExecutor
    """
    if isinstance(provider, str):
        provider = Provider(provider)
    
    # Get default limits
    default_limits = DEFAULT_PROVIDER_LIMITS.get(
        provider,
        ProviderLimits(max_concurrent=1, rate_limit_rpm=10)
    )
    
    # Apply overrides
    limits = ProviderLimits(
        max_concurrent=max_concurrent or default_limits.max_concurrent,
        rate_limit_rpm=rate_limit_rpm or default_limits.rate_limit_rpm,
        min_delay_seconds=default_limits.min_delay_seconds
    )
    
    return ParallelExecutor(provider=provider, limits=limits)


def run_parallel(
    items: List[T],
    process_func: Callable[[T], Coroutine[Any, Any, R]],
    provider: Union[Provider, str],
    get_item_id: Optional[Callable[[T], str]] = None,
    progress_callback: Optional[ProgressCallback] = None,
    max_concurrent: Optional[int] = None,
    rate_limit_rpm: Optional[int] = None
) -> BatchResult[R]:
    """Convenience function to run parallel execution.
    
    Args:
        items: Items to process
        process_func: Async processing function
        provider: API provider
        get_item_id: Optional item identifier function
        progress_callback: Optional progress callback
        max_concurrent: Optional concurrency override
        rate_limit_rpm: Optional rate limit override
        
    Returns:
        BatchResult with all results
    """
    executor = create_executor(
        provider=provider,
        max_concurrent=max_concurrent,
        rate_limit_rpm=rate_limit_rpm
    )
    
    return executor.execute_sync(
        items=items,
        process_func=process_func,
        get_item_id=get_item_id,
        progress_callback=progress_callback
    )


# =============================================================================
# Async-to-Sync Wrapper for Non-Async Functions
# =============================================================================

def wrap_sync_func(
    sync_func: Callable[[T], R]
) -> Callable[[T], Coroutine[Any, Any, R]]:
    """Wrap a synchronous function to be used with async executor.
    
    Args:
        sync_func: Synchronous function to wrap
        
    Returns:
        Async wrapper function
    """
    async def async_wrapper(item: T) -> R:
        # Run sync function in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_func, item)
    
    return async_wrapper


# =============================================================================
# Print Progress Helper
# =============================================================================

def create_print_progress(prefix: str = "") -> ProgressCallback:
    """Create a simple print-based progress callback.
    
    Args:
        prefix: Optional prefix for progress messages
        
    Returns:
        Progress callback function
    """
    def callback(completed: int, total: int, status: str, item_id: Optional[str]) -> None:
        item_str = f" {item_id}" if item_id else ""
        print(f"{prefix}[{completed:3}/{total}] {status}{item_str}")
    
    return callback
