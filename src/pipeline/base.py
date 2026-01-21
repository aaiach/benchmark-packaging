"""Base classes for the pipeline system.

Provides Step definitions and Pipeline orchestration with:
- Dependency validation
- File-based checkpointing
- Flexible step execution (ranges, single steps, resume)
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import re


@dataclass
class PipelineContext:
    """Context shared across pipeline steps.
    
    Attributes:
        category: Product category being processed
        category_slug: URL-safe version of category
        run_id: Unique identifier for this run (timestamp)
        country: Target country
        count: Number of products to discover
        output_dir: Directory for output files
        data: Shared data dictionary for passing results between steps
    """
    category: str
    category_slug: str
    run_id: str
    country: str
    count: int
    output_dir: Path
    data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_new(
        cls,
        category: str,
        country: str = "France",
        count: int = 30,
        output_dir: str = "output"
    ) -> "PipelineContext":
        """Create a new pipeline context with fresh run_id."""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        category_slug = category.replace(' ', '_').replace("'", '')
        return cls(
            category=category,
            category_slug=category_slug,
            run_id=run_id,
            country=country,
            count=count,
            output_dir=Path(output_dir),
        )
    
    @classmethod
    def from_run_id(
        cls,
        run_id: str,
        output_dir: str = "output"
    ) -> Optional["PipelineContext"]:
        """Load context from an existing run by finding its files.
        
        Returns None if the run_id doesn't exist.
        """
        output_path = Path(output_dir)
        
        # Find any file matching this run_id
        patterns = [
            f"*_discovered_{run_id}.json",
            f"*_scraped_{run_id}.json",
            f"*_with_images_{run_id}.json",
        ]
        
        for pattern in patterns:
            matches = list(output_path.glob(pattern))
            if matches:
                # Extract category from filename
                filename = matches[0].stem
                # Remove the suffix to get category
                for suffix in [f"_discovered_{run_id}", f"_scraped_{run_id}", f"_with_images_{run_id}"]:
                    if filename.endswith(suffix.replace(".json", "")):
                        category_slug = filename.replace(suffix.replace(".json", ""), "")
                        break
                else:
                    category_slug = filename.split("_")[0]
                
                return cls(
                    category=category_slug.replace('_', ' '),
                    category_slug=category_slug,
                    run_id=run_id,
                    country="France",  # Default, not stored in files
                    count=30,  # Default, not stored in files
                    output_dir=output_path,
                )
        
        return None


@dataclass
class Step:
    """Definition of a pipeline step.
    
    Attributes:
        number: Step number (1, 2, 3, ...)
        name: Short identifier (discovery, details, scraping, images)
        description: Human-readable description
        output_pattern: Pattern for output file (uses {category} and {run_id})
        requires: List of step numbers that must be completed first
        executor: Function that executes this step
    """
    number: int
    name: str
    description: str
    output_pattern: str
    requires: List[int] = field(default_factory=list)
    executor: Optional[Callable[[PipelineContext, Any], Any]] = None
    
    def get_output_file(self, ctx: PipelineContext) -> Path:
        """Get the output file path for this step."""
        filename = self.output_pattern.format(
            category=ctx.category_slug,
            run_id=ctx.run_id
        )
        return ctx.output_dir / filename
    
    def is_completed(self, ctx: PipelineContext) -> bool:
        """Check if this step has been completed (output file exists)."""
        return self.get_output_file(ctx).exists()
    
    def check_dependencies(
        self, 
        ctx: PipelineContext, 
        steps_registry: Dict[int, "Step"]
    ) -> Tuple[bool, Optional[str]]:
        """Check if all dependencies are satisfied.
        
        Returns:
            Tuple of (is_satisfied, error_message)
        """
        for req_num in self.requires:
            if req_num not in steps_registry:
                return False, f"Unknown dependency: step {req_num}"
            
            req_step = steps_registry[req_num]
            if not req_step.is_completed(ctx):
                return False, (
                    f"Step {self.number} ({self.name}) requires step {req_num} "
                    f"({req_step.name}) to be completed first. "
                    f"Missing file: {req_step.get_output_file(ctx)}"
                )
        
        return True, None


def parse_steps_arg(steps_arg: str, max_step: int) -> List[int]:
    """Parse the --steps argument into a list of step numbers.
    
    Supports formats:
        - "4" → [4]
        - "1-3" → [1, 2, 3]
        - "1,3,4" → [1, 3, 4]
        - "1-3,5" → [1, 2, 3, 5]
    
    Args:
        steps_arg: The steps argument string
        max_step: Maximum valid step number
        
    Returns:
        Sorted list of unique step numbers
        
    Raises:
        ValueError: If the format is invalid or step numbers are out of range
    """
    steps: Set[int] = set()
    
    parts = steps_arg.split(',')
    for part in parts:
        part = part.strip()
        
        if '-' in part:
            # Range: "1-3"
            match = re.match(r'^(\d+)-(\d+)$', part)
            if not match:
                raise ValueError(f"Invalid step range format: '{part}'")
            
            start, end = int(match.group(1)), int(match.group(2))
            if start > end:
                raise ValueError(f"Invalid range: {start} > {end}")
            
            for i in range(start, end + 1):
                if i < 1 or i > max_step:
                    raise ValueError(f"Step {i} is out of range (1-{max_step})")
                steps.add(i)
        else:
            # Single number: "4"
            if not part.isdigit():
                raise ValueError(f"Invalid step number: '{part}'")
            
            num = int(part)
            if num < 1 or num > max_step:
                raise ValueError(f"Step {num} is out of range (1-{max_step})")
            steps.add(num)
    
    return sorted(steps)


class Pipeline:
    """Orchestrates multi-step pipeline execution.
    
    Handles:
    - Step registration
    - Dependency validation
    - Sequential execution
    - Progress tracking
    """
    
    def __init__(self, steps: Dict[int, Step], config: Any = None):
        """Initialize the pipeline.
        
        Args:
            steps: Dictionary mapping step numbers to Step objects
            config: Optional configuration object
        """
        self.steps = steps
        self.config = config
        self.max_step = max(steps.keys()) if steps else 0
    
    def validate_execution_plan(
        self, 
        step_numbers: List[int], 
        ctx: PipelineContext
    ) -> Tuple[bool, List[str]]:
        """Validate that all requested steps can be executed.
        
        Checks:
        - All step numbers are valid
        - Dependencies are satisfied for each step
        
        Args:
            step_numbers: List of steps to execute (in order)
            ctx: Pipeline context
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[str] = []
        
        # Track which steps will be completed during execution
        will_be_completed: Set[int] = set()
        
        for step_num in step_numbers:
            if step_num not in self.steps:
                errors.append(f"Unknown step: {step_num}")
                continue
            
            step = self.steps[step_num]
            
            # Check dependencies
            for req_num in step.requires:
                if req_num in will_be_completed:
                    # Will be completed by a previous step in this run
                    continue
                
                req_step = self.steps.get(req_num)
                if not req_step:
                    errors.append(f"Step {step_num} depends on unknown step {req_num}")
                elif not req_step.is_completed(ctx):
                    errors.append(
                        f"Step {step_num} ({step.name}) requires step {req_num} "
                        f"({req_step.name}) to be completed first"
                    )
            
            will_be_completed.add(step_num)
        
        return len(errors) == 0, errors
    
    def run(
        self,
        step_numbers: List[int],
        ctx: PipelineContext,
        verbose: bool = True
    ) -> bool:
        """Execute the specified steps.
        
        Args:
            step_numbers: List of step numbers to execute (in order)
            ctx: Pipeline context
            verbose: Whether to print progress
            
        Returns:
            True if all steps completed successfully
        """
        # Validate first
        is_valid, errors = self.validate_execution_plan(step_numbers, ctx)
        if not is_valid:
            for error in errors:
                print(f"[!] {error}")
            return False
        
        # Ensure output directory exists
        ctx.output_dir.mkdir(exist_ok=True)
        
        # Execute steps
        for step_num in step_numbers:
            step = self.steps[step_num]
            
            if verbose:
                print(f"\n{'=' * 70}")
                print(f"STEP {step.number}: {step.description}")
                print("=" * 70)
            
            # Check if already completed
            if step.is_completed(ctx):
                if verbose:
                    print(f"[i] Step already completed. Re-running...")
            
            # Execute
            if step.executor:
                try:
                    result = step.executor(ctx, self.config)
                    ctx.data[f"step_{step_num}_result"] = result
                except Exception as e:
                    print(f"[!] Step {step_num} failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print(f"[!] No executor defined for step {step_num}")
                return False
            
            if verbose:
                output_file = step.get_output_file(ctx)
                if output_file.exists():
                    print(f"[✓] Output: {output_file}")
        
        return True
    
    def get_run_status(self, ctx: PipelineContext) -> Dict[int, bool]:
        """Get completion status for all steps in a run.
        
        Returns:
            Dictionary mapping step number to completion status
        """
        return {
            num: step.is_completed(ctx) 
            for num, step in self.steps.items()
        }
    
    def print_status(self, ctx: PipelineContext) -> None:
        """Print the status of all steps for a run."""
        print(f"\nRun: {ctx.run_id}")
        print(f"Category: {ctx.category}")
        print("-" * 50)
        
        status = self.get_run_status(ctx)
        for num in sorted(self.steps.keys()):
            step = self.steps[num]
            completed = "✓" if status[num] else "○"
            deps = f" (requires: {step.requires})" if step.requires else ""
            print(f"  [{completed}] Step {num}: {step.name}{deps}")
