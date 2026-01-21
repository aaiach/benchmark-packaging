"""Pipeline module for step-based execution.

This module provides a scalable architecture for running multi-step pipelines
with dependency validation, file-based checkpointing, and flexible execution.

Example usage:
    # Run steps 1-3 from scratch
    uv run python main.py "lait d'avoine" --steps 1-3
    
    # Continue from existing run with step 4
    uv run python main.py --run-id 20260120_184854 --steps 4
    
    # Re-run steps 3-4 on existing run
    uv run python main.py --run-id 20260120_184854 --steps 3-4
"""
from .base import Step, Pipeline, PipelineContext, parse_steps_arg
from .steps import STEPS, get_step, list_steps

__all__ = [
    'Step',
    'Pipeline', 
    'PipelineContext',
    'parse_steps_arg',
    'STEPS',
    'get_step',
    'list_steps',
]
