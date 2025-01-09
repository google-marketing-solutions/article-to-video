"""Generic and base classes for creating pipelines."""

import abc
from typing import Any, Callable, Generic, ParamSpec, Self, TypeVar

P = ParamSpec("P", bound=tuple[Any, ...])

R = TypeVar("R")


class BaseStep(abc.ABC, Generic[P, R]):
  """Abstract generic base class for creating pipeline steps."""

  def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
    return self.process(*args, **kwargs)

  @abc.abstractmethod
  def process(self, *args: P.args, **kwargs: P.kwargs) -> R:
    pass


class Args(Generic[P]):
  """Simple wrapper for function arguments.

  For passing kwargs to intermediate pipeline steps.
  """

  def __init__(self, *args: P.args, **kwargs: P.kwargs):
    self.args = args
    self.kwargs = kwargs


class Pipeline(BaseStep[P, R]):
  """Generic Pipeline that can be used to chain Callables.

  Basic usage:
  >>> Pipeline[[str], list[str]]([
  >>>  str.lower,
  >>>  str.split,
  >>> ]).process("Hello World")
  ["hello", "world"]

  To pass kwargs to an intermediate step, wrap the result of the previous
  function in an Args object:
  >>> Pipeline[[str], list[str]]([
  >>>  lambda s: Args(str.lower(s), named_arg="ARG"),
  >>>  some_function_that_takes_kwargs,
  >>> ]).process("Hello World")

  Pipelines are Callable so a Pipeline can be included as a step in a Pipeline.
  """

  def __init__(self, steps: list[BaseStep] = None):
    self.steps = steps or []

  def add_steps(self, *steps: Callable[P, R]) -> Self:
    """Adds steps to the pipeline.

    The first step will receive arguments from the pipeline's process method.
    Each subsequent step will receive the return value of the step before it.

    Args:
      *steps: Individual steps, to be executed in order.

    Returns:
        Self
    """
    self.steps.extend(steps)
    return self

  def prepare_args(self, *args: P.args, **kwargs: P.kwargs):
    if args and kwargs:
      return (args, kwargs)
    else:
      return args or kwargs

  def process(self, *args: P.args, **kwargs: P.kwargs) -> R:
    """Execute the steps in the pipeline.

    Accepts any positional or keyword arguments, all of which are passed
    as the parameters to the first step in the pipeline.

    Args:
      *args: positional arguments
      *kwargs: keyword arguments

    Returns:
      The result from the last step in the pipeline.
    """
    step_args = Args(*args, **kwargs)
    for step in self.steps:
      result = step(*step_args.args, **step_args.kwargs)
      if not isinstance(result, Args):
        step_args = Args(result)
      else:
        step_args = result
    return result
