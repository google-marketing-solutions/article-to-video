import unittest
import pipeline


class ConcreteStep(pipeline.BaseStep[[str], str]):

  def process(self, input_str: str) -> str:
    return input_str.lower()


class BaseStepTest(unittest.TestCase):

  def test_callable_executes_process(self):
    step = ConcreteStep()
    self.assertEqual(step("HELLO"), "hello")


def remove_chars(input_str: str, target_char: str):
  return input_str.replace(target_char, "")


class PipelineTest(unittest.TestCase):

  def test_init_with_no_steps(self):
    p = pipeline.Pipeline()
    self.assertEqual(p.steps, [])

  def test_init_with_steps(self):
    p = pipeline.Pipeline([str.lower])
    self.assertEqual(p.steps, [str.lower])

  def test_add_steps_extends_steps(self):
    p = pipeline.Pipeline([str.lower])
    p.add_steps(str.upper)
    self.assertEqual(p.steps, [str.lower, str.upper])

  def test_add_steps_returns_self(self):
    p = pipeline.Pipeline([str.lower])
    self.assertEqual(p.add_steps(str.upper), p)

  def test_process_executes_chain(self):
    p = pipeline.Pipeline[[str], list[str]]([str.lower, str.split])
    self.assertEqual(p.process("HELLO WORLD"), ["hello", "world"])

  def test_process_supports_kwargs(self):
    p = pipeline.Pipeline[[str], list[str]]([remove_chars, str.lower])
    self.assertEqual(p.process("HELLO WORLD", target_char="H"), "ello world")

  def test_process_can_unpack_args_class(self):
    p = pipeline.Pipeline[[str], list[str]]([
        lambda s: pipeline.Args(str.lower(s), target_char="h"),
        remove_chars,
    ])
    self.assertEqual(p.process("HELLO WORLD"), "ello world")


if __name__ == "__main__":
  unittest.main()
