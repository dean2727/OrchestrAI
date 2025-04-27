from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Literal
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from dataclasses import asdict, dataclass, field
from typing_extensions import TypedDict

@dataclass
class Evaluation:
    """An evaluation represents a criterion for evaluating a scenario.

    Attributes:
        name (str): Name of the evaluation criterion
        prompt (str): Prompt to evaluate the scenario
    """
    name: str
    prompt: str

@dataclass
class Scenario:
    """A scenario represents a specific test case with a name, prompt, and associated evaluations.

    Attributes:
        name (str): The name of the scenario
        prompt (str): The system prompt used for this scenario
        evaluations (List[Evaluation]): List of evaluations performed for this scenario
    """
    name: str
    prompt: str
    evaluations: List[Evaluation] = field(default_factory=list)

class EvaluationResult(BaseModel):
    name: str
    passed: bool
    reason: str

class EvaluationResponse(BaseModel):
    evaluation_results: List[EvaluationResult]
    extra_data: Dict[str, Any]

class EvaluationResults(BaseModel):
    results: List[EvaluationResult]

class BaseEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam], stereo_recording_url: str) -> Optional[EvaluationResponse]:
        raise NotImplementedError
    
@dataclass
class Agent:
    """An agent represents a conversational entity with a name, system prompt, and voice configuration.

    Attributes:
        name (str): The name of the agent
        prompt (str): The system prompt that defines the agent's behavior and role
        voice_id (str): The cartesia voice id for the agent (defaults to a british lady)
    """
    name: str
    prompt: str

@dataclass
class Test:
    """A test represents a scenario and an agent to test the scenario with

    Attributes:
        scenario (Scenario): The scenario to test
        agent (Agent): The agent to test with
    """
    scenario: Scenario
    agent: Agent

@dataclass
class TestResult():
    """Result of a test.

    Attributes:
        test (Test): The test that was run
        evaluation_results (Optional[EvaluationResponse]): The evaluation results of the test
        transcript (List[ChatCompletionMessageParam]): The transcript of the test
        stereo_recording_url (str): The URL of the stereo recording of the test
        error (str | None): The error that occurred during the test
    """
    test: Test
    evaluation_results: Optional[EvaluationResponse]
    transcript: List[ChatCompletionMessageParam]
    stereo_recording_url: str
    error: str | None = None

@dataclass
class BaseTelemetryEvent(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def properties(self) -> Dict[str, Any]:
		return {k: v for k, v in asdict(self).items() if k != 'name'}

@dataclass
class RunTestTelemetryEvent(BaseTelemetryEvent):
    test: Test
    name: str = 'run_test'

@dataclass
class TestResultsTelemetryEvent(BaseTelemetryEvent):
    test_results: List[TestResult]
    name: str = 'test_results'

class CallStatus(TypedDict):
    status: Literal["in_progress", "completed", "error"]
    transcript: Optional[List[ChatCompletionMessageParam]]
    stereo_recording_url: Optional[str]
    error: Optional[str]