"""Tests for BaseAgent and specialist agents."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fu7ur3pr00f.agents.specialists.base import BaseAgent, KnowledgeResult, MemoryResult
from fu7ur3pr00f.agents.specialists.coach import CoachAgent
from fu7ur3pr00f.agents.specialists.orchestrator import OrchestratorAgent

# =============================================================================
# BaseAgent Tests
# =============================================================================


class TestKnowledgeResult:
    """Tests for KnowledgeResult dataclass."""

    def test_create_knowledge_result(self):
        """Test creating KnowledgeResult with all fields."""
        result = KnowledgeResult(
            content="Test content",
            metadata={"source": "test", "section": "experience"},
            score=0.95,
        )

        assert result.content == "Test content"
        assert result.metadata == {"source": "test", "section": "experience"}
        assert result.score == 0.95

    def test_knowledge_result_default_score(self):
        """Test KnowledgeResult with default score."""
        result = KnowledgeResult(content="Test content", metadata={"source": "test"})

        assert result.score is None


class TestMemoryResult:
    """Tests for MemoryResult dataclass."""

    def test_create_memory_result(self):
        """Test creating MemoryResult with all fields."""
        result = MemoryResult(
            content="Test memory",
            event_type="decision",
            timestamp=1711234567.0,
            score=0.88,
        )

        assert result.content == "Test memory"
        assert result.event_type == "decision"
        assert result.timestamp == 1711234567.0
        assert result.score == 0.88

    def test_memory_result_default_values(self):
        """Test MemoryResult with default values."""
        result = MemoryResult(content="Test memory", event_type="goal")

        assert result.timestamp is None
        assert result.score is None


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""

    def test_base_agent_is_abstract(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent()  # type: ignore[abstract]

    def test_concrete_agent_implementation(self):
        """Test implementing a concrete agent."""

        class TestAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test agent"

            def can_handle(self, intent: str) -> bool:
                return "test" in intent.lower()

            async def process(self, context: dict) -> str:
                return "Test response"

        agent = TestAgent()
        assert agent.name == "test"
        assert agent.description == "Test agent"
        assert agent.can_handle("This is a test") is True
        assert agent.can_handle("No match") is False


class TestBaseAgentChromaDB:
    """Tests for BaseAgent ChromaDB integration.

    Note: These tests require mocking the ChromaDB client at import time.
    For now, they're skipped - the actual ChromaDB functionality is tested
    through integration tests.
    """

    @pytest.fixture
    def mock_chroma_client(self):
        """Create mock ChromaDB client."""
        with patch("fu7ur3pr00f.agents.specialists.base.get_chroma_client") as mock:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.get_collection.return_value = mock_collection
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def test_agent(self, mock_chroma_client):
        """Create test agent with mocked ChromaDB."""

        class TestAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test agent"

            def can_handle(self, intent: str) -> bool:
                return True

            async def process(self, context: dict) -> str:
                return "Test"

        return TestAgent()

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_chroma_lazy_loading(self, mock_chroma_client, test_agent):
        """Test that ChromaDB client is lazy-loaded."""
        # Should not call get_chroma_client until accessed
        mock_chroma_client.assert_not_called()

        # Access chroma property
        _ = test_agent.chroma

        # Should have called get_chroma_client once
        mock_chroma_client.assert_called_once()

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_chroma_thread_safety(self, mock_chroma_client, test_agent):
        """Test that ChromaDB loading is thread-safe."""
        # Access multiple times - should only create once
        _ = test_agent.chroma
        _ = test_agent.chroma
        _ = test_agent.chroma

        # Should still only be called once (singleton pattern)
        assert mock_chroma_client.call_count == 1

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_search_knowledge(self, mock_chroma_client, test_agent):
        """Test searching knowledge base."""
        # Setup mock response
        mock_collection = mock_chroma_client.get_collection.return_value
        mock_collection.query.return_value = {
            "documents": [["Doc 1", "Doc 2"]],
            "metadatas": [[{"source": "test"}, {"source": "test2"}]],
            "distances": [[0.1, 0.2]],
        }

        # Search
        results = test_agent.search_knowledge("test query", limit=2)

        # Verify
        assert len(results) == 2
        assert isinstance(results[0], KnowledgeResult)
        assert results[0].content == "Doc 1"
        assert results[0].score == 0.9  # 1.0 - 0.1

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_search_knowledge_with_filters(self, mock_chroma_client, test_agent):
        """Test searching with section and source filters."""
        mock_collection = mock_chroma_client.get_collection.return_value
        mock_collection.query.return_value = {
            "documents": [["Doc 1"]],
            "metadatas": [[{"source": "linkedin", "section": "experience"}]],
            "distances": [[0.15]],
        }

        test_agent.search_knowledge(
            "experience", limit=5, section="experience", sources=["linkedin"]
        )

        # Verify filter was passed
        call_args = mock_collection.query.call_args
        assert call_args[1]["where"] is not None

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_index_knowledge(self, mock_chroma_client, test_agent):
        """Test indexing documents to knowledge base."""
        mock_collection = mock_chroma_client.get_collection.return_value

        ids = test_agent.index_knowledge(
            documents=["Doc 1", "Doc 2"],
            metadatas=[{"source": "test"}, {"source": "test2"}],
        )

        assert len(ids) == 2
        assert all(id_.startswith("doc_") for id_ in ids)
        mock_collection.add.assert_called_once()

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_index_knowledge_length_mismatch(self, mock_chroma_client, test_agent):
        """Test indexing with mismatched documents/metadatas length."""
        with pytest.raises(ValueError, match="same length"):
            test_agent.index_knowledge(
                documents=["Doc 1"], metadatas=[{"source": "test"}, {"source": "test2"}]
            )

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_remember(self, mock_chroma_client, test_agent):
        """Test storing episodic memory."""
        mock_collection = mock_chroma_client.get_collection.return_value

        memory_id = test_agent.remember(
            event_type="decision",
            data="Test decision",
            metadata={"company": "TestCorp"},
        )

        assert memory_id.startswith("episodic_decision_")
        mock_collection.add.assert_called_once()

        # Verify metadata includes timestamp
        call_args = mock_collection.add.call_args
        assert "timestamp" in call_args[1]["metadatas"][0]

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_recall_memories(self, mock_chroma_client, test_agent):
        """Test recalling episodic memories."""
        mock_collection = mock_chroma_client.get_collection.return_value
        mock_collection.query.return_value = {
            "documents": [["Memory 1", "Memory 2"]],
            "metadatas": [
                [
                    {"type": "decision", "timestamp": 1711234567.0},
                    {"type": "goal", "timestamp": 1711234568.0},
                ]
            ],
            "distances": [[0.1, 0.2]],
        }

        results = test_agent.recall_memories(
            "test query", event_type="decision", limit=5
        )

        assert len(results) == 2
        assert isinstance(results[0], MemoryResult)
        assert results[0].event_type == "decision"

    @pytest.mark.skip(reason="ChromaDB mocking requires import-time patching")
    def test_get_memory_stats(self, mock_chroma_client, test_agent):
        """Test getting memory statistics."""
        mock_collection = mock_chroma_client.get_collection.return_value
        mock_collection.get.return_value = {
            "ids": ["id1", "id2", "id3"],
            "metadatas": [{"type": "decision"}, {"type": "decision"}, {"type": "goal"}],
        }

        stats = test_agent.get_memory_stats()

        assert stats["total"] == 3
        assert stats["by_type"]["decision"] == 2
        assert stats["by_type"]["goal"] == 1


# =============================================================================
# CoachAgent Tests
# =============================================================================


class TestCoachAgent:
    """Tests for CoachAgent."""

    def test_coach_agent_creation(self):
        """Test creating CoachAgent."""
        agent = CoachAgent()
        assert agent.name == "coach"
        assert agent.description == "Career growth and leadership coach"

    def test_coach_agent_can_handle_promotion(self):
        """Test CoachAgent handles promotion queries."""
        agent = CoachAgent()

        assert agent.can_handle("How do I get promoted?") is True
        assert agent.can_handle("I want to become Staff Engineer") is True
        assert agent.can_handle("Leadership development") is True
        assert agent.can_handle("Find me a job") is False

    def test_coach_agent_can_handle_keywords(self):
        """Test CoachAgent keyword matching."""
        agent = CoachAgent()

        test_cases = [
            ("I want to get promoted to Staff", True),
            ("How can I improve my leadership?", True),
            ("Career growth path", True),
            ("CliftonStrengths coaching", True),
            ("Find remote jobs", False),
            ("Search GitHub repos", False),
        ]

        for query, expected in test_cases:
            assert agent.can_handle(query) == expected, f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_coach_agent_process(self):
        """Test CoachAgent processing."""
        agent = CoachAgent()

        # Mock the internal methods
        agent._get_experience = MagicMock(return_value=[])
        agent._get_strengths = MagicMock(return_value=[])
        agent._get_goals = MagicMock(return_value=[])
        agent._assess_promotion_readiness = MagicMock(return_value={"score": 75})
        agent._create_development_plan = MagicMock(return_value={"actions": []})
        agent._build_response = MagicMock(return_value="Test response")

        context = {"query": "How can I get promoted?", "user_profile": {}}

        response = await agent.process(context)

        assert isinstance(response, str)
        assert len(response) > 0


class TestCoachAgentReadiness:
    """Tests for CoachAgent promotion readiness assessment."""

    @pytest.fixture
    def agent(self):
        """Create CoachAgent for testing."""
        return CoachAgent()

    def test_calculate_years_experience(self, agent):
        """Test years of experience calculation."""
        experience = [
            KnowledgeResult(content="Job 1", metadata={}),
            KnowledgeResult(content="Job 2", metadata={}),
            KnowledgeResult(content="Job 3", metadata={}),
        ]

        years = agent._calculate_years_experience(experience)
        assert years == 6  # 3 jobs * 2 years average

    def test_identify_leadership_themes(self, agent):
        """Test leadership themes identification."""
        strengths = [
            KnowledgeResult(content="Activator, Ideation, Strategic", metadata={}),
            KnowledgeResult(content="Developer, Empathy", metadata={}),
        ]

        themes = agent._identify_leadership_themes(strengths)

        assert "Activator" in themes
        assert "Ideation" in themes
        assert "Strategic" in themes
        assert "Developer" in themes
        assert "Empathy" in themes

    def test_count_impact_examples(self, agent):
        """Test impact example counting."""
        experience = [
            KnowledgeResult(content="Improved performance by 40%", metadata={}),
            KnowledgeResult(content="Led team of 5 engineers", metadata={}),
            KnowledgeResult(content="Wrote code for project", metadata={}),
        ]

        count = agent._count_impact_examples(experience)
        assert count == 2  # First two have impact keywords

    def test_goals_aligned_with_promotion(self, agent):
        """Test goal alignment checking."""
        aligned_goals = [
            KnowledgeResult(content="Become Staff Engineer", metadata={}),
        ]

        misaligned_goals = [
            KnowledgeResult(content="Learn Python", metadata={}),
        ]

        assert agent._goals_aligned_with_promotion(aligned_goals) is True
        assert agent._goals_aligned_with_promotion(misaligned_goals) is False


# =============================================================================
# OrchestratorAgent Tests
# =============================================================================


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent."""

    def test_orchestrator_creation(self):
        """Test creating OrchestratorAgent."""
        agent = OrchestratorAgent()
        assert agent.name == "orchestrator"
        assert "Routes requests" in agent.description
        assert "synthesizes" in agent.description.lower()

    def test_orchestrator_can_handle_all(self):
        """Test Orchestrator can handle all queries."""
        agent = OrchestratorAgent()
        assert agent.can_handle("Any query") is True

    def test_orchestrator_routing_coach(self):
        """Test routing to CoachAgent."""
        agent = OrchestratorAgent()

        assert agent._route_query("How do I get promoted?") == "coach"
        assert agent._route_query("Leadership development") == "coach"

    def test_orchestrator_routing_learning(self):
        """Test routing to LearningAgent."""
        agent = OrchestratorAgent()

        assert agent._route_query("I want to learn Python") == "learning"
        assert agent._route_query("How to become an expert?") == "learning"

    def test_orchestrator_routing_jobs(self):
        """Test routing to JobsAgent."""
        agent = OrchestratorAgent()

        assert agent._route_query("Find me a job") == "jobs"
        assert agent._route_query("remote python developer") == "jobs"
        assert agent._route_query("hiring") == "jobs"

    def test_orchestrator_routing_code(self):
        """Test routing to CodeAgent."""
        agent = OrchestratorAgent()

        assert agent._route_query("Improve my GitHub") == "code"
        assert agent._route_query("Open source contributions") == "code"

    def test_orchestrator_routing_founder(self):
        """Test routing to FounderAgent."""
        agent = OrchestratorAgent()

        assert agent._route_query("Should I start a company?") == "founder"
        assert agent._route_query("Launch my startup") == "founder"

    def test_orchestrator_routing_default(self):
        """Test default routing to coach."""
        agent = OrchestratorAgent()

        # Ambiguous query should default to coach
        assert agent._route_query("Help me") == "coach"

    @pytest.mark.asyncio
    async def test_orchestrator_initialize(self):
        """Test Orchestrator initialization."""
        agent = OrchestratorAgent()
        await agent.initialize()

        assert "coach" in agent.specialists
        assert isinstance(agent.specialists["coach"], CoachAgent)

    @pytest.mark.asyncio
    async def test_orchestrator_get_available_agents(self):
        """Test getting available agents."""
        agent = OrchestratorAgent()
        await agent.initialize()

        agents = agent.get_available_agents()

        assert len(agents) >= 1
        assert any(a["name"] == "coach" for a in agents)

    @pytest.mark.asyncio
    async def test_orchestrator_handle(self):
        """Test Orchestrator handle method."""
        agent = OrchestratorAgent()
        await agent.initialize()

        # Mock CoachAgent process
        agent.specialists["coach"].process = AsyncMock(return_value="Coach response")

        response = await agent.handle("How do I get promoted?")

        assert isinstance(response, str)

    def test_orchestrator_handle_no_specialist(self):
        """Test handling when no specialist available."""
        agent = OrchestratorAgent()

        response = agent._handle_no_specialist("test query")

        assert "I'm still learning" in response
        assert "career growth" in response.lower()


# =============================================================================
# Integration Tests
# =============================================================================


class TestMultiAgentIntegration:
    """Integration tests for multi-agent system."""

    @pytest.mark.asyncio
    async def test_orchestrator_coach_flow(self):
        """Test full flow: Orchestrator → CoachAgent."""
        # Initialize orchestrator
        orchestrator = OrchestratorAgent()
        await orchestrator.initialize()

        # Verify coach agent is available
        assert "coach" in orchestrator.specialists

        # Test routing
        route = orchestrator._route_query("How can I get promoted to Staff Engineer?")
        assert route == "coach"

    @pytest.mark.asyncio
    async def test_agent_values_filtering(self):
        """Test that values filtering is applied."""
        from fu7ur3pr00f.agents.values import ValuesContext, apply_values_filter

        # Test with red flags
        ctx = ValuesContext(company_uses_proprietary=True, crunch_expected=True)

        response = apply_values_filter("Great salary and benefits!", context=ctx)

        assert "⚠️" in response or "red flag" in response.lower()
